import asyncio
import json
from typing import Any, Awaitable, Dict, Optional

import httpx
import jose.jws
import jose.jwt
from fastapi import Depends, HTTPException
from fastapi.openapi.models import OAuthFlowImplicit, OAuthFlows
from fastapi.security import OAuth2
from starlette.datastructures import URL
from starlette.status import HTTP_403_FORBIDDEN

import djoek.settings as settings


class AuthenticationFailed(Exception):
    pass


class Authenticator:
    _keyset_future: Optional[Awaitable[Dict[str, Any]]]

    def __init__(self) -> None:
        self._keyset_future = None

    async def get_keys(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
            )
        r.raise_for_status()

        keyset = r.json()

        return {
            key["kid"]: json.dumps(key, sort_keys=True)
            for key in keyset["keys"]
            if key["use"] == "sig" and key["kty"] == "RSA" and key["alg"] == "RS256"
        }

    async def verify(self, auth_header: str) -> None:
        loop = asyncio.get_event_loop()

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

        if self._keyset_future is None:
            self._keyset_future = loop.create_future()
            self._keyset_future.set_result(await self.get_keys())
        keyset = await self._keyset_future

        key = keyset.get(key_id)
        if key is None:
            raise AuthenticationFailed("key not found")

        try:
            decoded_token = jose.jwt.decode(
                token, key, audience=settings.AUTH0_AUDIENCE
            )
        except (jose.JWTError, ValueError):
            raise AuthenticationFailed("invalid token or signature")

        if decoded_token.get("azp") not in settings.AUTH0_PARTIES:
            raise AuthenticationFailed("invalid client")


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
    )
)


async def require_auth(auth_header: str = Depends(oauth2_scheme)) -> None:
    try:
        await authenticator.verify(auth_header)
    except AuthenticationFailed as e:
        raise HTTPException(HTTP_403_FORBIDDEN, detail=str(e))