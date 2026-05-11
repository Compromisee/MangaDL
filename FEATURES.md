<div align="center">

# MangaDL — Complete Feature List

A comprehensive breakdown of every feature in MangaDL v2.0

[← Back to README](README.md)

</div>

---

## Table of Contents

- [Sources & Discovery](#sources--discovery)
- [Search & Browse](#search--browse)
- [Manga Detail View](#manga-detail-view)
- [Chapter & Volume Selection](#chapter--volume-selection)
- [Language Support](#language-support)
- [Download Engine](#download-engine)
- [Export Formats](#export-formats)
- [Download Modes](#download-modes)
- [Cart System](#cart-system)
- [Queue Management](#queue-management)
- [Library Management](#library-management)
- [History](#history)
- [Themes & Visual Customization](#themes--visual-customization)
- [Accessibility](#accessibility)
- [Animations & Effects](#animations--effects)
- [User Interfaces](#user-interfaces)
- [Web Dashboard Specific](#web-dashboard-specific)
- [Desktop GUI Specific](#desktop-gui-specific)
- [Terminal UI Specific](#terminal-ui-specific)
- [CLI Specific](#cli-specific)
- [Settings & Configuration](#settings--configuration)
- [Data Persistence](#data-persistence)
- [Networking & Performance](#networking--performance)
- [Error Handling & Recovery](#error-handling--recovery)
- [Developer Features](#developer-features)
- [Security & Privacy](#security--privacy)
- [Distribution & Deployment](#distribution--deployment)
- [Keyboard Shortcuts](#keyboard-shortcuts)

---

## Sources & Discovery

- Multi-source manga search engine
- **MangaDex** — official API integration with 40+ languages
- **MangaNato** — HTML scraper with full chapter list
- **Webtoons** — official LINE Webtoons platform support
- **MangaKakalot** — deep archive of older series
- Automatic source detection from URLs
- Pluggable source architecture (extend `BaseSource`)
- Per-source error isolation (one source failing doesn't break others)
- Cloudflare bypass via `cloudscraper` for protected sites
- Concurrent multi-source search (parallel threading)
- Source-specific HTTP headers (Referer, User-Agent)
- Per-source request retry with exponential backoff
- Source health status indicators
- URL pattern matching for source identification
- Source registry system for adding new providers

---

## Search & Browse

- Real-time search across all sources simultaneously
- Search by title, author, or keyword
- Source filter dropdown (all sources or specific one)
- Multi-threaded query execution (one thread per source)
- Result deduplication
- Source badge on every result card
- Cover art previews with lazy loading
- Author display
- Status display (ongoing, completed, hiatus)
- Genre tags
- Two view modes: **grid** and **list**
- Toggle between view modes with one click
- Empty state with helpful icon when no results
- Result count display
- Search-on-Enter keyboard support
- Loading spinner with descriptive text
- Auto-search on page load (when query in URL)
- Animated card entry with staggered delays

---

## Manga Detail View

- Beautiful modal overlay with backdrop blur
- Cover image with skeleton loader and fade-in
- Two-phase image loading (placeholder → real image)
- Title with serif typography
- Author display
- Status badge (ongoing/completed/hiatus)
- Source attribution
- Chapter count summary
- Volume count summary
- Genre tags
- Full description text
- Add to Cart button
- Download button (configurable)
- Modal close on click-outside
- Modal close on Escape key
- Smooth open/close animations

---

## Chapter & Volume Selection

- Tabbed view: **Chapters** and **Volumes**
- Live tab switching without reload
- Chapter list with checkboxes (all selected by default)
- Volume list with collapsible sections
- Volume header checkbox toggles all child chapters
- Indeterminate state when partially selected
- Chapter number display
- Chapter title display
- Volume label per chapter
- Page count per chapter (where available)
- **Select All** button
- **Select None** button
- **Invert selection** button
- Chapter range filter (From / To)
- Volume range filter (From / To)
- Real-time filter input (search chapters by text)
- Real-time volume filter input
- Bidirectional sync between chapter and volume views
- Click-anywhere-to-toggle on rows
- Auto-switch to volumes tab when "By Volume" mode selected
- Visual selection indicators
- Smooth checkbox animations

---

## Language Support

- 40+ languages on MangaDex
- Multi-language support on Webtoons (English, Korean, Japanese, Chinese, Thai, Indonesian, Spanish, French, German)
- Live language switching without losing place
- Language dropdown in manga detail
- Auto-detection of available languages per manga
- Automatic fallback to first available language if requested unavailable
- Human-readable language names (English, Japanese, Korean...)
- ISO language code display
- Per-chapter language tagging
- Language persisted across modal opens

---

## Download Engine

- Multi-threaded download architecture
- Outer thread pool for tasks (configurable, default 4)
- Inner thread pool per chapter for pages (configurable 2-16)
- Concurrent task limit (max simultaneous manga downloads)
- Per-page retry with exponential backoff
- Configurable retry attempts (1-20)
- Configurable request timeout (5-300 seconds)
- Streaming downloads with chunked I/O
- Real-time speed calculation
- Real-time byte counter
- Real-time progress percentage
- Current chapter tracking
- Cancellation support (graceful abortion)
- Cancel flag with thread-safe checking
- Lock-protected counters
- Auto-cleanup of temp files after task completion
- Per-chapter error isolation
- Image format auto-detection (JPG, PNG, WebP, GIF)
- Image content-type detection from HTTP headers
- Source-specific Referer headers for hot-link protection bypass
- Failed page retries don't block other pages

---

## Export Formats

### CBZ (Comic Book Archive)
- Standard ZIP archive format
- Compatible with all major comic readers
- No compression for faster reading
- Sequential page numbering
- Proper file extensions per image
- Volume mode bundles chapters with subdirectories

### PDF
- Multi-page PDF generation
- Auto RGB conversion from any format
- 150 DPI resolution by default
- Pillow-based rendering
- Volume mode combines all chapters
- All-in-one mode supported

### EPUB (Fixed-Layout)
- **Custom-built EPUB writer** (no `ebooklib` dependency)
- EPUB 3.0 specification compliance
- Fixed-layout `rendition:layout: pre-paginated`
- Per-page viewport meta matching image dimensions
- Apple Books validated
- Calibre validated
- Kobo readers validated
- Thorium Reader validated
- Auto WebP to JPEG conversion for compatibility
- Proper TOC with chapter navigation
- Volume mode creates sectioned TOC
- mimetype file first and uncompressed (spec required)
- Clean XHTML markup
- Embedded CSS for full-page images

### Images (Raw)
- Original quality preservation
- Organized folder structure: `Title/Chapter X/0001.jpg`
- Sequential zero-padded numbering
- Volume mode creates volume folders
- Original file extensions preserved

---

## Download Modes

- **By Chapter** — each chapter as a separate file
- **By Volume** — chapters grouped by volume into single files
- **All-in-One** — entire selection in one combined file
- Mode-aware file naming
- Mode persistence in settings
- Per-download mode override
- Volume detection from source metadata
- Unassigned chapters grouped under "No Volume"

---

## Cart System

- Add multiple manga to cart from any source
- Cart persisted in localStorage (survives reload)
- Per-item format and mode configuration
- Cart count badge in sidebar
- Cart pill in topbar (quick access)
- Visual cart item cards with covers
- Remove individual items
- Clear entire cart button
- Batch download all cart items at once
- Per-item chapter count display
- Source label per cart item
- Cart-level format override
- Cart-level mode override
- Auto-redirect to downloads view after batch start
- Toast notification on cart actions
- Empty state with call-to-action
- Animation on cart item addition

---

## Queue Management

- Dedicated Queue view
- Numbered queue position
- Total chapters per queued task
- Format and mode display
- Auto-refresh from API
- Empty state when queue empty
- Queue counts toward concurrent task limit
- FIFO processing order

---

## Library Management

- Browse all downloaded files
- Recursive directory walk
- File type icons (CBZ, PDF, EPUB, folders)
- File size display (auto-formatted KB/MB/GB)
- Relative path display
- Open download folder in OS file manager (one click)
- Empty state when no downloads
- Sorted alphabetically
- Cross-platform folder opening (Windows, macOS, Linux)

---

## History

- Auto-tracking of viewed manga
- Last 50 entries retained
- localStorage persistence
- Cover thumbnails
- Title, source, and date display
- Click to re-open manga modal
- Clear history button
- No tracking sent to any server (fully local)
- Sortable by recency

---

## Themes & Visual Customization

### 9 Built-in Themes
- **Dark** (default) — minimalist dark with blue accent
- **Light** — clean bright with darker blue
- **Midnight** — pure OLED black with indigo
- **Forest** — dark green-tinted with green accent
- **Rose** — warm pink-tinted with rose accent
- **Amber** — sepia warm with amber accent
- **Ocean** — deep teal with cyan accent
- **HC Dark** — high contrast (WCAG AAA), electric cyan
- **HC Light** — high contrast (WCAG AAA), classic blue

### Theme Features
- Live theme switching (no reload)
- Theme persistence in localStorage
- Theme picker dropdown with color swatches
- Active theme indicator with checkmark
- Theme-aware browser chrome color (`theme-color` meta)
- Theme-aware splash screen
- Smooth color transitions
- Per-theme accent colors throughout UI
- Per-theme shadow opacity

### Typography
- **Source Serif 4** for headings and titles
- **JetBrains Mono** for UI text and code
- Variable font weights (300-800)
- Optical sizing (8pt-60pt)

---

## Accessibility

- **Reduce motion** toggle (disables all animations)
- **Larger text** toggle (increased base font size globally)
- Respects OS `prefers-reduced-motion: reduce`
- WCAG AAA contrast ratios in HC themes
- 7:1 minimum contrast for HC modes
- 3px focus outlines with offset in HC modes
- Bold font weight enforcement in HC modes
- 2px borders on all interactive elements in HC modes
- Keyboard navigation support throughout
- Focus indicators on all buttons
- Semantic HTML5 markup
- Screen reader friendly
- Alt text on images
- ARIA-friendly toggle switches
- Tab order respected
- Escape key closes modals

---

## Animations & Effects

### Splash Screen
- Animated icon float
- Pulsing rings
- Loading bar progression
- Fade-out on completion

### Cards & UI
- Staggered card entry animations
- Card hover lift with shadow
- Icon scale + rotate on hover
- Smooth color transitions
- Backdrop blur on modals
- Modal slide-up entry
- Toast slide-in from bottom

### Hero & Backgrounds
- Animated radial gradient backgrounds
- Background "breathing" effect
- Subtle parallax on scroll
- Glow effects on accent elements

### Confetti
- Canvas-based particle system
- Fires on download completion
- 120 colored rectangles per burst
- Realistic physics (gravity, rotation, velocity decay)
- 8-color palette
- Auto-disabled if reduce motion enabled
- Per-task tracking (only fires once per download)

### Progress
- Smooth progress bar fills
- Color-coded by status (blue → green on complete, red on error)
- Pulse animation on active downloads
- Glow effect on active progress

### Status Indicators
- Active downloads pulse
- Online status dots glow
- Spinner rotation for loading states
- Indeterminate checkbox states

---

## User Interfaces

MangaDL provides **four** complete interfaces sharing one backend:

1. **Web Dashboard** (default)
2. **Desktop GUI** (Tkinter)
3. **Terminal UI** (Rich)
4. **Command Line** (argparse)

All four use the same `sources/`, `exporters/`, and `downloader/` packages.

---

## Web Dashboard Specific

- Single-page application architecture
- Sidebar navigation with sections (Navigate, Manage, System)
- Active route indicator (left bar)
- Collapsible sidebar on mobile
- Top bar with breadcrumb
- Active downloads pill in top bar
- Cart pill in top bar
- 10 distinct views (Home, Search, URL Import, Cart, Queue, Downloads, Library, History, Settings, About)
- WebSocket live updates via Socket.IO
- Real-time progress without polling
- Responsive design (mobile-friendly)
- PWA-ready manifest support
- SVG favicon (theme-aware)
- Auto-open browser on launch (when running as EXE)
- Toast notifications (success/error variants)
- Toast stacking and timeout
- Material Icons Outlined throughout

### Home View
- Hero section with animated background
- Two CTA buttons (Search, URL Import)
- Quick-access cards (Search, Cart, Downloads, Library)
- Source status grid with online indicators
- Format showcase cards
- Smooth scroll navigation

### About View
- Animated app icon
- Version display
- Stat counters (sources, formats, modes, languages)
- Project description

---

## Desktop GUI Specific

- Native Tkinter window (no browser required)
- Custom dark theme styling via ttk
- Sidebar navigation
- Treeview-based result lists
- Multi-column tables (title, author, source, status)
- Chapter/volume tab toggle
- Checkbox columns
- Volume range inputs
- Live download polling (1Hz)
- Settings panel with all backend options
- Browse for download directory
- Open download folder button
- Cancel selected download button
- Clear completed button
- Standalone executable possible

---

## Terminal UI Specific

- Powered by Rich library
- Gradient ASCII art banner
- Color-coded sources
- Interactive menu navigation
- Numbered selection prompts
- Live progress display with auto-refresh
- Gradient progress bars (purple → blue → green → red)
- Tree view for volumes
- Paginated chapter lists (30 per page)
- Color-coded status indicators
- Beautiful tables with rounded borders
- Source colors (magenta MangaDex, cyan MangaNato, etc.)
- Truncation with ellipsis for long text
- Status icons in panels
- Confirmation prompts
- Library browser with file type colors
- Settings editor

---

## CLI Specific

- argparse-based command structure
- Subcommands: `search`, `info`, `download`, `sources`, `library`, `interactive`
- Aliases: `dl` for `download`, `i` for `interactive`
- Comprehensive `--help` for all commands
- Chapter range syntax: `1-50`, `1,5,10-20,30`
- Format flag: `-f cbz|pdf|epub|images`
- Mode flag: `-m chapter|volume|all`
- Source flag: `-s mangadex|manganato|webtoons|mangakakalot`
- Output directory flag: `-o /path/to/output`
- Skip confirmation flag: `-y`
- Interactive mode with guided prompts
- Search returns numbered results
- Direct selection from search results
- Live progress bars in terminal
- Exit codes for scripting
- Pipe-friendly output

---

## Settings & Configuration

- **Download threads** (1-32, default 8)
- **Default format** (CBZ, PDF, EPUB, Images)
- **Default mode** (chapter, volume, all)
- **Download directory** (any writable path)
- **Request timeout** (5-300 seconds)
- **Retry attempts** (1-20)
- **Max concurrent tasks** (1-8)
- **Reduce motion** toggle
- **Larger text** toggle
- **Theme** selection (9 themes)
- Live save (no Save button needed)
- Settings persisted across sessions
- Settings sync between web and other interfaces (via API)
- Browse button for directory picker
- Path validation
- Apply button for directory changes
- Settings exposed via REST API

---

## Data Persistence

- **Cart** — saved to `localStorage` (browser)
- **History** — saved to `localStorage` (browser, last 50 entries)
- **Theme preference** — saved to `localStorage`
- **Accessibility preferences** — saved to `localStorage`
- **Server settings** — saved in memory (config.py defaults)
- **Downloads** — saved to disk in configurable directory
- **Library files** — persistent on disk
- **Task history** — in-memory (cleared on server restart)

---

## Networking & Performance

- HTTP keep-alive connections
- Connection pooling per session
- Streaming downloads (chunked reading)
- Configurable chunk size (default 8KB)
- Multi-threaded image fetching
- Concurrent source queries
- Lazy-loaded images in search results
- WebSocket for real-time updates (no polling)
- Cloudflare bypass via cloudscraper
- Custom User-Agent strings
- Automatic Referer header per source
- HTTP/1.1 with Accept: image/webp,image/apng
- Auto retry on connection errors
- Configurable timeout per request
- Smart deduplication on MangaDex chapters

---

## Error Handling & Recovery

- Per-page retry on download failure
- Per-chapter error isolation (one bad chapter doesn't stop the rest)
- Per-source error isolation in search
- Graceful task cancellation
- Error log per task (last 5 errors visible)
- Last 3 errors shown inline in download UI
- Error toast notifications
- HTTP timeout handling
- Connection reset handling
- Invalid URL detection
- Missing source detection
- Empty result handling
- Image format fallback (data → dataSaver on MangaDex)
- External chapter detection (skipped on MangaDex when no pages)
- Permission error messages
- Fallback to first available language

---

## Developer Features

- Modular source architecture
- Pluggable exporter system
- Abstract base classes (`BaseSource`)
- Dataclass-based models (`Chapter`, `MangaInfo`, `DownloadTask`)
- REST API with all features exposed
- Socket.IO event system
- Engine API for programmatic use
- Importable modules from external scripts
- Python 3.10+ type hints
- Console logging with `[Source]` prefixes
- Debug-friendly error messages
- Stack traces preserved in errors
- All HTTP requests via shared session helper
- Easy to add new sources (3 methods to implement)
- Easy to add new exporters (2 methods to implement)
- Hot-reload friendly during development
- Open source MIT license

---

## Security & Privacy

- **Zero telemetry** — no usage data sent anywhere
- **Zero analytics** — no tracking scripts
- **No accounts** — fully anonymous
- **Local-only** — no server-side storage
- **No cloud sync** — your library stays on your machine
- **No third-party CDNs for app code** (only Google Fonts/Icons for UI)
- **Open source** — full code auditable
- HTTPS for all source requests
- No password storage (no auth needed)
- Session isolation per Python process
- No external API keys required
- Downloads stay on local disk only

---

## Distribution & Deployment

- **Single-file EXE** — one `.exe`, no dependencies
- Auto-creates `downloads/` folder next to EXE
- No installer needed (portable)
- Auto-opens browser on launch
- Console window shows server logs
- Cross-platform builds: Windows, macOS, Linux
- Custom icon support (`.ico` on Windows)
- PyInstaller-based bundling
- All assets embedded in EXE (templates, CSS, JS)
- Configurable port (default 5000)
- Auto-detects PyInstaller temp dir
- Standalone Python script also supported
- Docker-ready architecture
- GitHub Actions CI/CD template included
- Build script with verification
- Build script with cleanup
- Build script with hidden import collection
- Multiple build variants (GUI, CLI, both)
- Promotional landing site included

---

## Keyboard Shortcuts

### Web Dashboard
- `Enter` (in search box) — execute search
- `Enter` (in URL box) — fetch manga
- `Enter` (in directory input) — apply
- `Escape` — close modal
- `Tab` / `Shift+Tab` — navigate between focusable elements
- Click-outside modal — close

### CLI
- `Ctrl+C` — interrupt current operation
- `Enter` — confirm default selection
- `q` / `quit` / `exit` / `b` / `back` — navigate back

### TUI
- Number keys — select menu items
- `Enter` — confirm selection
- `q` — quit
- `b` — back

---

## File Format Support

### Input (Image formats parsed)
- JPEG / JPG
- PNG
- WebP (auto-converted to JPG for EPUB)
- GIF
- BMP
- ICO

### Output (Export formats produced)
- CBZ (ZIP archive)
- PDF (multi-page)
- EPUB (fixed-layout EPUB 3)
- Image folders (original formats preserved)

---

## Browser Compatibility

- Chrome / Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Opera 76+
- Mobile browsers (iOS Safari, Chrome Android)

---

## Operating System Support

### Tested on
- Windows 10 / 11
- macOS 11+ (Intel and Apple Silicon)
- Ubuntu 20.04+ / Debian 11+
- Fedora 35+
- Arch Linux

### Should work on
- Any Linux with Python 3.10+
- Windows 7/8 (Python 3.8 build only)
- BSD variants

---

## Statistics

- **150+** features
- **9** themes
- **4** sources
- **4** export formats
- **3** download modes
- **4** user interfaces
- **40+** languages
- **10** distinct dashboard views
- **20+** REST API endpoints
- **~5,000** lines of Python
- **~3,500** lines of CSS
- **~1,500** lines of JavaScript
- **0** telemetry
- **0** ads
- **0** required accounts

---

<div align="center">

**MangaDL — Built for readers, by readers.**

[← Back to README](README.md) · [BUILD.md →](BUILD.md)

</div>
