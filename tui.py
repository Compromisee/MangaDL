#!/usr/bin/env python3
"""
MangaDL - Terminal UI (TUI)
Rich interactive terminal interface with colors, gradients, and live progress.
"""

import os
import sys
import time
import threading
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor

# --- Check for rich ---
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.progress import (
        Progress, BarColumn, TextColumn, TimeRemainingColumn,
        SpinnerColumn, TaskProgressColumn, DownloadColumn,
        TransferSpeedColumn,
    )
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.text import Text
    from rich.tree import Tree
    from rich.columns import Columns
    from rich.rule import Rule
    from rich.align import Align
    from rich.box import ROUNDED, HEAVY, SIMPLE, MINIMAL
    from rich.style import Style
    from rich.theme import Theme
    from rich.markup import escape
    from rich import box
except ImportError:
    print("This TUI requires the 'rich' library.")
    print("Install it with: pip install rich")
    sys.exit(1)

import config
from sources import detect_source, SOURCES
from sources.base import MangaInfo, Chapter
from downloader.engine import DownloadEngine


# --- Theme ---
CUSTOM_THEME = Theme({
    "title": "bold bright_white",
    "subtitle": "dim white",
    "accent": "bold dodger_blue2",
    "accent_dim": "dim dodger_blue2",
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "muted": "dim white",
    "source_mangadex": "bold bright_magenta",
    "source_manganato": "bold bright_cyan",
    "source_webtoons": "bold bright_green",
    "source_mangakakalot": "bold bright_yellow",
    "header_gradient_1": "bold bright_blue",
    "header_gradient_2": "bold dodger_blue2",
    "header_gradient_3": "bold deep_sky_blue1",
    "header_gradient_4": "bold cyan",
    "vol_header": "bold bright_cyan",
    "ch_number": "bold white",
    "ch_title": "dim white",
    "selected": "bold bright_green",
    "deselected": "dim red",
    "progress_complete": "bold bright_green",
    "progress_remaining": "dim white",
    "info_label": "bold bright_blue",
    "info_value": "white",
    "menu_key": "bold bright_yellow",
    "menu_desc": "white",
    "separator": "dim bright_black",
})

console = Console(theme=CUSTOM_THEME)


# --- Gradient Helpers ---
GRADIENT_BLUE = [
    "#1a1aff", "#2a4aff", "#3a6aff", "#4a8aff",
    "#5aaaff", "#6acaff", "#7aeaff", "#8affff",
]

GRADIENT_GREEN = [
    "#004400", "#006600", "#008800", "#00aa00",
    "#00cc00", "#00ee00", "#22ff22", "#66ff66",
]

GRADIENT_FIRE = [
    "#ff0000", "#ff2200", "#ff4400", "#ff6600",
    "#ff8800", "#ffaa00", "#ffcc00", "#ffee00",
]

GRADIENT_PURPLE = [
    "#4400aa", "#5500bb", "#6600cc", "#7700dd",
    "#8833ee", "#9955ff", "#aa77ff", "#bb99ff",
]


