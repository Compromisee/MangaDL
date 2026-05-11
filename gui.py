"""
MangaDL - Desktop GUI (Tkinter)
Standalone desktop app, no browser needed.
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

import config
from sources import detect_source, SOURCES
from sources.base import MangaInfo, Chapter
from downloader.engine import DownloadEngine
from exporters import get_exporter


# --- App State ---
class AppState:
    def __init__(self):
        self.manga: Optional[MangaInfo] = None
        self.chapters: list = []
        self.volumes: dict = {}
        self.engine = DownloadEngine()
        self.source = None
        self.source_key = ""
        self.language = "en"


state = AppState()


# --- Helpers ---
def format_bytes(b: int) -> str:
    if not b:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


def safe_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in " -_.()" else "_" for c in name).strip()


def build_volumes(chapters: list) -> dict:
    vols = {}
    for i, ch in enumerate(chapters):
        v = ch.volume or "No Volume"
        vols.setdefault(v, []).append(i)
    return vols


# --- Main Window ---
class MangaDLApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MangaDL")
        self.geometry("1000x700")
        self.minsize(800, 550)
        self.configure(bg="#111")

        # Style setup
        self.style = ttk.Style(self)
        self._setup_styles()

        # Layout
        self._build_sidebar()
        self._build_main_area()

        # Frames
        self.frames = {}
        self._build_search_frame()
        self._build_url_frame()
        self._build_manga_frame()
        self._build_downloads_frame()
        self._build_settings_frame()

        self._show_frame("search")
        self._poll_downloads()

    # --- Styles ---
    def _setup_styles(self):
        self.style.theme_use("clam")

        bg = "#111"
        bg2 = "#1a1a1a"
        bg3 = "#222"
        fg = "#e8e8e8"
        fg2 = "#999"
        accent = "#4f8ff7"
        border = "#2a2a2a"

        self.style.configure(".", background=bg, foreground=fg, borderwidth=0,
                             font=("Segoe UI", 10))
        self.style.configure("TFrame", background=bg)
        self.style.configure("Dark.TFrame", background=bg2)
        self.style.configure("Card.TFrame", background=bg3)

        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("Dark.TLabel", background=bg2, foreground=fg)
        self.style.configure("Dim.TLabel", background=bg, foreground=fg2, font=("Segoe UI", 9))
        self.style.configure("Title.TLabel", background=bg, foreground=fg, font=("Segoe UI", 14, "bold"))
        self.style.configure("Subtitle.TLabel", background=bg, foreground=fg2, font=("Segoe UI", 10))
        self.style.configure("Card.TLabel", background=bg3, foreground=fg)
        self.style.configure("CardDim.TLabel", background=bg3, foreground=fg2, font=("Segoe UI", 9))

        self.style.configure("TButton", background=bg3, foreground=fg, padding=(12, 6),
                             font=("Segoe UI", 9))
        self.style.map("TButton",
                       background=[("active", "#333"), ("pressed", "#444")],
                       foreground=[("disabled", "#555")])

        self.style.configure("Accent.TButton", background=accent, foreground="#fff",
                             padding=(16, 8), font=("Segoe UI", 10, "bold"))
        self.style.map("Accent.TButton",
                       background=[("active", "#3a7be0"), ("pressed", "#2a6bd0")])

        self.style.configure("Nav.TButton", background=bg2, foreground=fg2,
                             padding=(16, 10), font=("Segoe UI", 10), anchor="w")
        self.style.map("Nav.TButton",
                       background=[("active", "#2a2a2a")],
                       foreground=[("active", fg)])
        self.style.configure("NavActive.TButton", background="#1a2a40", foreground=accent,
                             padding=(16, 10), font=("Segoe UI", 10, "bold"), anchor="w")

        self.style.configure("TEntry", fieldbackground=bg3, foreground=fg, insertcolor=fg,
                             padding=8, font=("Segoe UI", 10))

        self.style.configure("TCombobox", fieldbackground=bg3, foreground=fg,
                             background=bg3, padding=6, font=("Segoe UI", 9))
        self.style.map("TCombobox", fieldbackground=[("readonly", bg3)])
        self.option_add("*TCombobox*Listbox.Background", bg3)
        self.option_add("*TCombobox*Listbox.Foreground", fg)
        self.option_add("*TCombobox*Listbox.selectBackground", accent)
        self.option_add("*TCombobox*Listbox.selectForeground", "#fff")

        self.style.configure("Horizontal.TProgressbar", troughcolor=bg3,
                             background=accent, thickness=6)

        self.style.configure("Treeview", background=bg2, foreground=fg,
                             fieldbackground=bg2, borderwidth=0, rowheight=28,
                             font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", background=bg3, foreground=fg2,
                             font=("Segoe UI", 9, "bold"))
        self.style.map("Treeview",
                       background=[("selected", "#1a2a40")],
                       foreground=[("selected", accent)])

        self.style.configure("TCheckbutton", background=bg, foreground=fg)
        self.style.map("TCheckbutton", background=[("active", bg)])

        self.style.configure("TLabelframe", background=bg, foreground=fg2)
        self.style.configure("TLabelframe.Label", background=bg, foreground=fg2,
                             font=("Segoe UI", 9, "bold"))

    # --- Sidebar ---
    def _build_sidebar(self):
        self.sidebar = ttk.Frame(self, style="Dark.TFrame", width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_frame = ttk.Frame(self.sidebar, style="Dark.TFrame")
        logo_frame.pack(fill="x", padx=16, pady=(20, 24))
        ttk.Label(logo_frame, text="MangaDL", style="Dark.TLabel",
                  font=("Segoe UI", 16, "bold")).pack(side="left")
        ttk.Label(logo_frame, text=" v2.0", style="Dark.TLabel",
                  font=("Segoe UI", 9), foreground="#555").pack(side="left", pady=(6, 0))

        # Nav buttons
        self.nav_buttons = {}
        nav_items = [
            ("search", "Search"),
            ("url", "URL Import"),
            ("downloads", "Downloads"),
            ("settings", "Settings"),
        ]
        for key, label in nav_items:
            btn = ttk.Button(self.sidebar, text=f"   {label}", style="Nav.TButton",
                             command=lambda k=key: self._show_frame(k))
            btn.pack(fill="x", padx=8, pady=1)
            self.nav_buttons[key] = btn

        # Bottom info
        ttk.Frame(self.sidebar, style="Dark.TFrame").pack(fill="both", expand=True)
        info = ttk.Label(self.sidebar, text=f"{len(SOURCES)} sources available",
                         style="Dark.TLabel", foreground="#555", font=("Segoe UI", 8))
        info.pack(side="bottom", padx=16, pady=12)

    def _show_frame(self, name: str):
        for key, btn in self.nav_buttons.items():
            btn.configure(style="NavActive.TButton" if key == name else "Nav.TButton")

        for frame_name, frame in self.frames.items():
            if frame_name == name:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    # --- Main Area ---
    def _build_main_area(self):
        self.main_area = ttk.Frame(self)
        self.main_area.pack(side="right", fill="both", expand=True)

    # --- Search Frame ---
    def _build_search_frame(self):
        frame = ttk.Frame(self.main_area)
        self.frames["search"] = frame

        # Top bar
        top = ttk.Frame(frame)
        top.pack(fill="x", padx=24, pady=(24, 16))

        ttk.Label(top, text="Search", style="Title.TLabel").pack(anchor="w")
        ttk.Label(top, text="Find manga, manhwa, and webtoons across all sources",
                  style="Dim.TLabel").pack(anchor="w", pady=(2, 0))

        # Search bar
        search_bar = ttk.Frame(frame)
        search_bar.pack(fill="x", padx=24, pady=(0, 16))

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_bar, textvariable=self.search_var, font=("Segoe UI", 11))
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.search_entry.bind("<Return>", lambda e: self._do_search())

        self.search_source_var = tk.StringVar(value="all")
        source_combo = ttk.Combobox(search_bar, textvariable=self.search_source_var,
                                    values=["all"] + list(SOURCES.keys()),
                                    state="readonly", width=14)
        source_combo.pack(side="left", padx=(8, 0))

        ttk.Button(search_bar, text="Search", style="Accent.TButton",
                   command=self._do_search).pack(side="left", padx=(8, 0))

        # Results tree
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        cols = ("title", "author", "source", "status")
        self.search_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        self.search_tree.heading("title", text="Title")
        self.search_tree.heading("author", text="Author")
        self.search_tree.heading("source", text="Source")
        self.search_tree.heading("status", text="Status")
        self.search_tree.column("title", width=350, minwidth=200)
        self.search_tree.column("author", width=150, minwidth=100)
        self.search_tree.column("source", width=100, minwidth=80)
        self.search_tree.column("status", width=80, minwidth=60)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.search_tree.yview)
        self.search_tree.configure(yscrollcommand=scrollbar.set)
        self.search_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.search_tree.bind("<Double-1>", self._on_search_select)

        # Status
        self.search_status = ttk.Label(frame, text="", style="Dim.TLabel")
        self.search_status.pack(padx=24, pady=(0, 8), anchor="w")

        self.search_results_data = []

    def _do_search(self):
        query = self.search_var.get().strip()
        if not query:
            return

        self.search_status.configure(text="Searching...")
        self.search_tree.delete(*self.search_tree.get_children())
        self.search_results_data = []

        def worker():
            results = []
            source_key = self.search_source_var.get()

            def search_one(key, src):
                try:
                    found = src.search(query)
                    for m in found:
                        results.append((key, m))
                except Exception:
                    pass

            if source_key == "all":
                threads = []
                for key, cls in SOURCES.items():
                    t = threading.Thread(target=search_one, args=(key, cls()))
                    t.start()
                    threads.append(t)
                for t in threads:
                    t.join(timeout=30)
            else:
                if source_key in SOURCES:
                    search_one(source_key, SOURCES[source_key]())

            self.after(0, lambda: self._populate_search(results))

        threading.Thread(target=worker, daemon=True).start()

    def _populate_search(self, results: list):
        self.search_results_data = results
        self.search_tree.delete(*self.search_tree.get_children())

        for i, (key, manga) in enumerate(results):
            self.search_tree.insert("", "end", iid=str(i), values=(
                manga.title,
                manga.author or "Unknown",
                manga.source,
                manga.status or "",
            ))

        self.search_status.configure(text=f"{len(results)} result(s) found")

    def _on_search_select(self, event):
        sel = self.search_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        key, manga = self.search_results_data[idx]
        self._load_manga(manga.url, key)

    # --- URL Import Frame ---
    def _build_url_frame(self):
        frame = ttk.Frame(self.main_area)
        self.frames["url"] = frame

        top = ttk.Frame(frame)
        top.pack(fill="x", padx=24, pady=(24, 16))
        ttk.Label(top, text="URL Import", style="Title.TLabel").pack(anchor="w")
        ttk.Label(top, text="Paste a manga URL from any supported source",
                  style="Dim.TLabel").pack(anchor="w", pady=(2, 0))

        bar = ttk.Frame(frame)
        bar.pack(fill="x", padx=24, pady=(0, 16))

        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(bar, textvariable=self.url_var, font=("Segoe UI", 11))
        url_entry.pack(side="left", fill="x", expand=True, ipady=4)
        url_entry.bind("<Return>", lambda e: self._do_url_fetch())

        ttk.Button(bar, text="Fetch", style="Accent.TButton",
                   command=self._do_url_fetch).pack(side="left", padx=(8, 0))

        self.url_status = ttk.Label(frame, text="", style="Dim.TLabel")
        self.url_status.pack(padx=24, anchor="w")

        # Supported sources
        sources_label = ttk.Label(frame,
                                  text="Supported: " + ", ".join(SOURCES.keys()),
                                  style="Dim.TLabel")
        sources_label.pack(padx=24, pady=(16, 0), anchor="w")

    def _do_url_fetch(self):
        url = self.url_var.get().strip()
        if not url:
            return
        source_key, src = detect_source(url)
        if not src:
            messagebox.showerror("Error", "Could not detect source for this URL.")
            return
        self._load_manga(url, source_key)

    # --- Load Manga Info ---
    def _load_manga(self, url: str, source_key: str):
        self._show_frame("manga")
        self.manga_status.configure(text="Loading manga info...")
        self.chapter_tree.delete(*self.chapter_tree.get_children())
        self.manga_title_label.configure(text="Loading...")
        self.manga_info_label.configure(text="")

        def worker():
            try:
                src = SOURCES[source_key]()
                lang = state.language
                manga = src.get_manga_info(url, language=lang)
                state.manga = manga
                state.chapters = manga.chapters
                state.volumes = build_volumes(manga.chapters)
                state.source = src
                state.source_key = source_key
                self.after(0, lambda: self._populate_manga(manga))
            except Exception as e:
                self.after(0, lambda: self._manga_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _manga_error(self, msg: str):
        self.manga_status.configure(text=f"Error: {msg}")
        self.manga_title_label.configure(text="Error loading manga")

    def _populate_manga(self, manga: MangaInfo):
        self.manga_title_label.configure(text=manga.title)

        vol_count = len([k for k in state.volumes if k != "No Volume"])
        info_parts = [
            f"Author: {manga.author or 'Unknown'}",
            f"Status: {manga.status or 'Unknown'}",
            f"Source: {manga.source}",
            f"Chapters: {len(manga.chapters)}",
            f"Volumes: {vol_count}",
        ]
        self.manga_info_label.configure(text="  |  ".join(info_parts))

        # Language selector
        langs = manga.available_languages or ["en"]
        lang_values = []
        for l in langs:
            if isinstance(l, dict):
                lang_values.append(l.get("code", "en"))
            else:
                lang_values.append(l)
        self.lang_combo.configure(values=lang_values)
        if state.language in lang_values:
            self.lang_var.set(state.language)
        elif lang_values:
            self.lang_var.set(lang_values[0])

        self._refresh_chapter_tree()
        self.manga_status.configure(
            text=f"{len(manga.chapters)} chapters loaded  |  {vol_count} volumes"
        )

    def _refresh_chapter_tree(self):
        self.chapter_tree.delete(*self.chapter_tree.get_children())
        self.chapter_check_vars.clear()

        view = self.view_var.get()

        if view == "Chapters":
            for i, ch in enumerate(state.chapters):
                var = tk.BooleanVar(value=True)
                self.chapter_check_vars[i] = var
                self.chapter_tree.insert("", "end", iid=str(i), values=(
                    "  +  ",
                    f"Ch. {ch.number}",
                    ch.title,
                    f"Vol. {ch.volume}" if ch.volume else "",
                ), tags=("checked",))
        else:
            # Volume view
            sorted_vols = sorted(state.volumes.keys(),
                                 key=lambda v: (v == "No Volume", float(v) if v != "No Volume" and v.replace(".", "").isdigit() else 999))
            for vol_name in sorted_vols:
                indices = state.volumes[vol_name]
                display = f"Volume {vol_name}" if vol_name != "No Volume" else "No Volume (Unassigned)"
                vol_id = f"vol_{vol_name}"
                self.chapter_tree.insert("", "end", iid=vol_id, values=(
                    "  +  ",
                    display,
                    f"{len(indices)} chapters",
                    "",
                ), tags=("volume",))

                var = tk.BooleanVar(value=True)
                self.chapter_check_vars[vol_id] = var

                for idx in indices:
                    ch = state.chapters[idx]
                    ch_iid = f"vol_{vol_name}_ch_{idx}"
                    child_var = tk.BooleanVar(value=True)
                    self.chapter_check_vars[ch_iid] = child_var
                    self.chapter_tree.insert(vol_id, "end", iid=ch_iid, values=(
                        "  +  ",
                        f"  Ch. {ch.number}",
                        ch.title,
                        "",
                    ), tags=("checked",))

        self.chapter_tree.tag_configure("checked", foreground="#e8e8e8")
        self.chapter_tree.tag_configure("unchecked", foreground="#555")
        self.chapter_tree.tag_configure("volume", foreground="#4f8ff7",
                                        font=("Segoe UI", 10, "bold"))

    # --- Manga Detail Frame ---
    def _build_manga_frame(self):
        frame = ttk.Frame(self.main_area)
        self.frames["manga"] = frame

        # Title bar
        title_bar = ttk.Frame(frame)
        title_bar.pack(fill="x", padx=24, pady=(20, 4))

        ttk.Button(title_bar, text="< Back", command=lambda: self._show_frame("search")).pack(side="left")

        self.manga_title_label = ttk.Label(title_bar, text="", style="Title.TLabel")
        self.manga_title_label.pack(side="left", padx=(16, 0))

        # Info row
        self.manga_info_label = ttk.Label(frame, text="", style="Dim.TLabel")
        self.manga_info_label.pack(fill="x", padx=24, pady=(0, 12))

        # Options bar
        opts = ttk.Frame(frame)
        opts.pack(fill="x", padx=24, pady=(0, 8))

        # Language
        ttk.Label(opts, text="Language:", style="Dim.TLabel").pack(side="left")
        self.lang_var = tk.StringVar(value="en")
        self.lang_combo = ttk.Combobox(opts, textvariable=self.lang_var,
                                       values=["en"], state="readonly", width=8)
        self.lang_combo.pack(side="left", padx=(4, 16))
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_lang_change)

        # View toggle
        ttk.Label(opts, text="View:", style="Dim.TLabel").pack(side="left")
        self.view_var = tk.StringVar(value="Chapters")
        view_combo = ttk.Combobox(opts, textvariable=self.view_var,
                                  values=["Chapters", "Volumes"], state="readonly", width=10)
        view_combo.pack(side="left", padx=(4, 16))
        view_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_chapter_tree())

        # Format
        ttk.Label(opts, text="Format:", style="Dim.TLabel").pack(side="left")
        self.format_var = tk.StringVar(value="cbz")
        fmt_combo = ttk.Combobox(opts, textvariable=self.format_var,
                                 values=["cbz", "pdf", "epub", "images"],
                                 state="readonly", width=8)
        fmt_combo.pack(side="left", padx=(4, 16))

        # Mode
        ttk.Label(opts, text="Mode:", style="Dim.TLabel").pack(side="left")
        self.mode_var = tk.StringVar(value="chapter")
        mode_combo = ttk.Combobox(opts, textvariable=self.mode_var,
                                  values=["chapter", "volume", "all"],
                                  state="readonly", width=10)
        mode_combo.pack(side="left", padx=(4, 0))

        # Action buttons
        btn_bar = ttk.Frame(frame)
        btn_bar.pack(fill="x", padx=24, pady=(0, 8))

        ttk.Button(btn_bar, text="Select All", command=self._select_all).pack(side="left", padx=(0, 4))
        ttk.Button(btn_bar, text="Select None", command=self._select_none).pack(side="left", padx=(0, 4))
        ttk.Button(btn_bar, text="Invert", command=self._invert_selection).pack(side="left", padx=(0, 4))

        # Range
        ttk.Label(btn_bar, text="   From:", style="Dim.TLabel").pack(side="left")
        self.range_from_var = tk.StringVar()
        ttk.Entry(btn_bar, textvariable=self.range_from_var, width=8).pack(side="left", padx=(4, 4))
        ttk.Label(btn_bar, text="To:", style="Dim.TLabel").pack(side="left")
        self.range_to_var = tk.StringVar()
        ttk.Entry(btn_bar, textvariable=self.range_to_var, width=8).pack(side="left", padx=(4, 4))
        ttk.Button(btn_bar, text="Apply Range", command=self._apply_range).pack(side="left", padx=(4, 0))

        # Download button
        ttk.Button(btn_bar, text="Download Selected", style="Accent.TButton",
                   command=self._start_download).pack(side="right")

        # Chapter tree
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        cols = ("check", "number", "title", "volume")
        self.chapter_tree = ttk.Treeview(tree_frame, columns=cols, show="tree headings",
                                         selectmode="extended")
        self.chapter_tree.heading("check", text="")
        self.chapter_tree.heading("number", text="Number")
        self.chapter_tree.heading("title", text="Title")
        self.chapter_tree.heading("volume", text="Volume")
        self.chapter_tree.column("#0", width=20, stretch=False)
        self.chapter_tree.column("check", width=40, stretch=False, anchor="center")
        self.chapter_tree.column("number", width=100, minwidth=60)
        self.chapter_tree.column("title", width=350, minwidth=150)
        self.chapter_tree.column("volume", width=100, minwidth=60)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.chapter_tree.yview)
        self.chapter_tree.configure(yscrollcommand=scrollbar.set)
        self.chapter_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.chapter_tree.bind("<Button-1>", self._on_chapter_click)

        self.chapter_check_vars = {}

        # Status
        self.manga_status = ttk.Label(frame, text="", style="Dim.TLabel")
        self.manga_status.pack(fill="x", padx=24, pady=(0, 12))

    def _on_lang_change(self, event):
        new_lang = self.lang_var.get()
        if new_lang == state.language:
            return
        state.language = new_lang
        if state.manga:
            self._load_manga(state.manga.url, state.source_key)

    def _on_chapter_click(self, event):
        region = self.chapter_tree.identify_region(event.x, event.y)
        if region not in ("cell", "tree"):
            return

        row_id = self.chapter_tree.identify_row(event.y)
        col = self.chapter_tree.identify_column(event.x)

        if not row_id:
            return

        # Toggle check on any click
        item = self.chapter_tree.item(row_id)
        current_check = item["values"][0] if item["values"] else ""
        new_check = "      " if current_check.strip() == "+" else "  +  "

        values = list(item["values"])
        values[0] = new_check
        self.chapter_tree.item(row_id, values=values)

        is_checked = new_check.strip() == "+"

        # If it's a volume header, toggle all children
        children = self.chapter_tree.get_children(row_id)
        if children:
            for child_id in children:
                child_item = self.chapter_tree.item(child_id)
                child_vals = list(child_item["values"])
                child_vals[0] = new_check
                self.chapter_tree.item(child_id, values=child_vals)
                self.chapter_tree.item(child_id,
                                       tags=("checked",) if is_checked else ("unchecked",))

        # Update tag for visual feedback
        tag = "checked" if is_checked else "unchecked"
        existing_tags = list(item.get("tags", ()))
        if "volume" in existing_tags:
            tag = "volume"
        self.chapter_tree.item(row_id, tags=(tag,))

    def _get_selected_indices(self) -> list:
        """Get chapter indices that are checked."""
        indices = []
        view = self.view_var.get()

        if view == "Chapters":
            for item_id in self.chapter_tree.get_children():
                item = self.chapter_tree.item(item_id)
                if item["values"] and str(item["values"][0]).strip() == "+":
                    try:
                        indices.append(int(item_id))
                    except ValueError:
                        pass
        else:
            # Volume view - collect from children
            for vol_id in self.chapter_tree.get_children():
                for child_id in self.chapter_tree.get_children(vol_id):
                    child_item = self.chapter_tree.item(child_id)
                    if child_item["values"] and str(child_item["values"][0]).strip() == "+":
                        # Extract index from iid like "vol_1_ch_5"
                        parts = child_id.split("_ch_")
                        if len(parts) == 2:
                            try:
                                indices.append(int(parts[1]))
                            except ValueError:
                                pass

        return sorted(set(indices))

    def _select_all(self):
        for item_id in self._all_tree_items():
            item = self.chapter_tree.item(item_id)
            values = list(item["values"])
            if values:
                values[0] = "  +  "
                self.chapter_tree.item(item_id, values=values, tags=("checked",))

    def _select_none(self):
        for item_id in self._all_tree_items():
            item = self.chapter_tree.item(item_id)
            values = list(item["values"])
            if values:
                values[0] = "      "
                tags = list(item.get("tags", ()))
                new_tag = "volume" if "volume" in tags else "unchecked"
                self.chapter_tree.item(item_id, values=values, tags=(new_tag,))

    def _invert_selection(self):
        for item_id in self._all_tree_items():
            item = self.chapter_tree.item(item_id)
            values = list(item["values"])
            if values:
                is_checked = str(values[0]).strip() == "+"
                values[0] = "      " if is_checked else "  +  "
                tags = list(item.get("tags", ()))
                if "volume" not in tags:
                    new_tag = "checked" if not is_checked else "unchecked"
                    self.chapter_tree.item(item_id, values=values, tags=(new_tag,))
                else:
                    self.chapter_tree.item(item_id, values=values)

    def _apply_range(self):
        try:
            r_from = float(self.range_from_var.get()) if self.range_from_var.get() else -float("inf")
            r_to = float(self.range_to_var.get()) if self.range_to_var.get() else float("inf")
        except ValueError:
            return

        view = self.view_var.get()

        if view == "Chapters":
            for item_id in self.chapter_tree.get_children():
                idx = int(item_id)
                ch = state.chapters[idx]
                try:
                    num = float(ch.number)
                except ValueError:
                    num = 0
                in_range = r_from <= num <= r_to
                item = self.chapter_tree.item(item_id)
                values = list(item["values"])
                values[0] = "  +  " if in_range else "      "
                tag = "checked" if in_range else "unchecked"
                self.chapter_tree.item(item_id, values=values, tags=(tag,))
        else:
            for vol_id in self.chapter_tree.get_children():
                vol_name = vol_id.replace("vol_", "")
                try:
                    vol_num = float(vol_name)
                except ValueError:
                    vol_num = -1

                in_range = r_from <= vol_num <= r_to
                item = self.chapter_tree.item(vol_id)
                values = list(item["values"])
                values[0] = "  +  " if in_range else "      "
                self.chapter_tree.item(vol_id, values=values, tags=("volume",))

                for child_id in self.chapter_tree.get_children(vol_id):
                    child_item = self.chapter_tree.item(child_id)
                    child_vals = list(child_item["values"])
                    child_vals[0] = "  +  " if in_range else "      "
                    tag = "checked" if in_range else "unchecked"
                    self.chapter_tree.item(child_id, values=child_vals, tags=(tag,))

    def _all_tree_items(self) -> list:
        """Get all item IDs in the tree, including children."""
        items = []
        for item_id in self.chapter_tree.get_children():
            items.append(item_id)
            for child_id in self.chapter_tree.get_children(item_id):
                items.append(child_id)
        return items

    # --- Start Download ---
    def _start_download(self):
        if not state.manga or not state.chapters:
            messagebox.showwarning("Warning", "No manga loaded.")
            return

        selected = self._get_selected_indices()
        if not selected:
            messagebox.showwarning("Warning", "No chapters selected.")
            return

        fmt = self.format_var.get()
        mode = self.mode_var.get()

        chapters = [state.chapters[i] for i in selected if i < len(state.chapters)]
        if not chapters:
            return

        task_id = state.engine.create_task(
            manga=state.manga,
            chapters=chapters,
            format_type=fmt,
            mode=mode,
            source=state.source,
        )

        self.manga_status.configure(
            text=f"Download started: {len(chapters)} chapter(s) as {fmt} ({mode} mode)"
        )
        self._show_frame("downloads")

    # --- Downloads Frame ---
    def _build_downloads_frame(self):
        frame = ttk.Frame(self.main_area)
        self.frames["downloads"] = frame

        top = ttk.Frame(frame)
        top.pack(fill="x", padx=24, pady=(24, 16))

        ttk.Label(top, text="Downloads", style="Title.TLabel").pack(side="left")
        ttk.Button(top, text="Clear Completed", command=self._clear_completed).pack(side="right")
        ttk.Button(top, text="Open Folder", command=self._open_dl_folder).pack(side="right", padx=(0, 8))

        # Downloads list
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        cols = ("title", "status", "progress", "chapters", "speed", "format")
        self.dl_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        self.dl_tree.heading("title", text="Title")
        self.dl_tree.heading("status", text="Status")
        self.dl_tree.heading("progress", text="Progress")
        self.dl_tree.heading("chapters", text="Chapters")
        self.dl_tree.heading("speed", text="Speed")
        self.dl_tree.heading("format", text="Format")
        self.dl_tree.column("title", width=250, minwidth=150)
        self.dl_tree.column("status", width=80, minwidth=60)
        self.dl_tree.column("progress", width=80, minwidth=60)
        self.dl_tree.column("chapters", width=80, minwidth=60)
        self.dl_tree.column("speed", width=80, minwidth=60)
        self.dl_tree.column("format", width=80, minwidth=60)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.dl_tree.yview)
        self.dl_tree.configure(yscrollcommand=scrollbar.set)
        self.dl_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Cancel button
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", padx=24, pady=(0, 4))
        ttk.Button(btn_frame, text="Cancel Selected", command=self._cancel_selected).pack(side="left")

        # Detail
        self.dl_detail = ttk.Label(frame, text="", style="Dim.TLabel")
        self.dl_detail.pack(fill="x", padx=24, pady=(0, 12))

    def _poll_downloads(self):
        """Refresh download list every second."""
        tasks = state.engine.get_all_tasks()

        existing = set(self.dl_tree.get_children())
        current_ids = set()

        for task in tasks:
            tid = task.task_id
            current_ids.add(tid)

            speed = format_bytes(int(task.speed)) + "/s" if task.speed else ""
            progress = f"{task.progress:.1f}%"
            chapters = f"{task.completed_chapters}/{task.total_chapters}"

            values = (
                task.manga.title[:40],
                task.status,
                progress,
                chapters,
                speed,
                f"{task.format_type}/{task.mode}",
            )

            if tid in existing:
                self.dl_tree.item(tid, values=values)
            else:
                self.dl_tree.insert("", "end", iid=tid, values=values)

        # Remove old items
        for old_id in existing - current_ids:
            self.dl_tree.delete(old_id)

        # Update detail for selected
        sel = self.dl_tree.selection()
        if sel:
            task = state.engine.get_task(sel[0])
            if task:
                detail = f"Current: {task.current_chapter}"
                if task.errors:
                    detail += f"  |  Last error: {task.errors[-1]}"
                detail += f"  |  Downloaded: {format_bytes(int(task.downloaded_bytes))}"
                self.dl_detail.configure(text=detail)

        self.after(1000, self._poll_downloads)

    def _cancel_selected(self):
        sel = self.dl_tree.selection()
        if sel:
            state.engine.cancel_task(sel[0])

    def _clear_completed(self):
        to_remove = [
            tid for tid, t in state.engine.tasks.items()
            if t.status in ("completed", "error", "cancelled")
        ]
        for tid in to_remove:
            del state.engine.tasks[tid]
            if self.dl_tree.exists(tid):
                self.dl_tree.delete(tid)

    def _open_dl_folder(self):
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

    # --- Settings Frame ---
    def _build_settings_frame(self):
        frame = ttk.Frame(self.main_area)
        self.frames["settings"] = frame

        top = ttk.Frame(frame)
        top.pack(fill="x", padx=24, pady=(24, 24))
        ttk.Label(top, text="Settings", style="Title.TLabel").pack(anchor="w")

        # Settings grid
        settings = ttk.Frame(frame)
        settings.pack(fill="x", padx=24)

        row = 0

        # Threads
        ttk.Label(settings, text="Download threads", style="TLabel").grid(
            row=row, column=0, sticky="w", pady=8)
        ttk.Label(settings, text="Concurrent page downloads per chapter",
                  style="Dim.TLabel").grid(row=row, column=1, sticky="w", padx=(24, 0), pady=8)
        self.threads_var = tk.StringVar(value=str(config.MAX_WORKERS))
        threads_combo = ttk.Combobox(settings, textvariable=self.threads_var,
                                     values=["2", "4", "6", "8", "12", "16"],
                                     state="readonly", width=6)
        threads_combo.grid(row=row, column=2, sticky="e", padx=(24, 0), pady=8)
        threads_combo.bind("<<ComboboxSelected>>", self._on_threads_change)
        row += 1

        # Default format
        ttk.Label(settings, text="Default format", style="TLabel").grid(
            row=row, column=0, sticky="w", pady=8)
        ttk.Label(settings, text="Default export format for new downloads",
                  style="Dim.TLabel").grid(row=row, column=1, sticky="w", padx=(24, 0), pady=8)
        self.default_format_var = tk.StringVar(value="cbz")
        fmt_combo = ttk.Combobox(settings, textvariable=self.default_format_var,
                                 values=["cbz", "pdf", "epub", "images"],
                                 state="readonly", width=8)
        fmt_combo.grid(row=row, column=2, sticky="e", padx=(24, 0), pady=8)
        row += 1

        # Default mode
        ttk.Label(settings, text="Default mode", style="TLabel").grid(
            row=row, column=0, sticky="w", pady=8)
        ttk.Label(settings, text="How chapters are organized by default",
                  style="Dim.TLabel").grid(row=row, column=1, sticky="w", padx=(24, 0), pady=8)
        self.default_mode_var = tk.StringVar(value="chapter")
        mode_combo = ttk.Combobox(settings, textvariable=self.default_mode_var,
                                  values=["chapter", "volume", "all"],
                                  state="readonly", width=10)
        mode_combo.grid(row=row, column=2, sticky="e", padx=(24, 0), pady=8)
        row += 1

        # Default language
        ttk.Label(settings, text="Default language", style="TLabel").grid(
            row=row, column=0, sticky="w", pady=8)
        ttk.Label(settings, text="Preferred chapter language",
                  style="Dim.TLabel").grid(row=row, column=1, sticky="w", padx=(24, 0), pady=8)
        self.default_lang_var = tk.StringVar(value="en")
        lang_entry = ttk.Entry(settings, textvariable=self.default_lang_var, width=8)
        lang_entry.grid(row=row, column=2, sticky="e", padx=(24, 0), pady=8)
        lang_entry.bind("<FocusOut>", self._on_default_lang_change)
        row += 1

        # Download dir
        ttk.Label(settings, text="Download directory", style="TLabel").grid(
            row=row, column=0, sticky="w", pady=8)
        self.dl_dir_label = ttk.Label(settings, text=config.DOWNLOAD_DIR,
                                      style="Dim.TLabel")
        self.dl_dir_label.grid(row=row, column=1, sticky="w", padx=(24, 0), pady=8)
        ttk.Button(settings, text="Browse", command=self._browse_dl_dir).grid(
            row=row, column=2, sticky="e", padx=(24, 0), pady=8)
        row += 1

        settings.columnconfigure(1, weight=1)

    def _on_threads_change(self, event):
        try:
            config.MAX_WORKERS = int(self.threads_var.get())
        except ValueError:
            pass

    def _on_default_lang_change(self, event):
        state.language = self.default_lang_var.get().strip() or "en"

    def _browse_dl_dir(self):
        d = filedialog.askdirectory(initialdir=config.DOWNLOAD_DIR)
        if d:
            config.DOWNLOAD_DIR = d
            os.makedirs(d, exist_ok=True)
            self.dl_dir_label.configure(text=d)


# --- Entry Point ---
def main():
    app = MangaDLApp()
    app.mainloop()


if __name__ == "__main__":
    main()