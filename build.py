
## build.py


"""
MangaDL - EXE Builder Script
Builds a single portable executable using PyInstaller.

Usage:
    python build.py              # Build GUI (web) version
    python build.py --cli        # Build CLI version
    python build.py --both       # Build both
    python build.py --clean      # Clean build artifacts
"""

import os
import sys
import shutil
import argparse
import subprocess
import platform


# --- Configuration ---
APP_NAME     = "MangaDL"
APP_VERSION  = "2.0.0"
MAIN_SCRIPT  = "app.py"
CLI_SCRIPT   = "cli.py"
ICON_FILE    = "icon.ico"   # Optional - will skip if not found
OUTPUT_DIR   = "dist"
BUILD_DIR    = "build"

SYSTEM = platform.system()  # Windows / Darwin / Linux


def run(cmd: list, **kwargs):
    """Run a shell command and stream output."""
    print(f"\n>>> {' '.join(cmd)}\n")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"\n[ERROR] Command failed with code {result.returncode}")
        sys.exit(result.returncode)
    return result


def check_pyinstaller():
    """Ensure PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} found.")
    except ImportError:
        print("PyInstaller not found. Installing...")
        run([sys.executable, "-m", "pip", "install", "pyinstaller"])


def clean():
    """Remove build artifacts."""
    for d in [BUILD_DIR, OUTPUT_DIR, "__pycache__"]:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"Removed: {d}")

    for root, dirs, files in os.walk("."):
        for f in files:
            if f.endswith(".pyc") or f.endswith(".spec"):
                path = os.path.join(root, f)
                os.remove(path)
                print(f"Removed: {path}")

    print("\nClean complete.")


def collect_data_files() -> list:
    """
    Collect all data files that need to be bundled into the EXE.
    Format: list of ('source_path', 'destination_in_bundle')
    """
    sep = ";" if SYSTEM == "Windows" else ":"
    data_files = []

    # Templates
    if os.path.exists("templates"):
        data_files.append(f"templates{sep}templates")

    # Static files
    if os.path.exists("static"):
        data_files.append(f"static{sep}static")

    # Config
    if os.path.exists("config.py"):
        data_files.append(f"config.py{sep}.")

    return data_files


def collect_hidden_imports() -> list:
    """
    Hidden imports that PyInstaller might miss.
    """
    return [
        # Flask / SocketIO
        "flask",
        "flask_socketio",
        "engineio",
        "socketio",
        "gevent",
        "gevent.monkey",
        "geventwebsocket",

        # Requests / Scraping
        "requests",
        "cloudscraper",
        "bs4",
        "lxml",
        "lxml.etree",
        "lxml.html",

        # Image processing
        "PIL",
        "PIL.Image",
        "PIL.JpegImagePlugin",
        "PIL.PngImagePlugin",
        "PIL.WebPImagePlugin",
        "PIL.GifImagePlugin",

        # PDF
        "reportlab",
        "reportlab.pdfgen",
        "reportlab.lib",

        # Crypto (cloudscraper dependency)
        "Crypto",
        "Crypto.Cipher",
        "cryptography",

        # Standard lib modules PyInstaller sometimes misses
        "zipfile",
        "threading",
        "concurrent.futures",
        "queue",
        "email",
        "email.mime",
        "http",
        "http.server",
        "urllib",
        "urllib.parse",
        "urllib.request",

        # Internal modules
        "sources",
        "sources.base",
        "sources.mangadex",
        "sources.manganato",
        "sources.webtoons",
        "sources.mangakakalot",
        "exporters",
        "exporters.epub",
        "exporters.cbz",
        "exporters.pdf",
        "exporters.images",
        "downloader",
        "downloader.engine",
    ]


def build_gui():
    """Build the GUI (web server) executable."""
    print("\n" + "=" * 56)
    print(f"  Building GUI EXE: {APP_NAME}")
    print("=" * 56)

    data_files = collect_data_files()
    hidden   = collect_hidden_imports()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", APP_NAME,
        "--distpath", OUTPUT_DIR,
        "--workpath", BUILD_DIR,
        "--noconfirm",
        "--clean",
    ]

    # Console window: keep it so users can see the server URL
    # Use --noconsole on Windows if you want a silent background app
    # cmd += ["--noconsole"]  # Uncomment for no console window

    # Icon
    if os.path.exists(ICON_FILE):
        cmd += ["--icon", ICON_FILE]
    else:
        print(f"Note: {ICON_FILE} not found, building without icon.")

    # Data files
    for d in data_files:
        cmd += ["--add-data", d]

    # Hidden imports
    for h in hidden:
        cmd += ["--hidden-import", h]

    # Collect all sub-packages
    cmd += ["--collect-all", "cloudscraper"]
    cmd += ["--collect-all", "flask_socketio"]
    cmd += ["--collect-all", "engineio"]
    cmd += ["--collect-all", "socketio"]
    cmd += ["--collect-all", "gevent"]

    # Entry point
    cmd.append(MAIN_SCRIPT)

    run(cmd)

    exe_name = f"{APP_NAME}.exe" if SYSTEM == "Windows" else APP_NAME
    exe_path = os.path.join(OUTPUT_DIR, exe_name)

    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"\n[OK] GUI EXE built: {exe_path} ({size_mb:.1f} MB)")
    else:
        print("\n[ERROR] EXE not found after build.")


def build_cli():
    """Build the CLI-only executable."""
    print("\n" + "=" * 56)
    print(f"  Building CLI EXE: {APP_NAME}-CLI")
    print("=" * 56)

    hidden = collect_hidden_imports()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", f"{APP_NAME}-CLI",
        "--distpath", OUTPUT_DIR,
        "--workpath", BUILD_DIR,
        "--noconfirm",
        "--clean",
        "--console",
    ]

    if os.path.exists(ICON_FILE):
        cmd += ["--icon", ICON_FILE]

    for h in hidden:
        cmd += ["--hidden-import", h]

    cmd += ["--collect-all", "cloudscraper"]

    cmd.append(CLI_SCRIPT)

    run(cmd)

    exe_name = f"{APP_NAME}-CLI.exe" if SYSTEM == "Windows" else f"{APP_NAME}-CLI"
    exe_path = os.path.join(OUTPUT_DIR, exe_name)

    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"\n[OK] CLI EXE built: {exe_path} ({size_mb:.1f} MB)")
    else:
        print("\n[ERROR] CLI EXE not found after build.")


def verify_sources():
    """Check all required files exist before building."""
    required = [
        "app.py",
        "cli.py",
        "config.py",
        "sources/__init__.py",
        "sources/base.py",
        "sources/mangadex.py",
        "sources/manganato.py",
        "sources/webtoons.py",
        "sources/mangakakalot.py",
        "exporters/__init__.py",
        "exporters/epub.py",
        "exporters/cbz.py",
        "exporters/pdf.py",
        "exporters/images.py",
        "downloader/__init__.py",
        "downloader/engine.py",
        "templates/index.html",
        "static/css/style.css",
        "static/js/app.js",
    ]

    print("Verifying source files...")
    missing = [f for f in required if not os.path.exists(f)]

    if missing:
        print("\n[ERROR] Missing required files:")
        for f in missing:
            print(f"  - {f}")
        print("\nMake sure all project files are in the current directory.")
        sys.exit(1)

    print(f"All {len(required)} required files found.")


def print_post_build_info():
    """Print instructions for running the built EXE."""
    exe_name = f"{APP_NAME}.exe" if SYSTEM == "Windows" else APP_NAME
    exe_path = os.path.join(OUTPUT_DIR, exe_name)

    print()
    print("=" * 56)
    print("  Build Complete")
    print("=" * 56)
    print()
    print("Output files:")
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            fp = os.path.join(OUTPUT_DIR, f)
            size_mb = os.path.getsize(fp) / (1024 * 1024)
            print(f"  {OUTPUT_DIR}/{f} ({size_mb:.1f} MB)")

    print()
    print("How to distribute:")
    print(f"  1. Copy the EXE from the '{OUTPUT_DIR}/' folder")
    print(f"  2. The EXE is fully self-contained — no Python needed")
    print()
    print("How to run:")
    if SYSTEM == "Windows":
        print(f"  Double-click {APP_NAME}.exe")
        print(f"  Then open http://localhost:5000 in your browser")
    else:
        print(f"  ./{APP_NAME}")
        print(f"  Then open http://localhost:5000 in your browser")
    print()
    print("Note: Downloads will be saved to a 'downloads/' folder")
    print("      in the same directory as the EXE.")
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="build.py",
        description="MangaDL EXE Builder",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Build CLI-only executable",
    )
    parser.add_argument(
        "--both",
        action="store_true",
        help="Build both GUI and CLI executables",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts and exit",
    )
    args = parser.parse_args()

    print()
    print("=" * 56)
    print(f"  MangaDL Builder v{APP_VERSION}")
    print(f"  Platform: {SYSTEM} ({platform.machine()})")
    print(f"  Python:   {sys.version.split()[0]}")
    print("=" * 56)

    if args.clean:
        clean()
        return

    check_pyinstaller()
    verify_sources()

    if args.both:
        build_gui()
        build_cli()
    elif args.cli:
        build_cli()
    else:
        build_gui()

    print_post_build_info()


if __name__ == "__main__":
    main()