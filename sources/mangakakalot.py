import re
from urllib.parse import quote_plus
from sources.base import BaseSource, MangaInfo, Chapter


class MangaKakalotSource(BaseSource):
    name = "MangaKakalot"
    base_url = "https://mangakakalot.com"

    def search(self, query: str) -> list:
        search_query = query.replace(" ", "_")
        url = f"{self.base_url}/search/story/{quote_plus(search_query)}"
        soup = self._get_soup(url)
        results = []

        panels = soup.select("div.story_item")
        for panel in panels[:20]:
            link_el = panel.select_one("a")
            if not link_el:
                continue
            href = link_el.get("href", "")
            img = panel.select_one("img")
            cover = img.get("src", "") if img else ""
            title_el = panel.select_one("h3 a")
            title = title_el.text.strip() if title_el else "Unknown"

            results.append(MangaInfo(
                id=href,
                title=title,
                author="Unknown",
                description="",
                cover_url=cover,
                url=href,
                source=self.name,
            ))
        return results

    def get_manga_info(self, url: str, language: str = "en") -> MangaInfo:
        soup = self._get_soup(url)

        title_el = soup.select_one("ul.manga-info-text li h1") or soup.select_one("div.manga-info-top h1")
        title = title_el.text.strip() if title_el else "Unknown"

        cover_el = soup.select_one("div.manga-info-pic img")
        cover_url = cover_el.get("src", "") if cover_el else ""

        author = "Unknown"
        status = "Unknown"
        genres = []

        info_items = soup.select("ul.manga-info-text li")
        for item in info_items:
            text = item.text.strip().lower()
            if "author" in text:
                a_tags = item.select("a")
                author = ", ".join(a.text.strip() for a in a_tags) if a_tags else "Unknown"
            elif "status" in text:
                status = text.split(":")[-1].strip().title()
            elif "genre" in text:
                genres = [a.text.strip() for a in item.select("a")]

        desc_el = soup.select_one("div#noidungm") or soup.select_one("div.manga-info-desc")
        description = desc_el.text.strip() if desc_el else ""

        chapters = []
        ch_list = soup.select("div.chapter-list div.row span a") or soup.select("div.manga-info-chapter div.row span a")
        for ch_el in reversed(ch_list):
            ch_url = ch_el.get("href", "")
            ch_title = ch_el.text.strip()
            ch_num = self._extract_chapter_num(ch_title)
            chapters.append(Chapter(
                id=ch_url,
                number=ch_num,
                title=ch_title,
                url=ch_url,
                language="en",
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
            available_languages=["en"],
        )

    def get_chapter_pages(self, chapter: Chapter) -> list:
        self.session.headers.update({"Referer": "https://mangakakalot.com/"})
        soup = self._get_soup(chapter.url)
        imgs = soup.select("div#vungdoc img") or soup.select("div.container-chapter-reader img")
        pages = [img.get("src", "") for img in imgs if img.get("src")]
        chapter.pages = pages
        chapter.page_count = len(pages)
        return pages

    def _extract_chapter_num(self, text: str) -> str:
        match = re.search(r"chapter\s+([\d.]+)", text, re.IGNORECASE)
        return match.group(1) if match else "0"