from djoek.providers import Provider
from djoek.providers.soundcloud import SoundcloudProvider
from djoek.providers.youtube import YouTubeProvider

PROVIDERS: dict[str, Provider] = {
    provider_class.key: provider_class()
    for provider_class in [YouTubeProvider, SoundcloudProvider]
}
