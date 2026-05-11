#!/usr/bin/env python3
"""
MangaDL - Command Line Interface
Usage:
    python cli.py search <query> [--source SOURCE]
    python cli.py download <url> [OPTIONS]
    python cli.py info <url>
    python cli.py sources
    python cli.py library
"""

import os
import sys
import time
import argparse
import threading
from typing import Optional

import config
from sources import detect_source, SOURCES
from sources.base import MangaInfo, Chapter
from downloader.engine import DownloadEngine


# --- Formatting Helpers ---

def format_bytes(size: int) -> str:
    if size == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB"]
    i = 0
    s = float(size)
    while s >= 1024 and i < len(units) - 1:
        s /= 1024
        i += 1
    return f"{s:.1f} {units[i]}"


def truncate(text: str, length: int) -> str:
    if len(text) <= length:
        return text
    return text[:length - 3] + "..."


def print_header():
    print()
    print("=" * 56)
    print("  MangaDL - Universal Manga/Webtoon Downloader (CLI)")
    print("=" * 56)
    print()


def print_table(headers: list, rows: list, widths: list):
    sep = "  "
    header_line = sep.join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_line)
    print(sep.join("-" * w for w in widths))
    for row in rows:
        line = sep.join(str(c).ljust(w) for c, w in zip(row, widths))
        print(line)


def print_progress_bar(progress: float, width: int = 40) -> str:
    filled = int(width * progress / 100)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {progress:5.1f}%"


# --- Commands ---

def cmd_sources(args):
    """List all available sources."""
    print_header()
    print("Available Sources:")
    print()
    headers = ["Key", "Name", "Base URL"]
    widths = [16, 16, 40]
    rows = []
    for key, cls in SOURCES.items():
        src = cls()
        rows.append([key, src.name, src.base_url])
    print_table(headers, rows, widths)
    print()


def cmd_search(args):
    """Search for manga across sources."""
    query = " ".join(args.query)
    source_key = args.source
    print_header()
    print(f"Searching: \"{query}\"")
    if source_key != "all":
        print(f"Source:    {source_key}")
    print()

    results = []

    def search_source(key, src):
        try:
            found = src.search(query)
            for m in found:
                results.append((key, m))
        except Exception as e:
            print(f"  [!] Error searching {key}: {e}")

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
        if source_key not in SOURCES:
            print(f"Error: Unknown source \"{source_key}\"")
            print(f"Available: {', '.join(SOURCES.keys())}")
            sys.exit(1)
        src = SOURCES[source_key]()
        search_source(source_key, src)

    if not results:
        print("No results found.")
        return

    print(f"Found {len(results)} result(s):")
    print()

    headers = ["#", "Source", "Title", "Author"]
    widths = [4, 14, 40, 20]
    rows = []
    for i, (key, manga) in enumerate(results, 1):
        rows.append([
            i,
            manga.source,
            truncate(manga.title, 40),
            truncate(manga.author or "Unknown", 20),
        ])
    print_table(headers, rows, widths)
    print()

    if not args.no_interactive:
        print("Enter a number to view details, or 'q' to quit:")
        while True:
            try:
                choice = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if choice.lower() in ("q", "quit", "exit", ""):
                break
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(results):
                    key, manga = results[idx]
                    show_manga_interactive(manga.url, key)
                else:
                    print("Invalid number.")
            except ValueError:
                print("Enter a number or 'q'.")


def cmd_info(args):
    """Show manga info from URL."""
    url = args.url
    print_header()
    print(f"Fetching: {url}")
    print()

    source_key, src = detect_source(url)
    if not src:
        print("Error: Could not detect source for this URL.")
        print(f"Supported: {', '.join(SOURCES.keys())}")
        sys.exit(1)

    try:
        manga = src.get_manga_info(url)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print_manga_info(manga, source_key)


