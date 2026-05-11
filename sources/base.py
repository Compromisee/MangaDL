from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List
import cloudscraper
import config


@dataclass
class Chapter:
    id: str
    number: str
    title: str
    url: str
    volume: Optional[str] = None
    language: str = "en"
    pages: list = field(default_factory=list)
    page_count: int = 0


@dataclass
class MangaInfo:
    id: str
    title: str
    author: str
    description: str
    cover_url: str
    url: str
    source: str
    chapters: list = field(default_factory=list)
    status: str = "Unknown"
    genres: list = field(default_factory=list)
    available_languages: list = field(default_factory=lambda: ["en"])


class BaseSource(ABC):
    name: str = "Unknown"
    base_url: str = ""

    def __init__(self):
        self.session = cloudscraper.create_scraper()
        self.session.headers.update(config.HEADERS)

    @abstractmethod
    def search(self, query: str) -> list:
        pass

    @abstractmethod
    def get_manga_info(self, url: str, language: str = "en") -> MangaInfo:
        pass

    @abstractmethod
    def get_chapter_pages(self, chapter: Chapter) -> list:
        pass

    def get_languages(self, url: str) -> list:
        """Override in subclasses that support multiple languages."""
        return ["en"]

    def _get(self, url: str, **kwargs):
        kwargs.setdefault("timeout", config.REQUEST_TIMEOUT)
        for attempt in range(config.RETRY_ATTEMPTS):
            try:
                resp = self.session.get(url, **kwargs)
                resp.raise_for_status()
                return resp
            except Exception:
                if attempt == config.RETRY_ATTEMPTS - 1:
                    raise
                import time
                time.sleep(config.RETRY_DELAY)

    def _get_json(self, url: str, **kwargs):
        return self._get(url, **kwargs).json()

    def _get_soup(self, url: str, **kwargs):
        from bs4 import BeautifulSoup
        return BeautifulSoup(self._get(url, **kwargs).text, "lxml")