"""
MangaDL - All-inclusive single-file EXE builder.
Produces ONE .exe with NO dependencies.
Only creates a 'downloads' folder next to itself at runtime.

Usage:
    python build_single.py
    python build_single.py --clean
"""

import os
import sys
import shutil
import subprocess
import platform

APP_NAME = "MangaDL"
APP_VERSION = "2.0.0"
ENTRY = "app.py"
ICON = "icon.ico"
OUT = "dist"
WORK = "build"
SYSTEM = platform.system()
SEP = ";" if SYSTEM == "Windows" else ":"

# Always use the directory of THIS script as the project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def run(cmd, **kw):
    print(f"\n>>> {' '.join(cmd)}\n")
    r = subprocess.run(cmd, cwd=PROJECT_ROOT, **kw)
    if r.returncode != 0:
        print(f"\n[ERROR] Command failed with code {r.returncode}")
        sys.exit(r.returncode)


def ensure_pyinstaller():
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} OK.")
    except ImportError:
        print("Installing PyInstaller...")
        run([sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"])


def clean():
    for d in (OUT, WORK, "__pycache__"):
        full = os.path.join(PROJECT_ROOT, d)
        if os.path.exists(full):
            shutil.rmtree(full, ignore_errors=True)
            print(f"Removed: {full}")
    for f in os.listdir(PROJECT_ROOT):
        if f.endswith(".spec"):
            full = os.path.join(PROJECT_ROOT, f)
            os.remove(full)
            print(f"Removed: {full}")
    print("\nClean complete.")


def collect_data():
    """All non-Python files that need to be inside the exe.
    Use absolute paths to avoid PyInstaller's specpath confusion."""
    bundles = []

    templates_path = os.path.join(PROJECT_ROOT, "templates")
    static_path = os.path.join(PROJECT_ROOT, "static")
    config_path = os.path.join(PROJECT_ROOT, "config.py")

    if os.path.exists(templates_path):
        bundles.append(f"{templates_path}{SEP}templates")
    if os.path.exists(static_path):
        bundles.append(f"{static_path}{SEP}static")
    if os.path.exists(config_path):
        bundles.append(f"{config_path}{SEP}.")

    return bundles


def collect_hidden_imports():
    """Modules PyInstaller might miss during static analysis."""
    return [
        # Flask + SocketIO ecosystem
        "flask", "flask_socketio", "engineio",
        "engineio.async_drivers.threading",
        "socketio", "werkzeug", "werkzeug.serving",

        # HTTP / scraping
        "requests", "cloudscraper", "bs4",
        "lxml", "lxml.etree", "lxml.html", "lxml._elementpath",
        "urllib3",

        # Image processing
        "PIL", "PIL.Image", "PIL.JpegImagePlugin", "PIL.PngImagePlugin",
        "PIL.WebPImagePlugin", "PIL.GifImagePlugin", "PIL.BmpImagePlugin",
        "PIL.IcoImagePlugin", "PIL.PdfImagePlugin",

        # Reportlab (PDF)
        "reportlab", "reportlab.pdfgen", "reportlab.lib",

        # Encryption (cloudscraper deps)
        "Crypto", "Crypto.Cipher",

        # Standard lib
        "zipfile", "threading", "concurrent.futures", "queue",
        "email", "email.mime", "http", "http.server", "http.client",
        "urllib", "urllib.parse", "urllib.request",
        "json", "uuid", "hashlib", "tempfile",

        # MangaDL internal modules
        "config",
        "sources", "sources.base", "sources.mangadex",
        "sources.manganato", "sources.webtoons", "sources.mangakakalot",
        "exporters", "exporters.epub", "exporters.cbz",
        "exporters.pdf", "exporters.images",
        "downloader", "downloader.engine",
    ]


def verify_files():
    required = [
        "app.py", "config.py",
        "sources/__init__.py", "sources/base.py",
        "sources/mangadex.py", "sources/manganato.py",
        "sources/webtoons.py", "sources/mangakakalot.py",
        "exporters/__init__.py", "exporters/epub.py",
        "exporters/cbz.py", "exporters/pdf.py", "exporters/images.py",
        "downloader/__init__.py", "downloader/engine.py",
        "templates/index.html",
        "static/css/style.css", "static/js/app.js",
    ]
    missing = []
    for f in required:
        full = os.path.join(PROJECT_ROOT, f.replace("/", os.sep))
        if not os.path.exists(full):
            missing.append(f)

    if missing:
        print("\n[ERROR] Missing required files:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)
    print(f"All {len(required)} required files present.")


def build():
    print("\n" + "=" * 56)
    print(f"  Building all-inclusive single-file EXE")
    print(f"  Target: {APP_NAME} {APP_VERSION}")
    print(f"  Platform: {SYSTEM}")
    print(f"  Project: {PROJECT_ROOT}")
    print("=" * 56)

    out_path = os.path.join(PROJECT_ROOT, OUT)
    work_path = os.path.join(PROJECT_ROOT, WORK)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", APP_NAME,
        "--distpath", out_path,
        "--workpath", work_path,
        # NOTE: removed --specpath (it caused the data path bug)
        "--noconfirm",
        "--clean",
        "--console",
    ]

    icon_path = os.path.join(PROJECT_ROOT, ICON)
    if os.path.exists(icon_path):
        cmd += ["--icon", icon_path]
        print(f"Using icon: {icon_path}")

    for d in collect_data():
        cmd += ["--add-data", d]

    for h in collect_hidden_imports():
        cmd += ["--hidden-import", h]

    # Only collect-all packages that actually exist as packages
    for pkg in ("cloudscraper", "PIL", "lxml", "reportlab"):
        cmd += ["--collect-all", pkg]

    cmd.append(os.path.join(PROJECT_ROOT, ENTRY))

    run(cmd)

    exe_name = f"{APP_NAME}.exe" if SYSTEM == "Windows" else APP_NAME
    exe_path = os.path.join(out_path, exe_name)

    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print()
        print("=" * 56)
        print("  BUILD SUCCESSFUL")
        print("=" * 56)
        print(f"  Output:  {exe_path}")
        print(f"  Size:    {size_mb:.1f} MB")
        print()
        print("  This single file contains EVERYTHING:")
        print("    - Python runtime")
        print("    - All dependencies")
        print("    - All templates and static files")
        print("    - All source code")
        print()
        print("  It will create a 'downloads' folder next to itself")
        print("  on first run. No installation required.")
        print()

        # Clean up build cache
        if os.path.exists(work_path):
            shutil.rmtree(work_path, ignore_errors=True)
            print("  Cleaned up build cache.")

        # Remove leftover .spec file from project root
        spec_file = os.path.join(PROJECT_ROOT, f"{APP_NAME}.spec")
        if os.path.exists(spec_file):
            os.remove(spec_file)

        print()
    else:
        print(f"\n[ERROR] EXE not produced at {exe_path}")
        sys.exit(1)


def main():
    if "--clean" in sys.argv:
        clean()
        return

    ensure_pyinstaller()
    verify_files()
    build()


if __name__ == "__main__":
    main()