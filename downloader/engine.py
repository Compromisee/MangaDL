import os
import time
import shutil
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

import config
from sources.base import BaseSource, Chapter, MangaInfo
from exporters import get_exporter


class DownloadTask:
    def __init__(self, task_id: str, manga: MangaInfo, chapters: list,
                 format_type: str, mode: str, source: BaseSource):
        self.task_id = task_id
        self.manga = manga
        self.chapters = chapters
        self.format_type = format_type
        self.mode = mode  # "chapter", "volume", "all"
        self.source = source
        self.status = "queued"
        self.progress = 0.0
        self.current_chapter = ""
        self.total_chapters = len(chapters)
        self.completed_chapters = 0
        self.errors = []
        self.output_paths = []
        self.cancel_flag = threading.Event()
        self.speed = 0
        self.downloaded_bytes = 0
        self.start_time = None


class DownloadEngine:
    def __init__(self):
        self.tasks: dict = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.Lock()
        self.on_progress: Optional[Callable] = None

    def create_task(self, manga: MangaInfo, chapters: list,
                    format_type: str, mode: str, source: BaseSource) -> str:
        task_id = hashlib.md5(
            f"{manga.title}{time.time()}".encode()
        ).hexdigest()[:12]

        task = DownloadTask(
            task_id=task_id,
            manga=manga,
            chapters=chapters,
            format_type=format_type,
            mode=mode,
            source=source,
        )

        with self._lock:
            self.tasks[task_id] = task

        self.executor.submit(self._run_task, task)
        return task_id

    def cancel_task(self, task_id: str):
        with self._lock:
            task = self.tasks.get(task_id)
            if task:
                task.cancel_flag.set()
                task.status = "cancelled"

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> list:
        return list(self.tasks.values())

    def _run_task(self, task: DownloadTask):
        task.status = "running"
        task.start_time = time.time()
        self._emit_progress(task)

        temp_base = os.path.join(config.TEMP_DIR, task.task_id)
        os.makedirs(temp_base, exist_ok=True)

        try:
            if task.mode == "volume":
                self._download_as_volumes(task, temp_base)
            elif task.mode == "all":
                self._download_all_in_one(task, temp_base)
            else:
                self._download_by_chapter(task, temp_base)

            if not task.cancel_flag.is_set():
                task.status = "completed"
                task.progress = 100.0
        except Exception as e:
            task.status = "error"
            task.errors.append(str(e))
        finally:
            shutil.rmtree(temp_base, ignore_errors=True)
            self._emit_progress(task)

    def _download_by_chapter(self, task: DownloadTask, temp_base: str):
        exporter = get_exporter(task.format_type)

        for idx, chapter in enumerate(task.chapters):
            if task.cancel_flag.is_set():
                return

            task.current_chapter = f"Ch. {chapter.number}: {chapter.title}"
            self._emit_progress(task)

            ch_temp = os.path.join(temp_base, f"ch_{chapter.number}")
            os.makedirs(ch_temp, exist_ok=True)

            try:
                pages = task.source.get_chapter_pages(chapter)
                image_paths = self._download_pages(task, pages, ch_temp, chapter)

                if image_paths:
                    output = exporter.export(
                        task.manga.title,
                        f"Chapter {chapter.number} - {chapter.title}",
                        image_paths,
                        config.DOWNLOAD_DIR,
                    )
                    task.output_paths.append(output)

            except Exception as e:
                task.errors.append(f"Ch.{chapter.number}: {str(e)}")

            task.completed_chapters = idx + 1
            task.progress = (task.completed_chapters / task.total_chapters) * 100
            self._emit_progress(task)

    def _download_as_volumes(self, task: DownloadTask, temp_base: str):
        exporter = get_exporter(task.format_type)

        volumes = {}
        for ch in task.chapters:
            vol = ch.volume or "No Volume"
            volumes.setdefault(vol, []).append(ch)

        total_chapters = sum(len(chs) for chs in volumes.values())
        completed = 0

        for vol_name, vol_chapters in sorted(volumes.items()):
            if task.cancel_flag.is_set():
                return

            chapters_data = []
            for chapter in vol_chapters:
                if task.cancel_flag.is_set():
                    return

                task.current_chapter = f"Vol.{vol_name} Ch.{chapter.number}"
                self._emit_progress(task)

                ch_temp = os.path.join(temp_base, f"v{vol_name}_ch{chapter.number}")
                os.makedirs(ch_temp, exist_ok=True)

                try:
                    pages = task.source.get_chapter_pages(chapter)
                    image_paths = self._download_pages(task, pages, ch_temp, chapter)
                    if image_paths:
                        chapters_data.append(
                            (f"Chapter {chapter.number}", image_paths)
                        )
                except Exception as e:
                    task.errors.append(f"Vol.{vol_name} Ch.{chapter.number}: {str(e)}")

                completed += 1
                task.completed_chapters = completed
                task.progress = (completed / total_chapters) * 100
                self._emit_progress(task)

            if chapters_data:
                output = exporter.export_volume(
                    task.manga.title,
                    f"Volume {vol_name}",
                    chapters_data,
                    config.DOWNLOAD_DIR,
                )
                task.output_paths.append(output)

    def _download_all_in_one(self, task: DownloadTask, temp_base: str):
        exporter = get_exporter(task.format_type)
        chapters_data = []

        for idx, chapter in enumerate(task.chapters):
            if task.cancel_flag.is_set():
                return

            task.current_chapter = f"Ch. {chapter.number}: {chapter.title}"
            self._emit_progress(task)

            ch_temp = os.path.join(temp_base, f"ch_{chapter.number}")
            os.makedirs(ch_temp, exist_ok=True)

            try:
                pages = task.source.get_chapter_pages(chapter)
                image_paths = self._download_pages(task, pages, ch_temp, chapter)
                if image_paths:
                    chapters_data.append(
                        (f"Chapter {chapter.number} - {chapter.title}", image_paths)
                    )
            except Exception as e:
                task.errors.append(f"Ch.{chapter.number}: {str(e)}")

            task.completed_chapters = idx + 1
            task.progress = (task.completed_chapters / task.total_chapters) * 100
            self._emit_progress(task)

        if chapters_data:
            output = exporter.export_volume(
                task.manga.title,
                f"{task.manga.title} - Complete",
                chapters_data,
                config.DOWNLOAD_DIR,
            )
            task.output_paths.append(output)

    def _download_pages(self, task: DownloadTask, pages: list,
                        output_dir: str, chapter: Chapter) -> list:
        image_paths = []
        download_lock = threading.Lock()

        def _dl_page(page_info):
            idx, url = page_info
            if task.cancel_flag.is_set():
                return None
            for attempt in range(config.RETRY_ATTEMPTS):
                try:
                    headers = dict(config.HEADERS)
                    if "webtoons" in url:
                        headers["Referer"] = "https://www.webtoons.com/"
                    elif "manganato" in url or "chapmanganato" in url:
                        headers["Referer"] = "https://manganato.com/"
                    elif "mangakakalot" in url:
                        headers["Referer"] = "https://mangakakalot.com/"

                    resp = task.source.session.get(
                        url, headers=headers, timeout=config.REQUEST_TIMEOUT, stream=True
                    )
                    resp.raise_for_status()

                    content_type = resp.headers.get("content-type", "")
                    if "png" in content_type:
                        ext = ".png"
                    elif "webp" in content_type:
                        ext = ".webp"
                    elif "gif" in content_type:
                        ext = ".gif"
                    else:
                        ext = ".jpg"

                    path = os.path.join(output_dir, f"{idx+1:04d}{ext}")
                    total_dl = 0
                    with open(path, "wb") as f:
                        for chunk in resp.iter_content(config.CHUNK_SIZE):
                            if task.cancel_flag.is_set():
                                return None
                            f.write(chunk)
                            total_dl += len(chunk)

                    with download_lock:
                        task.downloaded_bytes += total_dl
                        if task.start_time:
                            elapsed = time.time() - task.start_time
                            if elapsed > 0:
                                task.speed = task.downloaded_bytes / elapsed

                    return idx, path

                except Exception:
                    if attempt < config.RETRY_ATTEMPTS - 1:
                        time.sleep(config.RETRY_DELAY)
                    else:
                        return None

        results = {}
        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as pool:
            futures = {
                pool.submit(_dl_page, (i, url)): i
                for i, url in enumerate(pages)
            }
            for future in as_completed(futures):
                result = future.result()
                if result:
                    idx, path = result
                    results[idx] = path

        for i in sorted(results.keys()):
            image_paths.append(results[i])

        return image_paths

    def _emit_progress(self, task: DownloadTask):
        if self.on_progress:
            self.on_progress(task)