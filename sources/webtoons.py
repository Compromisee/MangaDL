import re
from sources.base import BaseSource, MangaInfo, Chapter


WEBTOON_LANGUAGES = {
    "en": "en",
    "ko": "ko",
    "ja": "ja",
    "zh-hans": "zh-hans",
    "zh-hant": "zh-hant",
    "th": "th",
    "id": "id",
    "es": "es",
    "fr": "fr",
    "de": "de",
}


class WebtoonsSource(BaseSource):
    name = "Webtoons"
    base_url = "https://www.webtoons.com"

    def search(self, query: str) -> list:
        url = f"{self.base_url}/en/search?keyword={query}"
        soup = self._get_soup(url)
        results = []

        cards = soup.select("ul#searchResult li a")
        for card in cards[:20]:
            href = card.get("href", "")
            if not href or "/episodeList" not in href:
                continue
            title_el = card.select_one("p.subj")
            title = title_el.text.strip() if title_el else "Unknown"
            img_el = card.select_one("img")
            cover = img_el.get("src", "") if img_el else ""
            author_el = card.select_one("p.author")
            author = author_el.text.strip() if author_el else "Unknown"

            if not href.startswith("http"):
                href = self.base_url + href

            results.append(MangaInfo(
                id=href,
                title=title,
                author=author,
                description="",
                cover_url=cover,
                url=href,
                source=self.name,
                available_languages=list(WEBTOON_LANGUAGES.keys()),
            ))
        return results

    def get_manga_info(self, url: str, language: str = "en") -> MangaInfo:
        # Replace language in URL if needed
        lang_url = self._replace_language_in_url(url, language)
        soup = self._get_soup(lang_url)

        title_el = soup.select_one("h1.subj")
        title = title_el.text.strip() if title_el else "Unknown"

        author_el = soup.select_one("a.author_area")
        author = author_el.text.strip() if author_el else "Unknown"

        desc_el = soup.select_one("p.summary")
        description = desc_el.text.strip() if desc_el else ""

        cover_el = soup.select_one("div.detail_header img")
        cover_url = cover_el.get("src", "") if cover_el else ""

        genre_els = soup.select("div.info .genre")
        genres = [g.text.strip() for g in genre_els]

        chapters = self._get_all_episodes(lang_url)

        return MangaInfo(
            id=url,
            title=title,
            author=author,
            description=description[:300],
            cover_url=cover_url,
            url=url,
            source=self.name,
            chapters=chapters,
            genres=genres,
            available_languages=list(WEBTOON_LANGUAGES.keys()),
        )

    def _replace_language_in_url(self, url: str, language: str) -> str:
        """Replace language code in webtoons URL."""
        return re.sub(
            r"webtoons\.com/([a-z\-]+)/",
            f"webtoons.com/{language}/",
            url,
            count=1,
        )

    def _get_all_episodes(self, url: str) -> list:
        chapters = []
        page = 1
        while True:
            page_url = f"{url}&page={page}"
            soup = self._get_soup(page_url)
            eps = soup.select("ul#_listUl li a")
            if not eps:
                break
            for ep in eps:
                href = ep.get("href", "")
                num_el = ep.select_one("span.tx")
                title_el = ep.select_one("span.subj span")
                num = num_el.text.strip().replace("#", "") if num_el else str(len(chapters))
                ch_title = title_el.text.strip() if title_el else f"Episode {num}"
                if not href.startswith("http"):
                    href = self.base_url + href
                chapters.append(Chapter(
                    id=href,
                    number=num,
                    title=ch_title,
                    url=href,
                ))
            page += 1
            if page > 200:
                break

        chapters.reverse()
        return chapters

    def get_chapter_pages(self, chapter: Chapter) -> list:
        self.session.headers.update({"Referer": "https://www.webtoons.com/"})
        soup = self._get_soup(chapter.url)
        imgs = soup.select("div#_imageList img")
        pages = []
        for img in imgs:
            src = img.get("data-url") or img.get("src", "")
            if src and "webtoons" in src:
                pages.append(src)
        chapter.pages = pages
        chapter.page_count = len(pages)
        return pages