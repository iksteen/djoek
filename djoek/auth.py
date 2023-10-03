import asyncio
import json
from math import inf
from typing import Any, Awaitable, MutableMapping, Optional

import httpx
import jose.jws
import jose.jwt
from cachetools import TTLCache
from fastapi import Depends, HTTPException
from fastapi.openapi.models import OAuthFlowImplicit, OAuthFlows
from fastapi.security import OAuth2
from peewee_async import Manager
from starlette.datastructures import URL
from starlette.status import HTTP_403_FORBIDDEN

import djoek.settings as settings
from djoek.models import User, get_manager


class AuthenticationFailed(Exception):
    pass


class Authenticator:
    _keyset_future: Optional[Awaitable[dict[str, Any]]]
    _userinfo_cache: MutableMapping[str, Awaitable[dict[str, Any]]]

    def __init__(self) -> None:
        self._keyset_future = None
        self._userinfo_cache = TTLCache(inf, 3600)

    async def get_keys(self, *, force: bool = False) -> dict[str, Any]:
        loop = asyncio.get_event_loop()

        if self._keyset_future is not None and not force:
            return await self._keyset_future
        self._keyset_future = loop.create_future()

        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
                )
            r.raise_for_status()

            keyset_data = r.json()

            keyset = {
                key["kid"]: json.dumps(key, sort_keys=True)
                for key in keyset_data["keys"]
                if key["use"] == "sig" and key["kty"] == "RSA" and key["alg"] == "RS256"
            }
            self._keyset_future.set_result(keyset)
        except Exception as e:
            f, self._keyset_future = self._keyset_future, None
            f.set_exception(e)
            raise
        return keyset

    async def get_userinfo(self, auth_header: str, sub: str) -> dict[str, Any]:
        loop = asyncio.get_event_loop()

        userinfo: dict[str, Any]

        f_userinfo = self._userinfo_cache.get(sub)
        if f_userinfo is not None:
            userinfo = await f_userinfo
            return userinfo

        f_userinfo = self._userinfo_cache[sub] = loop.create_future()
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"https://{settings.AUTH0_DOMAIN}/userinfo",
                    headers={"Authorization": auth_header},
                )
            r.raise_for_status()
            userinfo = r.json()
        except Exception as e:
            f_userinfo.set_exception(e)
            del self._userinfo_cache[sub]
            raise

        f_userinfo.set_result(userinfo)
        return userinfo

    async def verify(self, auth_header: Optional[str]) -> dict[str, Any]:
        if auth_header is None:
            raise AuthenticationFailed("no authentication provided")

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != "Bearer":
            raise AuthenticationFailed("invalid authorization header")

        token = parts[1]
        try:
            token_header = jose.jws.get_unverified_header(token)
        except jose.JWSError:
            raise AuthenticationFailed("invalid token")

        if (
            token_header.get("typ") != "JWT"
            or token_header.get("alg") != "RS256"
            or "kid" not in token_header
        ):
            raise AuthenticationFailed("unsupported token")

        key_id = token_header["kid"]

        keyset = await self.get_keys()
        key = keyset.get(key_id)
        if key is None:
            keyset = await self.get_keys(force=True)
            key = keyset.get(key_id)
            if key is None:
                raise AuthenticationFailed("key not found")

        try:
            decoded_token: dict[str, Any] = jose.jwt.decode(
                token, key, audience=settings.AUTH0_AUDIENCE
            )
        except (jose.JWTError, ValueError):
            raise AuthenticationFailed("invalid token or signature")

        if decoded_token.get("azp") not in settings.AUTH0_PARTIES:
            raise AuthenticationFailed("invalid client")

        return decoded_token


authenticator = Authenticator()

oauth2_scheme = OAuth2(
    flows=OAuthFlows(
        implicit=OAuthFlowImplicit(
            authorizationUrl=str(
                URL(f"https://{settings.AUTH0_DOMAIN}/authorize").include_query_params(
                    audience=settings.AUTH0_AUDIENCE
                )
            )
        )
    ),
    auto_error=False,
)


async def is_authenticated(auth_header: Optional[str] = Depends(oauth2_scheme)) -> bool:
    try:
        await authenticator.verify(auth_header)
        return True
    except AuthenticationFailed:
        return False


async def require_auth(
    auth_header: Optional[str] = Depends(oauth2_scheme),
) -> dict[str, Any]:
    try:
        return await authenticator.verify(auth_header)
    except AuthenticationFailed as e:
        raise HTTPException(HTTP_403_FORBIDDEN, detail=str(e))


async def require_userinfo(
    auth_header: str = Depends(oauth2_scheme),
    token: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    try:
        return await authenticator.get_userinfo(auth_header, token["sub"])
    except Exception as e:
        raise HTTPException(HTTP_403_FORBIDDEN, detail=str(e))


async def require_user_id(
    manager: Manager = Depends(get_manager),
    userinfo: dict[str, Any] = Depends(require_userinfo),
) -> int:
    user_id: int = await manager.execute(
        User.insert(sub=userinfo["sub"], profile=userinfo).on_conflict(
            conflict_target=[User.sub], update={User.profile: userinfo}
        )
    )
    return user_id


async def require_user(
    user_id: int = Depends(require_user_id), manager: Manager = Depends(get_manager)
) -> User:
    user: User = await manager.get(User, id=user_id)
    return user
