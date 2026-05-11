import re
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from sources.base import BaseSource, MangaInfo, Chapter


class MangaNatoSource(BaseSource):
    name = "MangaNato"
    base_url = "https://manganato.com"

    def search(self, query: str) -> list:
        search_query = query.replace(" ", "_")
        url = f"https://manganato.com/search/story/{quote_plus(search_query)}"
        soup = self._get_soup(url)
        results = []

        panels = soup.select("div.search-story-item")
        for panel in panels[:20]:
            link_el = panel.select_one("a.item-img")
            if not link_el:
                continue
            href = link_el.get("href", "")
            title = link_el.get("title", "Unknown")
            img = link_el.select_one("img")
            cover = img.get("src", "") if img else ""

            author_el = panel.select_one("span.text-nowrap.item-author")
            author = author_el.text.strip() if author_el else "Unknown"

            results.append(MangaInfo(
                id=href,
                title=title,
                author=author,
                description="",
                cover_url=cover,
                url=href,
                source=self.name,
            ))
        return results

    def get_manga_info(self, url: str) -> MangaInfo:
        soup = self._get_soup(url)

        title_el = soup.select_one("div.story-info-right h1")
        title = title_el.text.strip() if title_el else "Unknown"

        cover_el = soup.select_one("span.info-image img")
        cover_url = cover_el.get("src", "") if cover_el else ""

        author = "Unknown"
        status = "Unknown"
        genres = []

        table_rows = soup.select("table.variations-tableInfo tr")
        for row in table_rows:
            label_el = row.select_one("td.table-label")
            value_el = row.select_one("td.table-value")
            if not label_el or not value_el:
                continue
            label = label_el.text.strip().lower()
            if "author" in label:
                author = value_el.text.strip()
            elif "status" in label:
                status = value_el.text.strip()
            elif "genre" in label:
                genres = [a.text.strip() for a in value_el.select("a")]

        desc_el = soup.select_one("div.panel-story-info-description")
        description = ""
        if desc_el:
            description = desc_el.text.replace("Description :", "").strip()

        chapters = []
        ch_list = soup.select("ul.row-content-chapter li a.chapter-name")
        for i, ch_el in enumerate(reversed(ch_list)):
            ch_url = ch_el.get("href", "")
            ch_title = ch_el.text.strip()
            ch_num = self._extract_chapter_num(ch_title)
            chapters.append(Chapter(
                id=ch_url,
                number=ch_num,
                title=ch_title,
                url=ch_url,
            ))

        return MangaInfo(
            id=url,
            title=title,
            author=author,
            description=description[:300],
            cover_url=cover_url,
            url=url,
            source=self.name,
            chapters=chapters,
            status=status,
            genres=genres,
        )

    def get_chapter_pages(self, chapter: Chapter) -> list:
        self.session.headers.update({"Referer": "https://manganato.com/"})
        soup = self._get_soup(chapter.url)
        imgs = soup.select("div.container-chapter-reader img")
        pages = [img.get("src", "") for img in imgs if img.get("src")]
        chapter.pages = pages
        chapter.page_count = len(pages)
        return pages

    def _extract_chapter_num(self, text: str) -> str:
        match = re.search(r"chapter\s+([\d.]+)", text, re.IGNORECASE)
        return match.group(1) if match else "0"