from typing import Dict

from djoek.providers import Provider
from djoek.providers.soundcloud import SoundcloudProvider
from djoek.providers.youtube import YouTubeProvider

PROVIDERS: Dict[str, Provider] = {
    provider_class.key: provider_class()  # type: ignore
    for provider_class in [YouTubeProvider, SoundcloudProvider]
}
