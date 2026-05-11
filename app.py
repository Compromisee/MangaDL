"""
MangaDL - Web Server
Self-contained single-file executable.
"""
import os
import sys

# --- PyInstaller path resolution ---
def _resolve_paths():
    """Resolve correct paths whether running from source or PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        bundle_dir = sys._MEIPASS
        exe_dir = os.path.dirname(sys.executable)
    else:
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
        exe_dir = bundle_dir
    return bundle_dir, exe_dir

BUNDLE_DIR, EXE_DIR = _resolve_paths()

if BUNDLE_DIR not in sys.path:
    sys.path.insert(0, BUNDLE_DIR)

# --- Imports ---
import json
import threading
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

import config
from sources import detect_source, SOURCES
from sources.base import MangaInfo, Chapter
from downloader.engine import DownloadEngine

# --- Flask app with bundled paths ---
app = Flask(
    __name__,
    template_folder=os.path.join(BUNDLE_DIR, "templates"),
    static_folder=os.path.join(BUNDLE_DIR, "static"),
)
app.config["SECRET_KEY"] = "mangadl-secret-key-change-me"
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

engine = DownloadEngine()


LANGUAGE_NAMES = {
    "en": "English", "ja": "Japanese", "ko": "Korean",
    "zh": "Chinese", "zh-hans": "Chinese (Simplified)", "zh-hant": "Chinese (Traditional)",
    "es": "Spanish", "es-la": "Spanish (Latin America)",
    "fr": "French", "de": "German", "it": "Italian",
    "pt": "Portuguese", "pt-br": "Portuguese (Brazil)",
    "ru": "Russian", "pl": "Polish", "nl": "Dutch",
    "ar": "Arabic", "tr": "Turkish", "vi": "Vietnamese",
    "th": "Thai", "id": "Indonesian", "ms": "Malay",
    "hi": "Hindi", "bn": "Bengali", "uk": "Ukrainian",
    "ro": "Romanian", "hu": "Hungarian", "cs": "Czech",
    "el": "Greek", "sv": "Swedish", "da": "Danish",
    "fi": "Finnish", "no": "Norwegian", "he": "Hebrew",
    "fa": "Persian", "bg": "Bulgarian", "hr": "Croatian",
    "lt": "Lithuanian", "mn": "Mongolian", "my": "Burmese",
    "tl": "Filipino", "ka": "Georgian", "la": "Latin",
}


def get_language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code.upper())


def emit_progress(task):
    socketio.emit("download_progress", {
        "task_id": task.task_id,
        "title": task.manga.title,
        "status": task.status,
        "progress": task.progress,
        "current_chapter": task.current_chapter,
        "total_chapters": task.total_chapters,
        "completed_chapters": task.completed_chapters,
        "errors": task.errors[-5:],
        "speed": task.speed,
        "downloaded_bytes": task.downloaded_bytes,
        "format": task.format_type,
        "mode": task.mode,
    })


engine.on_progress = emit_progress


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.json
    query = data.get("query", "").strip()
    source_key = data.get("source", "all")

    if not query:
        return jsonify({"error": "Query is empty"}), 400

    results = []

    def search_source(key, src):
        try:
            found = src.search(query)
            for m in found:
                results.append({
                    "id": m.id,
                    "title": m.title,
                    "author": m.author,
                    "description": m.description,
                    "cover_url": m.cover_url,
                    "url": m.url,
                    "source": m.source,
                    "source_key": key,
                    "status": m.status,
                    "genres": m.genres,
                    "available_languages": m.available_languages,
                })
        except Exception as e:
            print(f"Search error ({key}): {e}")

    if source_key == "all":
        threads = []
        for key, cls in SOURCES.items():
            src = cls()
            t = threading.Thread(target=search_source, args=(key, src))
            t.start()
            threads.append(t)
        for t in threads:
            t.join(timeout=30)
    else:
        if source_key in SOURCES:
            src = SOURCES[source_key]()
            search_source(source_key, src)
        else:
            return jsonify({"error": f"Unknown source: {source_key}"}), 400

    return jsonify({"results": results})


@app.route("/api/languages", methods=["POST"])
def api_languages():
    data = request.json
    url = data.get("url", "").strip()
    source_key = data.get("source_key")

    if not url:
        return jsonify({"error": "URL is empty"}), 400

    try:
        if source_key and source_key in SOURCES:
            src = SOURCES[source_key]()
        else:
            source_key, src = detect_source(url)
            if not src:
                return jsonify({"error": "Cannot detect source"}), 400

        languages = src.get_languages(url)
        lang_list = [{"code": c, "name": get_language_name(c)} for c in languages]
        return jsonify({"languages": lang_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/manga_info", methods=["POST"])
def api_manga_info():
    data = request.json
    url = data.get("url", "").strip()
    source_key = data.get("source_key")
    language = data.get("language", "en")

    if not url:
        return jsonify({"error": "URL is empty"}), 400

    try:
        if source_key and source_key in SOURCES:
            src = SOURCES[source_key]()
        else:
            source_key, src = detect_source(url)
            if not src:
                return jsonify({"error": "Could not detect source for this URL"}), 400

        manga = src.get_manga_info(url, language=language)

        chapters_list = []
        for ch in manga.chapters:
            chapters_list.append({
                "id": ch.id,
                "number": ch.number,
                "title": ch.title,
                "url": ch.url,
                "volume": ch.volume,
                "language": ch.language,
                "page_count": ch.page_count,
            })

        lang_list = [{"code": c, "name": get_language_name(c)} for c in manga.available_languages]

        return jsonify({
            "id": manga.id,
            "title": manga.title,
            "author": manga.author,
            "description": manga.description,
            "cover_url": manga.cover_url,
            "url": manga.url,
            "source": manga.source,
            "source_key": source_key,
            "status": manga.status,
            "genres": manga.genres,
            "chapters": chapters_list,
            "available_languages": lang_list,
            "current_language": language,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.json
    manga_data = data.get("manga")
    chapter_indices = data.get("chapter_indices", [])
    format_type = data.get("format", "cbz")
    mode = data.get("mode", "chapter")

    if not manga_data:
        return jsonify({"error": "No manga data"}), 400

    source_key = manga_data.get("source_key")
    url = manga_data.get("url", "")

    if source_key and source_key in SOURCES:
        src = SOURCES[source_key]()
    else:
        source_key, src = detect_source(url)
        if not src:
            return jsonify({"error": "Cannot determine source"}), 400

    try:
        chapters_data = manga_data.get("chapters", [])
        chapters = []
        for ch_data in chapters_data:
            chapters.append(Chapter(
                id=ch_data["id"],
                number=ch_data["number"],
                title=ch_data["title"],
                url=ch_data["url"],
                volume=ch_data.get("volume"),
                language=ch_data.get("language", "en"),
            ))

        selected_chapters = [chapters[i] for i in chapter_indices if i < len(chapters)]
        if not selected_chapters:
            return jsonify({"error": "No chapters selected"}), 400

        manga_info = MangaInfo(
            id=manga_data.get("id", ""),
            title=manga_data.get("title", "Unknown"),
            author=manga_data.get("author", "Unknown"),
            description=manga_data.get("description", ""),
            cover_url=manga_data.get("cover_url", ""),
            url=url,
            source=manga_data.get("source", ""),
            chapters=selected_chapters,
            status=manga_data.get("status", "Unknown"),
            genres=manga_data.get("genres", []),
        )

        task_id = engine.create_task(
            manga=manga_info,
            chapters=selected_chapters,
            format_type=format_type,
            mode=mode,
            source=src,
        )

        return jsonify({"task_id": task_id, "message": "Download started"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tasks")
def api_tasks():
    tasks = engine.get_all_tasks()
    result = []
    for t in tasks:
        result.append({
            "task_id": t.task_id,
            "title": t.manga.title,
            "status": t.status,
            "progress": t.progress,
            "current_chapter": t.current_chapter,
            "total_chapters": t.total_chapters,
            "completed_chapters": t.completed_chapters,
            "errors": t.errors[-5:],
            "speed": t.speed,
            "downloaded_bytes": t.downloaded_bytes,
            "format": t.format_type,
            "mode": t.mode,
        })
    return jsonify({"tasks": result})


@app.route("/api/cancel/<task_id>", methods=["POST"])
def api_cancel(task_id):
    engine.cancel_task(task_id)
    return jsonify({"message": "Cancelled"})


@app.route("/api/clear_completed", methods=["POST"])
def api_clear_completed():
    to_remove = [
        tid for tid, t in engine.tasks.items()
        if t.status in ("completed", "error", "cancelled")
    ]
    for tid in to_remove:
        del engine.tasks[tid]
    return jsonify({"message": f"Cleared {len(to_remove)} tasks"})


@app.route("/api/library")
def api_library():
    files = []
    for root, dirs, filenames in os.walk(config.DOWNLOAD_DIR):
        for fname in filenames:
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, config.DOWNLOAD_DIR)
            try:
                size = os.path.getsize(fpath)
            except OSError:
                size = 0
            files.append({"name": rel_path, "size": size, "path": fpath})
    files.sort(key=lambda f: f["name"])
    return jsonify({"files": files})


@app.route("/api/open_folder", methods=["POST"])
def api_open_folder():
    import subprocess
    import platform
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(config.DOWNLOAD_DIR)
        elif system == "Darwin":
            subprocess.Popen(["open", config.DOWNLOAD_DIR])
        else:
            subprocess.Popen(["xdg-open", config.DOWNLOAD_DIR])
    except Exception:
        pass
    return jsonify({"message": "Opened"})


@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    return jsonify({
        "threads": config.MAX_WORKERS,
        "timeout": config.REQUEST_TIMEOUT,
        "retries": config.RETRY_ATTEMPTS,
        "download_dir": config.DOWNLOAD_DIR,
        "max_tasks": getattr(config, "MAX_CONCURRENT_TASKS", 3),
    })


@app.route("/api/settings", methods=["POST"])
def api_set_settings():
    data = request.json

    if "threads" in data:
        val = int(data["threads"])
        if 1 <= val <= 32:
            config.MAX_WORKERS = val

    if "timeout" in data:
        val = int(data["timeout"])
        if 5 <= val <= 300:
            config.REQUEST_TIMEOUT = val

    if "retries" in data:
        val = int(data["retries"])
        if 1 <= val <= 20:
            config.RETRY_ATTEMPTS = val

    if "max_tasks" in data:
        val = int(data["max_tasks"])
        if 1 <= val <= 8:
            config.MAX_CONCURRENT_TASKS = val

    if "download_dir" in data:
        new_dir = data["download_dir"].strip()
        if new_dir:
            try:
                os.makedirs(new_dir, exist_ok=True)
                config.DOWNLOAD_DIR = new_dir
            except Exception as e:
                return jsonify({"error": f"Invalid directory: {e}"}), 400

    return jsonify({
        "message": "Settings saved",
        "threads": config.MAX_WORKERS,
        "timeout": config.REQUEST_TIMEOUT,
        "retries": config.RETRY_ATTEMPTS,
        "download_dir": config.DOWNLOAD_DIR,
        "max_tasks": getattr(config, "MAX_CONCURRENT_TASKS", 3),
    })


# --- Entry point ---
if __name__ == "__main__":
    import webbrowser
    import time

    PORT = 5000
    URL = f"http://localhost:{PORT}"

    def open_browser():
        time.sleep(1.5)
        try:
            webbrowser.open(URL)
        except Exception:
            pass

    print()
    print("=" * 56)
    print("  MangaDL - Universal Manga Downloader")
    print(f"  Server:    {URL}")
    print(f"  Downloads: {config.DOWNLOAD_DIR}")
    print("=" * 56)
    print()
    print("  Opening browser automatically...")
    print("  Press Ctrl+C to stop the server.")
    print()

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        socketio.run(
            app,
            host="0.0.0.0",
            port=PORT,
            debug=False,
            allow_unsafe_werkzeug=True,
        )
    except KeyboardInterrupt:
        print("\nServer stopped.")