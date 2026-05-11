import re
from sources.base import BaseSource, MangaInfo, Chapter


class MangaDexSource(BaseSource):
    name = "MangaDex"
    base_url = "https://api.mangadex.org"

    def search(self, query: str) -> list:
        params = {
            "title": query,
            "limit": 20,
            "includes[]": ["cover_art", "author"],
            "contentRating[]": ["safe", "suggestive", "erotica"],
            "order[relevance]": "desc",
        }
        data = self._get_json(f"{self.base_url}/manga", params=params)
        results = []
        for item in data.get("data", []):
            attrs = item["attributes"]
            title = attrs["title"].get("en") or next(iter(attrs["title"].values()), "Unknown")

            cover_url = ""
            author_name = "Unknown"
            for rel in item.get("relationships", []):
                if rel["type"] == "cover_art":
                    cover_file = rel.get("attributes", {}).get("fileName", "")
                    if cover_file:
                        cover_url = f"https://uploads.mangadex.org/covers/{item['id']}/{cover_file}.256.jpg"
                elif rel["type"] == "author":
                    author_name = rel.get("attributes", {}).get("name", "Unknown")

            desc = attrs.get("description", {}).get("en", "")
            genres = [t["attributes"]["name"].get("en", "") for t in attrs.get("tags", [])]

            results.append(MangaInfo(
                id=item["id"],
                title=title,
                author=author_name,
                description=desc[:300],
                cover_url=cover_url,
                url=f"https://mangadex.org/title/{item['id']}",
                source=self.name,
                status=attrs.get("status", "Unknown"),
                genres=genres,
            ))
        return results

    def get_manga_info(self, url: str, language: str = "en") -> MangaInfo:
        manga_id = self._extract_id(url)
        data = self._get_json(
            f"{self.base_url}/manga/{manga_id}",
            params={"includes[]": ["cover_art", "author"]}
        )
        item = data["data"]
        attrs = item["attributes"]
        title = attrs["title"].get("en") or next(iter(attrs["title"].values()), "Unknown")

        cover_url = ""
        author_name = "Unknown"
        for rel in item.get("relationships", []):
            if rel["type"] == "cover_art":
                cover_file = rel.get("attributes", {}).get("fileName", "")
                if cover_file:
                    cover_url = f"https://uploads.mangadex.org/covers/{manga_id}/{cover_file}.512.jpg"
            elif rel["type"] == "author":
                author_name = rel.get("attributes", {}).get("name", "Unknown")

        desc = attrs.get("description", {}).get("en", "")
        genres = [t["attributes"]["name"].get("en", "") for t in attrs.get("tags", [])]

        # Get available languages from manga metadata
        available_languages = attrs.get("availableTranslatedLanguages", []) or ["en"]
        available_languages = [l for l in available_languages if l]
        if not available_languages:
            available_languages = ["en"]

        # If requested language not available, fallback to first available
        if language not in available_languages:
            print(f"[MangaDex] Language '{language}' not available, using '{available_languages[0]}'")
            language = available_languages[0]

        chapters = self._get_all_chapters(manga_id, language)

        info = MangaInfo(
            id=manga_id,
            title=title,
            author=author_name,
            description=desc,
            cover_url=cover_url,
            url=url,
            source=self.name,
            chapters=chapters,
            status=attrs.get("status", "Unknown"),
            genres=genres,
            available_languages=sorted(available_languages),
        )
        return info

    def get_languages(self, url: str) -> list:
        manga_id = self._extract_id(url)
        try:
            data = self._get_json(f"{self.base_url}/manga/{manga_id}")
            langs = data.get("data", {}).get("attributes", {}).get("availableTranslatedLanguages", [])
            langs = [l for l in langs if l]
            return sorted(langs) if langs else ["en"]
        except Exception:
            return ["en"]

    def _get_all_chapters(self, manga_id: str, language: str = "en") -> list:
        """Fetch all chapters with proper deduplication and external chapter handling."""
        all_chapters = []
        offset = 0
        limit = 500  # MangaDex max
        max_iterations = 50  # Safety limit
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            params = {
                "translatedLanguage[]": [language],
                "order[chapter]": "asc",
                "order[volume]": "asc",
                "limit": limit,
                "offset": offset,
                "includes[]": ["scanlation_group"],
                "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"],
            }
            try:
                data = self._get_json(
                    f"{self.base_url}/manga/{manga_id}/feed",
                    params=params,
                )
            except Exception as e:
                print(f"[MangaDex] Error fetching chapters: {e}")
                break

            chapter_data = data.get("data", [])
            if not chapter_data:
                break

            for item in chapter_data:
                attrs = item.get("attributes", {})
                ch_num = attrs.get("chapter")
                # Allow chapter 0 and missing chapter numbers
                if ch_num is None:
                    ch_num = "0"
                ch_num = str(ch_num).strip()
                if not ch_num:
                    ch_num = "0"

                ch_title = attrs.get("title") or ""
                if not ch_title.strip():
                    ch_title = f"Chapter {ch_num}"

                volume = attrs.get("volume")
                if volume == "":
                    volume = None

                pages = attrs.get("pages", 0) or 0
                external_url = attrs.get("externalUrl")

                # Skip ONLY if it's external AND has 0 pages on MangaDex
                # If it has pages, we can still download it
                if external_url and pages == 0:
                    continue

                all_chapters.append(Chapter(
                    id=item["id"],
                    number=ch_num,
                    title=ch_title,
                    url=f"https://mangadex.org/chapter/{item['id']}",
                    volume=volume,
                    language=language,
                    page_count=pages,
                ))

            total = data.get("total", 0)
            offset += limit
            if offset >= total or len(chapter_data) < limit:
                break

        if not all_chapters:
            print(f"[MangaDex] WARNING: No chapters returned for manga {manga_id} in language '{language}'")
            return []

        # Deduplicate: keep the version with most pages, or first if tied
        # Group by (chapter_number, volume) so different volumes with same ch number coexist
        chapter_groups = {}
        for ch in all_chapters:
            key = (ch.number, ch.volume or "")
            if key not in chapter_groups:
                chapter_groups[key] = ch
            else:
                # Keep the one with more pages
                if ch.page_count > chapter_groups[key].page_count:
                    chapter_groups[key] = ch

        # Sort by chapter number numerically
        unique = list(chapter_groups.values())

        def sort_key(ch):
            try:
                v = float(ch.volume) if ch.volume else 0
            except (ValueError, TypeError):
                v = 0
            try:
                n = float(ch.number)
            except (ValueError, TypeError):
                n = 0
            return (v, n)

        unique.sort(key=sort_key)

        print(f"[MangaDex] Loaded {len(unique)} unique chapters (from {len(all_chapters)} raw entries) in '{language}'")
        return unique

    def get_chapter_pages(self, chapter: Chapter) -> list:
        try:
            data = self._get_json(f"{self.base_url}/at-home/server/{chapter.id}")
        except Exception as e:
            print(f"[MangaDex] Failed to get pages for {chapter.id}: {e}")
            return []

        if "baseUrl" not in data or "chapter" not in data:
            print(f"[MangaDex] Invalid response for chapter {chapter.id}")
            return []

        base = data["baseUrl"]
        ch_data = data["chapter"]
        ch_hash = ch_data.get("hash", "")
        if not ch_hash:
            return []

        pages = []
        file_list = ch_data.get("data", [])
        quality = "data"

        if not file_list:
            file_list = ch_data.get("dataSaver", [])
            quality = "data-saver"

        for filename in file_list:
            pages.append(f"{base}/{quality}/{ch_hash}/{filename}")

        chapter.pages = pages
        chapter.page_count = len(pages)
        return pages

    def _extract_id(self, url: str) -> str:
        match = re.search(
            r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})",
            url
        )
        if match:
            return match.group(1)
        match = re.search(r"mangadex\.org/title/([^/\s?#]+)", url)
        if match:
            return match.group(1)
        return url