def gradient_text(text: str, colors: list) -> Text:
    """Apply a gradient of colors across a text string."""
    result = Text()
    if not text:
        return result
    step = max(1, len(text) // len(colors))
    for i, char in enumerate(text):
        color_idx = min(i // max(step, 1), len(colors) - 1)
        result.append(char, style=Style(color=colors[color_idx], bold=True))
    return result


def gradient_bar(progress: float, width: int = 40,
                 colors: list = None, empty_char: str = "━",
                 fill_char: str = "━") -> Text:
    """Create a gradient progress bar."""
    if colors is None:
        if progress >= 100:
            colors = GRADIENT_GREEN
        elif progress >= 50:
            colors = GRADIENT_BLUE
        else:
            colors = GRADIENT_PURPLE

    filled = int(width * min(progress, 100) / 100)
    empty = width - filled

    result = Text()
    for i in range(filled):
        color_idx = min(i * len(colors) // max(filled, 1), len(colors) - 1)
        result.append(fill_char, style=Style(color=colors[color_idx]))

    result.append(empty_char * empty, style="dim bright_black")
    return result


def format_bytes(b) -> str:
    b = float(b or 0)
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


def source_style(source: str) -> str:
    s = source.lower()
    if "mangadex" in s:
        return "source_mangadex"
    elif "manganato" in s:
        return "source_manganato"
    elif "webtoon" in s:
        return "source_webtoons"
    elif "mangakakalot" in s:
        return "source_mangakakalot"
    return "accent"


# --- Banner ---
def print_banner():
    console.print()
    lines = [
        "  __  __                         ____  _     ",
        " |  \\/  | __ _ _ __   __ _  __ _|  _ \\| |    ",
        " | |\\/| |/ _` | '_ \\ / _` |/ _` | | | | |    ",
        " | |  | | (_| | | | | (_| | (_| | |_| | |___ ",
        " |_|  |_|\\__,_|_| |_|\\__, |\\__,_|____/|_____|",
        "                     |___/                    ",
    ]
    gradients = [GRADIENT_BLUE, GRADIENT_PURPLE, GRADIENT_BLUE, GRADIENT_PURPLE, GRADIENT_BLUE, GRADIENT_PURPLE]
    for line, grad in zip(lines, gradients):
        console.print(gradient_text(line, grad))

    console.print()
    console.print(
        "  [dim]Universal Manga / Manhwa / Webtoon Downloader[/]"
    )
    console.print(
        f"  [dim]v2.0  |  {len(SOURCES)} sources  |  4 export formats[/]"
    )
    console.print()


# --- Menus ---
def print_main_menu():
    console.print(Rule(style="separator"))
    menu = Table(show_header=False, box=None, padding=(0, 2), expand=False)
    menu.add_column(style="menu_key", width=4)
    menu.add_column(style="menu_desc")
    menu.add_row("[1]", "Search manga")
    menu.add_row("[2]", "Import from URL")
    menu.add_row("[3]", "View downloads")
    menu.add_row("[4]", "Browse library")
    menu.add_row("[5]", "Sources info")
    menu.add_row("[6]", "Settings")
    menu.add_row("[q]", "Quit")
    console.print(menu)
    console.print()


# --- State ---
class TUIState:
    def __init__(self):
        self.engine = DownloadEngine()
        self.manga: Optional[MangaInfo] = None
        self.chapters: list = []
        self.source = None
        self.source_key = ""
        self.language = "en"
        self.default_format = "cbz"
        self.default_mode = "chapter"
        self.settings = {
            "threads": config.MAX_WORKERS,
            "format": "cbz",
            "mode": "chapter",
            "language": "en",
        }


state = TUIState()


# --- Search ---
def cmd_search():
    console.print()
    console.print("[title]Search[/]")
    console.print("[subtitle]Search across all supported sources[/]")
    console.print()

    query = Prompt.ask("[accent]Search query[/]")
    if not query.strip():
        return

    # Source selection
    source_names = ["all"] + list(SOURCES.keys())
    console.print(f"[muted]Available sources: {', '.join(source_names)}[/]")
    source_key = Prompt.ask("[accent]Source[/]", default="all",
                            choices=source_names)

    console.print()

    results = []
    errors = []

    with Progress(
        SpinnerColumn(style="accent"),
        TextColumn("[accent]Searching...[/]"),
        TextColumn("[muted]{task.description}[/]"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("", total=None)

        def search_one(key, src):
            progress.update(task, description=f"[{source_style(key)}]{key}[/]")
            try:
                found = src.search(query)
                for m in found:
                    results.append((key, m))
            except Exception as e:
                errors.append(f"{key}: {e}")

        if source_key == "all":
            threads = []
            for key, cls in SOURCES.items():
                t = threading.Thread(target=search_one, args=(key, cls()))
                t.start()
                threads.append(t)
            for t in threads:
                t.join(timeout=30)
        else:
            search_one(source_key, SOURCES[source_key]())

    if errors:
        for err in errors:
            console.print(f"[warning]  Warning: {err}[/]")

    if not results:
        console.print("[error]No results found.[/]")
        return

    # Display results
    console.print()
    console.print(f"[success]{len(results)} result(s) found[/]")
    console.print()

    table = Table(
        box=box.ROUNDED,
        border_style="dim bright_black",
        header_style="bold bright_white",
        row_styles=["", "dim"],
        expand=True,
        padding=(0, 1),
    )
    table.add_column("#", style="accent", width=4, justify="right")
    table.add_column("Title", style="white", ratio=4)
    table.add_column("Author", style="muted", ratio=2)
    table.add_column("Source", ratio=1)
    table.add_column("Status", style="muted", width=12)

    for i, (key, manga) in enumerate(results, 1):
        src_sty = source_style(manga.source or key)
        table.add_row(
            str(i),
            escape(manga.title[:60]),
            escape((manga.author or "Unknown")[:25]),
            f"[{src_sty}]{escape(manga.source or key)}[/]",
            escape(manga.status or ""),
        )

    console.print(table)
    console.print()

    # Selection
    console.print("[muted]Enter number to view details, or 'b' to go back[/]")
    while True:
        choice = Prompt.ask("[accent]Select[/]", default="b")
        if choice.lower() in ("b", "back", "q", ""):
            return
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                key, manga = results[idx]
                view_manga(manga.url, key)
                return
            else:
                console.print("[error]Invalid number[/]")
        except ValueError:
            console.print("[error]Enter a number or 'b'[/]")


# --- URL Import ---
def cmd_url():
    console.print()
    console.print("[title]URL Import[/]")
    console.print("[subtitle]Paste a manga URL from any supported source[/]")
    console.print()

    console.print("[muted]Supported: " + ", ".join(SOURCES.keys()) + "[/]")
    console.print()

    url = Prompt.ask("[accent]URL[/]")
    if not url.strip():
        return

    source_key, src = detect_source(url)
    if not src:
        console.print("[error]Could not detect source for this URL.[/]")
        return

    view_manga(url, source_key)


# --- View Manga ---
def view_manga(url: str, source_key: str):
    console.print()

    manga = None
    with Progress(
        SpinnerColumn(style="accent"),
        TextColumn("[accent]Fetching manga info...[/]"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("", total=None)
        try:
            src = SOURCES[source_key]()
            manga = src.get_manga_info(url, language=state.settings["language"])
            state.manga = manga
            state.chapters = manga.chapters
            state.source = src
            state.source_key = source_key
        except Exception as e:
            console.print(f"[error]Error: {e}[/]")
            return

    if not manga:
        return

    # --- Display manga info ---
    print_manga_detail(manga)

    # --- Available languages ---
    langs = manga.available_languages or []
    if langs:
        lang_codes = []
        for l in langs:
            if isinstance(l, dict):
                lang_codes.append(l.get("code", "en"))
            else:
                lang_codes.append(l)

        if len(lang_codes) > 1:
            console.print()
            lang_display = " ".join(
                f"[bold bright_cyan]{c}[/]" if c == state.settings["language"]
                else f"[dim]{c}[/]"
                for c in lang_codes[:30]
            )
            console.print(f"  Languages: {lang_display}")
            if len(lang_codes) > 30:
                console.print(f"  [dim]...and {len(lang_codes) - 30} more[/]")

    # --- Chapter / Volume summary ---
    volumes = {}
    for ch in manga.chapters:
        v = ch.volume or "No Volume"
        volumes.setdefault(v, []).append(ch)

    named_vols = {k: v for k, v in volumes.items() if k != "No Volume"}
    unassigned = volumes.get("No Volume", [])

    console.print()
    summary = Text()
    summary.append("  Chapters: ", style="info_label")
    summary.append(f"{len(manga.chapters)}", style="info_value")
    summary.append("   Volumes: ", style="info_label")
    summary.append(f"{len(named_vols)}", style="info_value")
    if unassigned:
        summary.append(f" (+{len(unassigned)} unassigned)", style="muted")
    console.print(summary)

    if not manga.chapters:
        console.print("[warning]No chapters found for this language.[/]")
        return

    # --- Action menu ---
    manga_action_menu(manga, volumes)


def print_manga_detail(manga: MangaInfo):
    """Print a nice manga detail panel."""
    info_text = Text()
    info_text.append("Title:   ", style="info_label")
    info_text.append(f"{manga.title}\n", style="bold bright_white")
    info_text.append("Author:  ", style="info_label")
    info_text.append(f"{manga.author or 'Unknown'}\n", style="info_value")
    info_text.append("Status:  ", style="info_label")

    status = manga.status or "Unknown"
    status_style = "success" if "ongoing" in status.lower() else \
                   "warning" if "completed" in status.lower() else "info_value"
    info_text.append(f"{status}\n", style=status_style)

    info_text.append("Source:  ", style="info_label")
    info_text.append(f"{manga.source}\n", style=source_style(manga.source))

    if manga.genres:
        info_text.append("Genres:  ", style="info_label")
        genre_parts = []
        for g in manga.genres[:10]:
            genre_parts.append(f"[dim bright_cyan]{g}[/]")
        info_text.append(" ".join(genre_parts) + "\n")

    if manga.description:
        desc = manga.description[:250]
        if len(manga.description) > 250:
            desc += "..."
        info_text.append("\n")
        info_text.append(desc, style="muted")

    panel = Panel(
        info_text,
        title=gradient_text(f" {manga.title[:50]} ", GRADIENT_BLUE),
        border_style="bright_blue",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)


def manga_action_menu(manga: MangaInfo, volumes: dict):
    """Interactive menu for a loaded manga."""
    selected = set(range(len(manga.chapters)))  # All selected by default

    while True:
        console.print()
        console.print(Rule(
            gradient_text(" Actions ", GRADIENT_BLUE),
            style="separator",
        ))

        sel_count = len(selected)
        total = len(manga.chapters)
        sel_bar = gradient_bar(sel_count / total * 100 if total else 0, width=20, colors=GRADIENT_GREEN)

        status_line = Text()
        status_line.append(f"  {sel_count}/{total} chapters selected  ", style="muted")
        status_line.append(sel_bar)
        console.print(status_line)
        console.print()

        menu = Table(show_header=False, box=None, padding=(0, 2), expand=False)
        menu.add_column(style="menu_key", width=4)
        menu.add_column(style="menu_desc")
        menu.add_row("[1]", "View chapters")
        menu.add_row("[2]", "View volumes")
        menu.add_row("[3]", "Select chapters (range / list)")
        menu.add_row("[4]", "Select volumes")
        menu.add_row("[5]", "Select all / none / invert")
        menu.add_row("[6]", "Change language")
        menu.add_row("[d]", f"Download selected ({sel_count} ch.)")
        menu.add_row("[b]", "Back")
        console.print(menu)
        console.print()

        choice = Prompt.ask("[accent]Action[/]", default="b")

        if choice == "1":
            show_chapter_list(manga.chapters, selected)
        elif choice == "2":
            show_volume_list(manga.chapters, volumes, selected)
        elif choice == "3":
            selected = select_chapters_interactive(manga.chapters, selected)
        elif choice == "4":
            selected = select_volumes_interactive(manga.chapters, volumes, selected)
        elif choice == "5":
            selected = bulk_select_menu(manga.chapters, selected)
        elif choice == "6":
            change_language(manga)
            return  # Reload
        elif choice.lower() == "d":
            if not selected:
                console.print("[warning]No chapters selected.[/]")
                continue
            start_download(manga, selected)
            return
        elif choice.lower() in ("b", "q", "back"):
            return


def show_chapter_list(chapters: list, selected: set):
    """Display paginated chapter list with selection status."""
    console.print()
    page_size = 30
    total_pages = max(1, (len(chapters) + page_size - 1) // page_size)
    current_page = 0

    while True:
        start = current_page * page_size
        end = min(start + page_size, len(chapters))
        page_chapters = chapters[start:end]

        table = Table(
            title=f"Chapters (Page {current_page + 1}/{total_pages})",
            box=box.ROUNDED,
            border_style="dim bright_black",
            header_style="bold bright_white",
            expand=True,
            padding=(0, 1),
        )
        table.add_column("", width=3, justify="center")
        table.add_column("#", style="ch_number", width=8)
        table.add_column("Title", style="ch_title", ratio=4)
        table.add_column("Vol", style="muted", width=8)
        table.add_column("Pages", style="muted", width=6, justify="right")

        for i, ch in enumerate(page_chapters):
            idx = start + i
            is_sel = idx in selected
            check = "[selected]+[/]" if is_sel else "[deselected]-[/]"
            row_style = "" if is_sel else "dim"

            table.add_row(
                check,
                f"Ch. {ch.number}",
                escape(ch.title[:50]),
                f"V.{ch.volume}" if ch.volume else "",
                str(ch.page_count) if ch.page_count else "",
                style=row_style,
            )

        console.print(table)
        console.print()

        nav_parts = []
        if current_page > 0:
            nav_parts.append("[menu_key][p][/] prev")
        if current_page < total_pages - 1:
            nav_parts.append("[menu_key][n][/] next")
        nav_parts.append("[menu_key][b][/] back")
        console.print("  " + "  |  ".join(nav_parts))

        action = Prompt.ask("[accent]Navigate[/]", default="b")
        if action.lower() == "n" and current_page < total_pages - 1:
            current_page += 1
        elif action.lower() == "p" and current_page > 0:
            current_page -= 1
        elif action.lower() in ("b", "q", "back"):
            return


def show_volume_list(chapters: list, volumes: dict, selected: set):
    """Display volumes with chapter counts and selection status."""
    console.print()

    sorted_vols = sorted(
        volumes.keys(),
        key=lambda v: (v == "No Volume", float(v) if v != "No Volume" and v.replace(".", "").isdigit() else 9999)
    )

    tree = Tree(
        gradient_text("Volumes", GRADIENT_BLUE),
        guide_style="dim bright_black",
    )

    for vol_name in sorted_vols:
        ch_indices = []
        for i, ch in enumerate(chapters):
            v = ch.volume or "No Volume"
            if v == vol_name:
                ch_indices.append(i)

        sel_in_vol = sum(1 for i in ch_indices if i in selected)
        total_in_vol = len(ch_indices)

        if sel_in_vol == total_in_vol:
            vol_check = "[selected]+[/]"
        elif sel_in_vol > 0:
            vol_check = "[warning]~[/]"
        else:
            vol_check = "[deselected]-[/]"

        vol_label = vol_name if vol_name != "No Volume" else "Unassigned"
        pct = sel_in_vol / total_in_vol * 100 if total_in_vol else 0
        bar = gradient_bar(pct, width=15, colors=GRADIENT_GREEN)

        vol_text = Text()
        vol_text.append(f"{vol_check} ")
        vol_text.append(f"Volume {vol_label}", style="vol_header")
        vol_text.append(f"  {sel_in_vol}/{total_in_vol} ch.  ", style="muted")
        vol_text.append(bar)

        branch = tree.add(vol_text)

        # Show first/last chapter in volume
        if ch_indices:
            first_ch = chapters[ch_indices[0]]
            last_ch = chapters[ch_indices[-1]]
            branch.add(
                f"[muted]Ch. {first_ch.number} - {last_ch.number}[/]"
            )

    console.print(tree)
    console.print()
    Prompt.ask("[muted]Press Enter to go back[/]", default="")


def select_chapters_interactive(chapters: list, selected: set) -> set:
    """Let user select chapters by range or comma-separated list."""
    console.print()
    console.print("[accent]Chapter Selection[/]")
    console.print("[muted]Enter a range or list. Examples:[/]")
    console.print("[muted]  1-50       Chapters 1 through 50[/]")
    console.print("[muted]  1,5,10-20  Chapters 1, 5, and 10-20[/]")
    console.print("[muted]  all        Select all[/]")
    console.print("[muted]  none       Deselect all[/]")
    console.print()

    if chapters:
        console.print(
            f"[muted]Available: Ch. {chapters[0].number} to Ch. {chapters[-1].number}[/]"
        )

    choice = Prompt.ask("[accent]Selection[/]", default="all")

    if choice.lower() == "all":
        return set(range(len(chapters)))
    elif choice.lower() == "none":
        return set()

    new_selected = set()
    for part in choice.split(","):
        part = part.strip()
        if "-" in part:
            try:
                a, b = part.split("-", 1)
                start = float(a.strip())
                end = float(b.strip())
                for i, ch in enumerate(chapters):
                    try:
                        num = float(ch.number)
                        if start <= num <= end:
                            new_selected.add(i)
                    except ValueError:
                        pass
            except ValueError:
                console.print(f"[warning]Invalid range: {part}[/]")
        else:
            for i, ch in enumerate(chapters):
                if ch.number == part:
                    new_selected.add(i)

    console.print(f"[success]{len(new_selected)} chapter(s) selected[/]")
    return new_selected


def select_volumes_interactive(chapters: list, volumes: dict, selected: set) -> set:
    """Select/deselect by volume."""
    console.print()
    console.print("[accent]Volume Selection[/]")

    sorted_vols = sorted(
        volumes.keys(),
        key=lambda v: (v == "No Volume", float(v) if v != "No Volume" and v.replace(".", "").isdigit() else 9999)
    )

    for i, vol in enumerate(sorted_vols, 1):
        count = sum(1 for ch in chapters if (ch.volume or "No Volume") == vol)
        label = vol if vol != "No Volume" else "Unassigned"
        console.print(f"  [menu_key]{i:3d}[/]  Volume {label} ({count} ch.)")

    console.print()
    console.print("[muted]Enter volume numbers (e.g. 1-5 or 1,3,5) or 'all'/'none'[/]")
    choice = Prompt.ask("[accent]Volumes[/]", default="all")

    if choice.lower() == "all":
        return set(range(len(chapters)))
    elif choice.lower() == "none":
        return set()

    # Parse selection
    target_vols = set()
    for part in choice.split(","):
        part = part.strip()
        if "-" in part:
            try:
                a, b = part.split("-", 1)
                for idx in range(int(a), int(b) + 1):
                    if 1 <= idx <= len(sorted_vols):
                        target_vols.add(sorted_vols[idx - 1])
            except ValueError:
                pass
        else:
            try:
                idx = int(part)
                if 1 <= idx <= len(sorted_vols):
                    target_vols.add(sorted_vols[idx - 1])
            except ValueError:
                pass

    new_selected = set()
    for i, ch in enumerate(chapters):
        v = ch.volume or "No Volume"
        if v in target_vols:
            new_selected.add(i)

    console.print(f"[success]{len(new_selected)} chapter(s) selected from {len(target_vols)} volume(s)[/]")
    return new_selected


def bulk_select_menu(chapters: list, selected: set) -> set:
    """Select all, none, or invert."""
    console.print()
    menu = Table(show_header=False, box=None, padding=(0, 2))
    menu.add_column(style="menu_key", width=4)
    menu.add_column(style="menu_desc")
    menu.add_row("[1]", "Select all")
    menu.add_row("[2]", "Select none")
    menu.add_row("[3]", "Invert selection")
    menu.add_row("[b]", "Back")
    console.print(menu)

    choice = Prompt.ask("[accent]Choice[/]", default="b")
    if choice == "1":
        console.print(f"[success]All {len(chapters)} chapters selected[/]")
        return set(range(len(chapters)))
    elif choice == "2":
        console.print("[warning]All chapters deselected[/]")
        return set()
    elif choice == "3":
        inverted = set(range(len(chapters))) - selected
        console.print(f"[success]Inverted: {len(inverted)} chapters selected[/]")
        return inverted
    return selected


def change_language(manga: MangaInfo):
    """Change language and reload."""
    langs = manga.available_languages or []
    lang_codes = []
    for l in langs:
        if isinstance(l, dict):
            lang_codes.append(l.get("code", "en"))
        else:
            lang_codes.append(l)

    if not lang_codes:
        lang_codes = ["en"]

    console.print()
    console.print("[accent]Available languages:[/]")
    for i, code in enumerate(lang_codes, 1):
        marker = " [selected]<< current[/]" if code == state.settings["language"] else ""
        console.print(f"  [menu_key]{i:3d}[/]  {code}{marker}")

    console.print()
    choice = Prompt.ask("[accent]Language[/]", default=state.settings["language"])

    # Accept either index or code
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(lang_codes):
            choice = lang_codes[idx]
    except ValueError:
        pass

    if choice in lang_codes:
        state.settings["language"] = choice
        console.print(f"[success]Language set to: {choice}[/]")
        console.print("[muted]Reloading chapters...[/]")
        view_manga(manga.url, state.source_key)
    else:
        console.print(f"[warning]Unknown language: {choice}[/]")


# --- Download ---
def start_download(manga: MangaInfo, selected: set):
    """Configure and start a download."""
    console.print()
    console.print(Rule(gradient_text(" Download ", GRADIENT_GREEN), style="separator"))
    console.print()

    # Format
    fmt = Prompt.ask(
        "[accent]Format[/]",
        choices=["cbz", "pdf", "epub", "images"],
        default=state.settings["format"],
    )

    # Mode
    mode = Prompt.ask(
        "[accent]Mode[/]",
        choices=["chapter", "volume", "all"],
        default=state.settings["mode"],
    )

    chapters = [manga.chapters[i] for i in sorted(selected)]

    console.print()
    console.print(f"  [info_label]Title:[/]    {manga.title}")
    console.print(f"  [info_label]Chapters:[/] {len(chapters)}")
    console.print(f"  [info_label]Format:[/]   {fmt}")
    console.print(f"  [info_label]Mode:[/]     {mode}")
    console.print(f"  [info_label]Output:[/]   {config.DOWNLOAD_DIR}")
    console.print()

    if not Confirm.ask("[accent]Start download?[/]", default=True):
        return

    console.print()

    task_id = state.engine.create_task(
        manga=manga,
        chapters=chapters,
        format_type=fmt,
        mode=mode,
        source=state.source,
    )

    monitor_download(task_id)


def monitor_download(task_id: str):
    """Live-updating download progress display."""
    console.print()

    with Live(console=console, refresh_per_second=4) as live:
        while True:
            task = state.engine.get_task(task_id)
            if not task:
                break

            # Build display
            layout = Table.grid(padding=(0, 0))
            layout.add_column()

            # Title
            title_text = Text()
            title_text.append("  Downloading: ", style="info_label")
            title_text.append(task.manga.title[:50], style="bold bright_white")
            layout.add_row(title_text)

            # Status
            status_style = {
                "running": "accent",
                "completed": "success",
                "error": "error",
                "cancelled": "warning",
                "queued": "muted",
            }.get(task.status, "muted")

            status_text = Text()
            status_text.append("  Status: ", style="info_label")
            status_text.append(task.status.upper(), style=status_style)
            status_text.append(f"  |  {task.format_type}/{task.mode}", style="muted")
            layout.add_row(status_text)

            # Current chapter
            if task.current_chapter:
                ch_text = Text()
                ch_text.append("  Current: ", style="info_label")
                ch_text.append(task.current_chapter[:60], style="ch_title")
                layout.add_row(ch_text)

            # Progress bar
            progress = task.progress or 0
            if task.status == "completed":
                colors = GRADIENT_GREEN
            elif task.status == "error":
                colors = GRADIENT_FIRE
            elif progress > 60:
                colors = GRADIENT_BLUE
            else:
                colors = GRADIENT_PURPLE

            bar_text = Text()
            bar_text.append("  ")
            bar_text.append(gradient_bar(progress, width=50, colors=colors))
            bar_text.append(f"  {progress:5.1f}%", style="bold bright_white")
            layout.add_row(bar_text)

            # Stats
            speed = format_bytes(int(task.speed)) + "/s" if task.speed else "-- B/s"
            downloaded = format_bytes(int(task.downloaded_bytes))
            ch_progress = f"{task.completed_chapters}/{task.total_chapters}"

            stats_text = Text()
            stats_text.append("  Chapters: ", style="info_label")
            stats_text.append(ch_progress, style="info_value")
            stats_text.append("  |  Speed: ", style="info_label")
            stats_text.append(speed, style="info_value")
            stats_text.append("  |  Downloaded: ", style="info_label")
            stats_text.append(downloaded, style="info_value")
            layout.add_row(stats_text)

            # Errors
            if task.errors:
                for err in task.errors[-2:]:
                    err_text = Text()
                    err_text.append("  Error: ", style="error")
                    err_text.append(err[:80], style="dim red")
                    layout.add_row(err_text)

            # Empty line
            layout.add_row(Text(""))

            panel = Panel(
                layout,
                border_style="bright_blue" if task.status == "running" else
                             "bright_green" if task.status == "completed" else
                             "bright_red" if task.status == "error" else "dim",
                box=box.ROUNDED,
            )

            live.update(panel)

            if task.status in ("completed", "error", "cancelled"):
                time.sleep(0.5)
                break

            time.sleep(0.25)

    # Final summary
    task = state.engine.get_task(task_id)
    if task:
        console.print()
        if task.status == "completed":
            console.print(
                Panel(
                    f"[success]Download completed![/]\n"
                    f"[muted]Total: {format_bytes(int(task.downloaded_bytes))}[/]\n"
                    f"[muted]Files:[/]\n" +
                    "\n".join(f"  [dim]{p}[/]" for p in task.output_paths),
                    border_style="bright_green",
                    box=box.ROUNDED,
                )
            )
        elif task.status == "error":
            console.print("[error]Download finished with errors.[/]")
            for err in task.errors:
                console.print(f"  [dim red]{err}[/]")
        elif task.status == "cancelled":
            console.print("[warning]Download was cancelled.[/]")

    console.print()
    Prompt.ask("[muted]Press Enter to continue[/]", default="")


# --- View Downloads ---
def cmd_downloads():
    console.print()
    console.print("[title]Downloads[/]")
    console.print()

    tasks = state.engine.get_all_tasks()
    if not tasks:
        console.print("[muted]No downloads.[/]")
        console.print()
        Prompt.ask("[muted]Press Enter to go back[/]", default="")
        return

    table = Table(
        box=box.ROUNDED,
        border_style="dim bright_black",
        header_style="bold bright_white",
        expand=True,
        padding=(0, 1),
    )
    table.add_column("#", width=3, justify="right", style="accent")
    table.add_column("Title", ratio=3)
    table.add_column("Status", width=12)
    table.add_column("Progress", width=20)
    table.add_column("Ch.", width=8, justify="center")
    table.add_column("Format", width=10, style="muted")

    for i, task in enumerate(tasks, 1):
        status_style = {
            "running": "accent",
            "completed": "success",
            "error": "error",
            "cancelled": "warning",
            "queued": "muted",
        }.get(task.status, "muted")

        progress = task.progress or 0
        if task.status == "completed":
            bar = gradient_bar(100, width=15, colors=GRADIENT_GREEN)
        elif task.status == "error":
            bar = gradient_bar(progress, width=15, colors=GRADIENT_FIRE)
        else:
            bar = gradient_bar(progress, width=15, colors=GRADIENT_BLUE)

        progress_cell = Text()
        progress_cell.append(bar)
        progress_cell.append(f" {progress:.0f}%", style="muted")

        table.add_row(
            str(i),
            escape(task.manga.title[:35]),
            f"[{status_style}]{task.status}[/]",
            progress_cell,
            f"{task.completed_chapters}/{task.total_chapters}",
            f"{task.format_type}/{task.mode}",
        )

    console.print(table)
    console.print()

    # Actions
    menu = Table(show_header=False, box=None, padding=(0, 2))
    menu.add_column(style="menu_key", width=4)
    menu.add_column(style="menu_desc")
    menu.add_row("[c]", "Cancel a download")
    menu.add_row("[x]", "Clear completed")
    menu.add_row("[b]", "Back")
    console.print(menu)

    choice = Prompt.ask("[accent]Action[/]", default="b")

    if choice.lower() == "c":
        idx = Prompt.ask("[accent]Download # to cancel[/]", default="")
        try:
            i = int(idx) - 1
            if 0 <= i < len(tasks):
                state.engine.cancel_task(tasks[i].task_id)
                console.print("[warning]Cancelled.[/]")
        except ValueError:
            pass
    elif choice.lower() == "x":
        to_remove = [
            tid for tid, t in state.engine.tasks.items()
            if t.status in ("completed", "error", "cancelled")
        ]
        for tid in to_remove:
            del state.engine.tasks[tid]
        console.print(f"[success]Cleared {len(to_remove)} task(s).[/]")


# --- Library ---
def cmd_library():
    console.print()
    console.print("[title]Library[/]")
    console.print(f"[subtitle]{config.DOWNLOAD_DIR}[/]")
    console.print()

    if not os.path.exists(config.DOWNLOAD_DIR):
        console.print("[muted]Download directory is empty.[/]")
        Prompt.ask("[muted]Press Enter[/]", default="")
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
        console.print("[muted]Library is empty.[/]")
        Prompt.ask("[muted]Press Enter[/]", default="")
        return

    files.sort(key=lambda f: f[0])

    table = Table(
        box=box.ROUNDED,
        border_style="dim bright_black",
        header_style="bold bright_white",
        expand=True,
        padding=(0, 1),
    )
    table.add_column("File", ratio=5)
    table.add_column("Size", width=12, justify="right", style="muted")
    table.add_column("Type", width=8, style="accent")

    ext_styles = {
        ".cbz": "bright_yellow",
        ".pdf": "bright_red",
        ".epub": "bright_green",
        ".jpg": "bright_cyan",
        ".png": "bright_cyan",
    }

    total_size = 0
    for name, size in files:
        total_size += size
        ext = os.path.splitext(name)[1].lower()
        ext_style = ext_styles.get(ext, "muted")
        table.add_row(
            escape(name),
            format_bytes(size),
            f"[{ext_style}]{ext}[/]",
        )

    console.print(table)
    console.print()
    console.print(
        f"  [info_label]Total:[/] {len(files)} files, {format_bytes(total_size)}"
    )
    console.print()
    Prompt.ask("[muted]Press Enter to go back[/]", default="")


# --- Sources ---
def cmd_sources():
    console.print()
    console.print("[title]Supported Sources[/]")
    console.print()

    table = Table(
        box=box.ROUNDED,
        border_style="dim bright_black",
        header_style="bold bright_white",
        padding=(0, 2),
    )
    table.add_column("Key", style="accent", width=16)
    table.add_column("Name", width=16)
    table.add_column("Base URL", style="muted", ratio=2)
    table.add_column("Languages", width=14)

    for key, cls in SOURCES.items():
        src = cls()
        sty = source_style(key)
        multi = "Multi" if key in ("mangadex",) else "English"
        table.add_row(
            f"[{sty}]{key}[/]",
            src.name,
            src.base_url,
            multi,
        )

    console.print(table)
    console.print()
    Prompt.ask("[muted]Press Enter to go back[/]", default="")


# --- Settings ---
def cmd_settings():
    console.print()
    console.print("[title]Settings[/]")
    console.print()

    while True:
        table = Table(
            box=box.ROUNDED,
            border_style="dim bright_black",
            header_style="bold bright_white",
            padding=(0, 2),
        )
        table.add_column("#", width=3, style="menu_key")
        table.add_column("Setting", width=20)
        table.add_column("Value", style="accent", width=15)
        table.add_column("Description", style="muted")

        table.add_row("1", "Threads", str(config.MAX_WORKERS), "Concurrent page downloads")
        table.add_row("2", "Format", state.settings["format"], "Default export format")
        table.add_row("3", "Mode", state.settings["mode"], "Default download mode")
        table.add_row("4", "Language", state.settings["language"], "Default language")
        table.add_row("5", "Output dir", config.DOWNLOAD_DIR[:30], "Download location")

        console.print(table)
        console.print()

        choice = Prompt.ask("[accent]Setting # to change (or 'b' to go back)[/]", default="b")

        if choice.lower() in ("b", "back", "q"):
            return
        elif choice == "1":
            val = Prompt.ask("[accent]Threads[/]", default=str(config.MAX_WORKERS),
                             choices=["2", "4", "6", "8", "12", "16"])
            config.MAX_WORKERS = int(val)
        elif choice == "2":
            val = Prompt.ask("[accent]Format[/]", default=state.settings["format"],
                             choices=["cbz", "pdf", "epub", "images"])
            state.settings["format"] = val
        elif choice == "3":
            val = Prompt.ask("[accent]Mode[/]", default=state.settings["mode"],
                             choices=["chapter", "volume", "all"])
            state.settings["mode"] = val
        elif choice == "4":
            val = Prompt.ask("[accent]Language code[/]", default=state.settings["language"])
            state.settings["language"] = val.strip()
        elif choice == "5":
            val = Prompt.ask("[accent]Output directory[/]", default=config.DOWNLOAD_DIR)
            if val.strip():
                config.DOWNLOAD_DIR = val.strip()
                os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)

        console.print()


# --- Main Loop ---
def main():
    print_banner()

    while True:
        print_main_menu()

        try:
            choice = Prompt.ask("[accent]>[/]", default="q")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[muted]Goodbye.[/]")
            break

        if choice == "1":
            cmd_search()
        elif choice == "2":
            cmd_url()
        elif choice == "3":
            cmd_downloads()
        elif choice == "4":
            cmd_library()
        elif choice == "5":
            cmd_sources()
        elif choice == "6":
            cmd_settings()
        elif choice.lower() in ("q", "quit", "exit"):
            console.print("[muted]Goodbye.[/]")
            break
        else:
            console.print("[warning]Unknown option. Enter 1-6 or q.[/]")


if __name__ == "__main__":
    main()