def cmd_download(args):
    """Download manga from URL."""
    url = args.url
    format_type = args.format
    mode = args.mode
    chapter_from = args.chapter_from
    chapter_to = args.chapter_to
    chapter_list = args.chapters
    output_dir = args.output or config.DOWNLOAD_DIR

    print_header()
    print(f"URL:    {url}")
    print(f"Format: {format_type}")
    print(f"Mode:   {mode}")
    print(f"Output: {output_dir}")
    print()

    source_key, src = detect_source(url)
    if not src:
        print("Error: Could not detect source for this URL.")
        sys.exit(1)

    print(f"Source: {src.name}")
    print("Fetching manga info...")

    try:
        manga = src.get_manga_info(url)
    except Exception as e:
        print(f"Error fetching manga: {e}")
        sys.exit(1)

    print(f"Title:  {manga.title}")
    print(f"Chapters available: {len(manga.chapters)}")
    print()

    if not manga.chapters:
        print("No chapters found.")
        sys.exit(1)

    # Filter chapters
    selected = select_chapters(manga.chapters, chapter_from, chapter_to, chapter_list)

    if not selected:
        print("No chapters matched the selection criteria.")
        sys.exit(1)

    print(f"Selected {len(selected)} chapter(s):")
    for ch in selected[:10]:
        print(f"  Ch. {ch.number} - {ch.title}")
    if len(selected) > 10:
        print(f"  ... and {len(selected) - 10} more")
    print()

    if not args.yes:
        try:
            confirm = input("Proceed with download? [Y/n] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)
        if confirm in ("n", "no"):
            print("Aborted.")
            sys.exit(0)

    # Override download dir
    original_dl_dir = config.DOWNLOAD_DIR
    config.DOWNLOAD_DIR = output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Start download
    engine = DownloadEngine()
    task_id = engine.create_task(
        manga=manga,
        chapters=selected,
        format_type=format_type,
        mode=mode,
        source=src,
    )

    print()
    print("Downloading...")
    print()

    monitor_task(engine, task_id)

    config.DOWNLOAD_DIR = original_dl_dir


def cmd_interactive(args):
    """Interactive mode."""
    print_header()
    print("Interactive Mode")
    print("Commands: search, url, sources, library, quit")
    print()

    while True:
        try:
            line = input("mangadl> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not line:
            continue

        parts = line.split(None, 1)
        cmd = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""

        if cmd in ("q", "quit", "exit"):
            print("Goodbye.")
            break
        elif cmd == "search":
            if not rest:
                print("Usage: search <query>")
                continue
            interactive_search(rest)
        elif cmd == "url":
            if not rest:
                print("Usage: url <manga_url>")
                continue
            show_manga_interactive(rest)
        elif cmd == "sources":
            for key, cls in SOURCES.items():
                src = cls()
                print(f"  {key:16s} {src.name}")
        elif cmd == "library":
            list_library()
        elif cmd == "help":
            print("Commands:")
            print("  search <query>  - Search for manga")
            print("  url <url>       - Load manga from URL")
            print("  sources         - List available sources")
            print("  library         - Show downloaded files")
            print("  quit            - Exit")
        else:
            print(f"Unknown command: {cmd}. Type 'help' for commands.")


def cmd_library(args):
    """List downloaded files."""
    print_header()
    list_library()


# --- Helper Functions ---

def select_chapters(chapters: list, ch_from: Optional[str], ch_to: Optional[str],
                    ch_list: Optional[str]) -> list:
    """Filter chapters based on range or explicit list."""
    if ch_list:
        # Parse comma-separated list: "1,2,5-10,15"
        selected_nums = set()
        for part in ch_list.split(","):
            part = part.strip()
            if "-" in part:
                try:
                    a, b = part.split("-", 1)
                    start = float(a.strip())
                    end = float(b.strip())
                    for ch in chapters:
                        try:
                            num = float(ch.number)
                            if start <= num <= end:
                                selected_nums.add(ch.number)
                        except ValueError:
                            pass
                except ValueError:
                    pass
            else:
                selected_nums.add(part)

        return [ch for ch in chapters if ch.number in selected_nums]

    if ch_from is not None or ch_to is not None:
        start = float(ch_from) if ch_from else -float("inf")
        end = float(ch_to) if ch_to else float("inf")
        selected = []
        for ch in chapters:
            try:
                num = float(ch.number)
                if start <= num <= end:
                    selected.append(ch)
            except ValueError:
                pass
        return selected

    return list(chapters)


def print_manga_info(manga: MangaInfo, source_key: str = ""):
    """Print manga details."""
    print("-" * 56)
    print(f"Title:    {manga.title}")
    print(f"Author:   {manga.author}")
    print(f"Status:   {manga.status}")
    print(f"Source:   {manga.source}")
    if manga.genres:
        print(f"Genres:   {', '.join(manga.genres[:8])}")
    if manga.description:
        desc = manga.description[:200]
        if len(manga.description) > 200:
            desc += "..."
        print(f"Summary:  {desc}")
    print(f"Chapters: {len(manga.chapters)}")
    print(f"URL:      {manga.url}")
    print("-" * 56)

    if manga.chapters:
        print()
        print("Chapters:")
        headers = ["#", "Number", "Title", "Volume"]
        widths = [5, 10, 40, 10]
        rows = []
        display_chapters = manga.chapters
        truncated = False
        if len(display_chapters) > 50:
            display_chapters = manga.chapters[:25] + manga.chapters[-25:]
            truncated = True

        for i, ch in enumerate(manga.chapters[:25], 1):
            rows.append([
                i,
                ch.number,
                truncate(ch.title, 40),
                ch.volume or "-",
            ])

        if truncated:
            rows.append(["...", "...", f"... {len(manga.chapters) - 50} more ...", "..."])
            for i, ch in enumerate(manga.chapters[-25:], len(manga.chapters) - 24):
                rows.append([
                    i,
                    ch.number,
                    truncate(ch.title, 40),
                    ch.volume or "-",
                ])

        print_table(headers, rows, widths)
    print()


def show_manga_interactive(url: str, source_key: str = None):
    """Fetch and display manga, then offer download options."""
    if source_key:
        src = SOURCES[source_key]()
    else:
        source_key, src = detect_source(url)
        if not src:
            print("Error: Could not detect source for this URL.")
            return

    print(f"Fetching from {src.name}...")
    try:
        manga = src.get_manga_info(url)
    except Exception as e:
        print(f"Error: {e}")
        return

    print()
    print_manga_info(manga, source_key)

    if not manga.chapters:
        return

    print("Download options:")
    print("  Enter chapter selection (e.g. 'all', '1-10', '1,3,5,8-12')")
    print("  Or 'back' to return.")
    print()

    try:
        selection = input("Chapters> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if selection.lower() in ("back", "b", "q", ""):
        return

    if selection.lower() == "all":
        selected = list(manga.chapters)
    else:
        selected = select_chapters(manga.chapters, None, None, selection)

    if not selected:
        print("No chapters matched.")
        return

    print(f"Selected {len(selected)} chapter(s).")

    # Format
    print()
    print("Format options: cbz, pdf, epub, images")
    try:
        fmt = input("Format [cbz]> ").strip().lower() or "cbz"
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if fmt not in ("cbz", "pdf", "epub", "images"):
        print(f"Unknown format: {fmt}. Using cbz.")
        fmt = "cbz"

    # Mode
    print()
    print("Mode options: chapter, volume, all")
    try:
        mode = input("Mode [chapter]> ").strip().lower() or "chapter"
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if mode not in ("chapter", "volume", "all"):
        print(f"Unknown mode: {mode}. Using chapter.")
        mode = "chapter"

    print()
    print(f"Downloading {len(selected)} chapter(s) as {fmt} ({mode} mode)...")
    print()

    engine = DownloadEngine()
    task_id = engine.create_task(
        manga=manga,
        chapters=selected,
        format_type=fmt,
        mode=mode,
        source=src,
    )

    monitor_task(engine, task_id)


def interactive_search(query: str):
    """Search and display results interactively."""
    print(f"Searching: \"{query}\"")
    results = []

    def search_source(key, src):
        try:
            found = src.search(query)
            for m in found:
                results.append((key, m))
        except Exception:
            pass

    threads = []
    for key, cls in SOURCES.items():
        src = cls()
        t = threading.Thread(target=search_source, args=(key, src))
        t.start()
        threads.append(t)
    for t in threads:
        t.join(timeout=30)

    if not results:
        print("No results found.")
        return

    print(f"Found {len(results)} result(s):")
    print()
    for i, (key, manga) in enumerate(results, 1):
        print(f"  {i:3d}. [{manga.source}] {truncate(manga.title, 50)} - {truncate(manga.author or 'Unknown', 20)}")
    print()
    print("Enter number to view, or 'back':")

    try:
        choice = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if choice.lower() in ("back", "b", "q", ""):
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(results):
            key, manga = results[idx]
            show_manga_interactive(manga.url, key)
        else:
            print("Invalid number.")
    except ValueError:
        print("Invalid input.")


def monitor_task(engine: DownloadEngine, task_id: str):
    """Monitor download progress in the terminal."""
    last_line_len = 0

    while True:
        task = engine.get_task(task_id)
        if not task:
            break

        speed_str = format_bytes(int(task.speed)) + "/s" if task.speed else "-- B/s"
        dl_str = format_bytes(int(task.downloaded_bytes))
        bar = print_progress_bar(task.progress, 30)

        status_line = (
            f"\r  {bar}  "
            f"{task.completed_chapters}/{task.total_chapters} ch  "
            f"{speed_str}  {dl_str}  "
            f"{truncate(task.current_chapter, 30)}"
        )

        padding = max(0, last_line_len - len(status_line))
        sys.stdout.write(status_line + " " * padding)
        sys.stdout.flush()
        last_line_len = len(status_line)

        if task.status in ("completed", "error", "cancelled"):
            break

        time.sleep(0.5)

    print()
    print()

    task = engine.get_task(task_id)
    if task:
        if task.status == "completed":
            print(f"Download completed.")
            print(f"Total downloaded: {format_bytes(int(task.downloaded_bytes))}")
            if task.output_paths:
                print(f"Output files:")
                for p in task.output_paths:
                    print(f"  {p}")
        elif task.status == "error":
            print(f"Download finished with errors.")
            for err in task.errors:
                print(f"  [!] {err}")
        elif task.status == "cancelled":
            print("Download was cancelled.")

    print()


def list_library():
    """List files in the download directory."""
    if not os.path.exists(config.DOWNLOAD_DIR):
        print("Download directory is empty.")
        return

    files = []
    for root, dirs, filenames in os.walk(config.DOWNLOAD_DIR):
        for fname in filenames:
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, config.DOWNLOAD_DIR)
            try:
                size = os.path.getsize(fpath)
            except OSError:
                size = 0
            files.append((rel, size))

    if not files:
        print("Library is empty.")
        return

    files.sort(key=lambda f: f[0])

    print(f"Downloaded files ({len(files)}):")
    print()
    headers = ["File", "Size"]
    widths = [56, 12]
    rows = []
    for name, size in files:
        rows.append([truncate(name, 56), format_bytes(size)])
    print_table(headers, rows, widths)

    total_size = sum(s for _, s in files)
    print()
    print(f"Total: {len(files)} files, {format_bytes(total_size)}")
    print()


# --- Argument Parser ---

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mangadl",
        description="MangaDL - Universal Manga/Webtoon Downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s search "one piece"
  %(prog)s search "solo leveling" --source mangadex
  %(prog)s info https://mangadex.org/title/xxxxx
  %(prog)s download https://mangadex.org/title/xxxxx
  %(prog)s download https://mangadex.org/title/xxxxx --format pdf --mode volume
  %(prog)s download https://mangadex.org/title/xxxxx --chapters 1-10
  %(prog)s download https://mangadex.org/title/xxxxx --chapters 1,5,10-20
  %(prog)s download https://manganato.com/manga-xxxx --from 1 --to 50
  %(prog)s sources
  %(prog)s library
  %(prog)s interactive
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # search
    sp_search = subparsers.add_parser("search", help="Search for manga")
    sp_search.add_argument("query", nargs="+", help="Search query")
    sp_search.add_argument(
        "-s", "--source", default="all",
        choices=["all"] + list(SOURCES.keys()),
        help="Source to search (default: all)",
    )
    sp_search.add_argument(
        "--no-interactive", action="store_true",
        help="Disable interactive selection after results",
    )

    # info
    sp_info = subparsers.add_parser("info", help="Show manga info from URL")
    sp_info.add_argument("url", help="Manga URL")

    # download
    sp_dl = subparsers.add_parser("download", aliases=["dl"], help="Download manga from URL")
    sp_dl.add_argument("url", help="Manga URL")
    sp_dl.add_argument(
        "-f", "--format", default="cbz",
        choices=["cbz", "pdf", "epub", "images"],
        help="Export format (default: cbz)",
    )
    sp_dl.add_argument(
        "-m", "--mode", default="chapter",
        choices=["chapter", "volume", "all"],
        help="Download mode (default: chapter)",
    )
    sp_dl.add_argument(
        "--from", dest="chapter_from", default=None,
        help="Start chapter number",
    )
    sp_dl.add_argument(
        "--to", dest="chapter_to", default=None,
        help="End chapter number",
    )
    sp_dl.add_argument(
        "-c", "--chapters", default=None,
        help="Chapter selection (e.g. '1,2,5-10,15')",
    )
    sp_dl.add_argument(
        "-o", "--output", default=None,
        help="Output directory (default: ./downloads)",
    )
    sp_dl.add_argument(
        "-y", "--yes", action="store_true",
        help="Skip confirmation prompt",
    )

    # sources
    subparsers.add_parser("sources", help="List available sources")

    # library
    subparsers.add_parser("library", help="List downloaded files")

    # interactive
    subparsers.add_parser("interactive", aliases=["i"], help="Interactive mode")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        print()
        print("Tip: Run 'python cli.py interactive' for interactive mode.")
        sys.exit(0)

    command_map = {
        "search": cmd_search,
        "info": cmd_info,
        "download": cmd_download,
        "dl": cmd_download,
        "sources": cmd_sources,
        "library": cmd_library,
        "interactive": cmd_interactive,
        "i": cmd_interactive,
    }

    func = command_map.get(args.command)
    if func:
        try:
            func(args)
        except KeyboardInterrupt:
            print("\nInterrupted.")
            sys.exit(130)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()