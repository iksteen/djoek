from typing import Dict

from djoek.providers import Provider
from djoek.providers.youtube import YouTubeProvider

PROVIDERS: Dict[str, Provider] = {
    provider_class.key: provider_class() for provider_class in [YouTubeProvider]
}
