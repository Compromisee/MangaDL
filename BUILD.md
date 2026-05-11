## BUILD.md

<div align="center">

# Building MangaDL Executables

Complete guide for compiling MangaDL into standalone executables that can run without Python installed.

[![PyInstaller](https://img.shields.io/badge/PyInstaller-6.0+-orange?style=flat-square)](https://pyinstaller.org/)
[![Cross-platform](https://img.shields.io/badge/Builds-Windows%20%7C%20macOS%20%7C%20Linux-blue?style=flat-square)]()

[← Back to README](README.md)

</div>

---

## Table of Contents

- [Overview](#overview)
- [What Gets Built](#what-gets-built)
- [Prerequisites](#prerequisites)
- [Quick Build](#quick-build)
- [Platform-Specific Instructions](#platform-specific-instructions)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Build Variants](#build-variants)
- [Adding a Custom Icon](#adding-a-custom-icon)
- [Reducing EXE Size](#reducing-exe-size)
- [Distribution](#distribution)
- [Build Troubleshooting](#build-troubleshooting)
- [Advanced: Custom .spec File](#advanced-custom-spec-file)
- [CI/CD Automated Builds](#cicd-automated-builds)

---

## Overview

The build system uses **PyInstaller** to bundle MangaDL into a single self-contained executable. Users can run the EXE on any compatible system without installing Python or any dependencies.

The included `build.py` script automates the entire process:
- Verifies all source files are present
- Installs PyInstaller if missing
- Bundles all dependencies (Flask, Pillow, cloudscraper, etc.)
- Includes templates and static files
- Detects icon if present
- Outputs to `dist/` folder

---

## What Gets Built

| Variant | Output File | Size | Description |
|---------|-------------|------|-------------|
| **GUI** | `MangaDL.exe` | ~80-150 MB | Web server launcher (default) |
| **CLI** | `MangaDL-CLI.exe` | ~60-100 MB | Command-line only |
| **Both** | Both files | combined | Build both at once |

EXE size is large because PyInstaller bundles the entire Python runtime + all dependencies into one file.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Python** | 3.10+ | Match your target architecture (32 vs 64-bit) |
| **pip** | Latest | `python -m pip install --upgrade pip` |
| **PyInstaller** | 6.0+ | Auto-installed by `build.py` |
| **Disk space** | ~500 MB | For build artifacts |
| **RAM** | ~2 GB | During compilation |

> **Important:** Build on the platform you're targeting. Windows EXEs cannot be built on macOS/Linux without complex cross-compilation setup.

---

## Quick Build

### Step 1: Activate your virtual environment

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### Step 3: Run the build

```bash
python build.py
```

### Step 4: Find your EXE

```
dist/
└── MangaDL.exe    # or MangaDL on Mac/Linux
```

Test it by double-clicking — it should open a console window and start the server. Open `http://localhost:5000` in your browser.

---

## Platform-Specific Instructions

### Windows

<details open>
<summary><b>Step-by-step Windows build</b></summary>

```batch
:: Open Command Prompt or PowerShell as Administrator (recommended)
:: Navigate to your project folder
cd C:\path\to\mangadl

:: Create venv if you haven't yet
python -m venv venv

:: Activate it
venv\Scripts\activate

:: Install dependencies
pip install -r requirements.txt
pip install pyinstaller

:: Build the GUI version
python build.py

:: Output: dist\MangaDL.exe

:: Optional: build CLI too
python build.py --cli

:: Optional: build both
python build.py --both
```

**Test the EXE:**
```batch
cd dist
MangaDL.exe
```

A console window appears, showing the server URL. Open `http://localhost:5000` in your browser.

</details>

---

### macOS

<details>
<summary><b>Step-by-step macOS build</b></summary>

```bash
# Open Terminal
cd /path/to/mangadl

# Create venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build
python build.py

# Output: dist/MangaDL

# Make executable
chmod +x dist/MangaDL

# Test
./dist/MangaDL
```

**For a proper `.app` bundle:**

```bash
python -m PyInstaller --windowed --name MangaDL \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --collect-all cloudscraper \
    --collect-all flask_socketio \
    app.py
```

The result is `dist/MangaDL.app` which you can drag to Applications.

> **Note for macOS Catalina+:** Unsigned apps trigger Gatekeeper warnings. Right-click the app → Open → confirm. For distribution, you'll need an Apple Developer certificate.

</details>

---

### Linux

<details>
<summary><b>Step-by-step Linux build</b></summary>

**Install build prerequisites:**

```bash
# Debian / Ubuntu
sudo apt install python3 python3-venv python3-pip python3-dev \
                 libxml2-dev libxslt1-dev libjpeg-dev zlib1g-dev

# Fedora / RHEL
sudo dnf install python3 python3-pip python3-devel \
                 libxml2-devel libxslt-devel libjpeg-devel zlib-devel

# Arch
sudo pacman -S python python-pip libxml2 libxslt libjpeg-turbo zlib
```

**Build:**

```bash
cd /path/to/mangadl
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
pip install pyinstaller

python build.py

# Output: dist/MangaDL
chmod +x dist/MangaDL
./dist/MangaDL
```

**Optional: Create a `.desktop` launcher:**

Save as `~/.local/share/applications/mangadl.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=MangaDL
Comment=Universal Manga Downloader
Exec=/full/path/to/dist/MangaDL
Icon=/full/path/to/icon.png
Terminal=true
Categories=Utility;Network;
```

</details>

---

## Build Variants

### GUI Build (Web Server) — Default

```bash
python build.py
```

Builds `MangaDL.exe` that launches the Flask web server. User opens `http://localhost:5000` in their browser. Console window stays open showing logs.

### CLI Build

```bash
python build.py --cli
```

Builds `MangaDL-CLI.exe` — a pure command-line tool. No web server, no browser. Run with arguments like `MangaDL-CLI.exe download URL`.

### Build Both

```bash
python build.py --both
```

Builds both variants in sequence. Output:
```
dist/
├── MangaDL.exe
└── MangaDL-CLI.exe
```

### Clean Build Artifacts

```bash
python build.py --clean
```

Removes `build/`, `dist/`, `__pycache__/`, and any `.spec` files. Use before committing or to start fresh.

---

## Adding a Custom Icon

### Windows

1. Create or download a `.ico` file (use [favicon.io](https://favicon.io) to convert PNG to ICO)
2. Save it as `icon.ico` in the project root
3. Run `python build.py` — the script auto-detects it

To verify:
- Right-click the EXE → Properties → check the icon shows correctly

### macOS

1. Create an `.icns` file (use `iconutil` or [iConvert Icons](https://iconverticons.com))
2. Edit `build.py`:
   ```python
   ICON_FILE = "icon.icns"
   ```
3. Build: `python build.py`

### Linux

Linux EXEs don't have embedded icons. Set the icon in your `.desktop` launcher file instead.

### Convert SVG to ICO

```bash
pip install Pillow cairosvg

python -c "
from cairosvg import svg2png
from PIL import Image
from io import BytesIO

png_data = svg2png(url='static/favicon.svg', output_width=256, output_height=256)
img = Image.open(BytesIO(png_data))
img.save('icon.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
print('icon.ico created')
"
```

---

## Reducing EXE Size

The default EXE is ~80-150 MB. To shrink it:

### 1. Use UPX Compression

Install [UPX](https://upx.github.io/):

**Windows:** Download `upx.exe`, place it in your project folder or PATH.

**macOS:** `brew install upx`

**Linux:** `sudo apt install upx-ucl`

PyInstaller auto-detects UPX. Rebuild:

```bash
python build.py
```

Expected reduction: **30-50% smaller**.

### 2. Exclude Unused Modules

Edit `build.py` and add `--exclude-module` flags:

```python
cmd += [
    "--exclude-module", "matplotlib",
    "--exclude-module", "numpy",
    "--exclude-module", "scipy",
    "--exclude-module", "pandas",
    "--exclude-module", "tkinter",  # Only if not building gui.py
]
```

### 3. Strip Debug Symbols (Linux/Mac)

```bash
strip dist/MangaDL
```

### 4. Use `--onedir` Instead of `--onefile`

Edit `build.py`, change:
```python
cmd = [..., "--onefile", ...]
```
to:
```python
cmd = [..., "--onedir", ...]
```

This produces a folder with the EXE + dependencies, instead of a single file. Faster startup, easier to compress with installer tools, but harder to distribute.

---

## Distribution

### Single-file Distribution

Just send the `MangaDL.exe` file. It's fully self-contained.

```
MangaDL.exe (140 MB)
```

### Folder Distribution

Bundle the EXE with sample folders:

```
MangaDL/
├── MangaDL.exe
├── README.txt           ← simple usage guide
├── downloads/           ← empty, will be created on first run
└── temp/                ← empty, will be created on first run
```

### Creating an Installer

**Windows — Inno Setup:**

Download [Inno Setup](https://jrsoftware.org/isinfo.php), create `installer.iss`:

```ini
[Setup]
AppName=MangaDL
AppVersion=2.0
DefaultDirName={pf}\MangaDL
OutputBaseFilename=MangaDL-Setup
OutputDir=installer
Compression=lzma2/ultra
SolidCompression=yes

[Files]
Source: "dist\MangaDL.exe"; DestDir: "{app}"
Source: "README.md"; DestDir: "{app}"

[Icons]
Name: "{commonprograms}\MangaDL"; Filename: "{app}\MangaDL.exe"
Name: "{commondesktop}\MangaDL"; Filename: "{app}\MangaDL.exe"
```

Compile to get `MangaDL-Setup.exe`.

**macOS — DMG:**

```bash
brew install create-dmg

create-dmg \
    --volname "MangaDL Installer" \
    --window-size 500 300 \
    --app-drop-link 380 200 \
    "MangaDL.dmg" \
    "dist/MangaDL.app"
```

**Linux — AppImage:**

Use [appimage-builder](https://appimage-builder.readthedocs.io/) for a portable Linux binary.

---

## Build Troubleshooting

<details>
<summary><b>"templates not found" or "static not found" at runtime</b></summary>

**Cause:** PyInstaller didn't bundle the data folders.

**Fix:** Make sure `app.py` resolves paths correctly:

```python
import sys
import os

# At the top of app.py
if getattr(sys, 'frozen', False):
    BASE = sys._MEIPASS  # PyInstaller temp dir
else:
    BASE = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE, 'templates'),
    static_folder=os.path.join(BASE, 'static'),
)
```

</details>

<details>
<summary><b>"No module named X" when running EXE</b></summary>

**Cause:** PyInstaller missed a dependency.

**Fix:** Add it to `collect_hidden_imports()` in `build.py`:

```python
def collect_hidden_imports():
    return [
        ...,
        "your_missing_module",
    ]
```

Then rebuild.

</details>

<details>
<summary><b>EXE starts but immediately closes</b></summary>

**Cause:** Crash on startup (uncaught exception).

**Fix:** Run from terminal to see the error:

```batch
cd dist
MangaDL.exe
```

The console will print the traceback. Common causes:
- Missing data files → fix paths
- Port in use → change port in `app.py`
- Permissions → run as admin

</details>

<details>
<summary><b>Antivirus flags the EXE as malware</b></summary>

**Cause:** PyInstaller binaries are common false positives because malware authors also use it.

**Fixes:**
1. Add the EXE to AV exclusion list
2. Sign with a code-signing certificate ($$$)
3. Submit to AV vendor as false positive
4. Build with `--onedir` instead of `--onefile` (less suspicious)

</details>

<details>
<summary><b>Build is extremely slow</b></summary>

**Causes:**
- First build downloads dependencies — subsequent builds are faster
- Antivirus is scanning every file — temporarily disable real-time protection
- Slow disk — use SSD for the project folder

</details>

<details>
<summary><b>"recursion limit" error during build</b></summary>

**Fix:** Increase Python's recursion limit. Edit `build.py` at the top:

```python
import sys
sys.setrecursionlimit(5000)
```

</details>

<details>
<summary><b>Build succeeds but EXE crashes on Windows 7 / older systems</b></summary>

**Cause:** Built with newer Python that doesn't support older Windows.

**Fix:** Use Python 3.8 (last version supporting Windows 7) for the build.

</details>

<details>
<summary><b>"Failed to execute script" with no further info</b></summary>

**Fix:** Build without `--noconsole` (default in `build.py`) so you can see errors:

```python
# In build.py, ensure this line is NOT present:
# cmd += ["--noconsole"]
```

</details>

<details>
<summary><b>Socket.IO not working in EXE</b></summary>

**Fix:** Make sure these are in `collect_hidden_imports()`:

```python
"engineio.async_drivers.threading",
"engineio.async_drivers.gevent",
"socketio",
"flask_socketio",
```

Already included in the default `build.py`.

</details>

<details>
<summary><b>"PIL/Pillow image format not supported"</b></summary>

**Fix:** Add image plugins explicitly:

```python
"PIL.JpegImagePlugin",
"PIL.PngImagePlugin",
"PIL.WebPImagePlugin",
"PIL.GifImagePlugin",
"PIL.BmpImagePlugin",
```

Already included.

</details>

---

## Advanced: Custom .spec File

For advanced control, generate and edit a `.spec` file:

```bash
pyi-makespec --onefile --name MangaDL app.py
```

This creates `MangaDL.spec`. Edit it, then build with:

```bash
pyinstaller MangaDL.spec
```

Example custom `.spec`:

```python
# MangaDL.spec
block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
    ],
    hiddenimports=[
        'engineio.async_drivers.threading',
        'cloudscraper',
        # ... etc
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy'],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MangaDL',
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon='icon.ico',
)
```

---

## CI/CD Automated Builds

### GitHub Actions

Create `.github/workflows/build.yml`:

```yaml
name: Build Executables

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build:
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller

      - name: Build
        run: python build.py

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: MangaDL-${{ matrix.os }}
          path: dist/*
```

This builds Windows, macOS, and Linux binaries automatically when you push a tag like `v2.0.0`.

---

<div align="center">

### Build Issues?

Open an issue on [GitHub](https://github.com/anibeat495/mangadl/issues) with:
- Your OS and Python version
- Full output of the build command
- Contents of `build/MangaDL/warn-MangaDL.txt`

[← Back to README](README.md)

</div>
