from sources.mangadex import MangaDexSource
from sources.manganato import MangaNatoSource
from sources.webtoons import WebtoonsSource
from sources.mangakakalot import MangaKakalotSource

SOURCES = {
    "mangadex": MangaDexSource,
    "manganato": MangaNatoSource,
    "webtoons": WebtoonsSource,
    "mangakakalot": MangaKakalotSource,
}

SOURCE_PATTERNS = {
    "mangadex.org": "mangadex",
    "api.mangadex.org": "mangadex",
    "manganato.com": "manganato",
    "chapmanganato.to": "manganato",
    "readmanganato.com": "manganato",
    "webtoons.com": "webtoons",
    "mangakakalot.com": "mangakakalot",
    "chapangakakalot.to": "mangakakalot",
}


def detect_source(url: str):
    url_lower = url.lower()
    for pattern, source_key in SOURCE_PATTERNS.items():
        if pattern in url_lower:
            return source_key, SOURCES[source_key]()
    return None, None


def get_all_sources():
    return {k: v() for k, v in SOURCES.items()}