# SoundVault ![Version](https://img.shields.io/badge/version-1.0.5-blue)

Audio asset manager for content creators — catalog, tag, preview, and track usage of SFX, music, and voice clips across projects. Ships as a native desktop app for Windows, macOS, and Linux.

## Features

### Library Management
- **Tag-based organization** — Assign custom tags with live color pickers to categorize audio files
- **Episode tracking** — Group tracks by episode, scene, or project
- **Star & use tracking** — Mark favorites and track which files you've already used to avoid repeats
- **Bulk operations** — Select multiple tracks to tag, assign episodes, mark used/unused, or delete in one action
- **Search & filter** — Search by title/artist/tags/notes, filter by tag (with live tag search), episode, folder, or usage status
- **File browser** — Browse and filter by folder structure
- **Import/Export database** — Backup or transfer your library between machines
- **Auto-detect** — Automatically scans your music folder for new audio files

### Audio Player
- **Built-in player** — Play, pause, seek, volume control, mute
- **Drag & drop** — Drag tracks directly into your DAW, video editor, or file explorer (`text/uri-list`, `text/plain`, and `DownloadURL` formats)
- **Progress bar** — Click to seek, keyboard shortcuts for fine control

### Appearance
- **12 themes** — Dark, Light, Neon, Cyberpunk, Ocean, Sunset, Midnight, Forest, Coffee, Royal, Candy, Monochrome
- **Theme preview cards** — See each theme at a glance before applying
- **Custom accent color** — Pick any color, overrides theme default
- **Font size** — Adjust from 10px to 18px
- **Animation speed** — Slow down or speed up transitions (0x to 2x)
- **Compact mode** — Tighter spacing for more content on screen
- **Glass UI** — Frosted glass effect with adjustable blur (2-40px) and opacity (20-90%)
- **Backgrounds** — Gradient presets (7), solid colors, or custom background image with opacity control
- **Reset Appearance** — One-click restore all appearance defaults

## Download

Grab the latest release from the [Releases](https://github.com/BliTZN0va/SoundVault/releases) page.

| Platform | Format |
|----------|--------|
| Windows | `.exe` installer, portable `.exe`, `.msi` |
| macOS | `.app` bundle, `.dmg`, `.pkg` |
| Linux | `.AppImage`, `.deb`, `.rpm` |

**Requirements:** Windows 10+, macOS 11+, or Linux (glibc 2.28+). No additional runtime needed.

## Usage

1. Launch SoundVault
2. Set your music folder path in Settings (or let it auto-detect from the `music` folder)
3. Click **Scan** to find audio files, or **+ Add** to manually add tracks
4. Assign tags, episodes, and notes to organize your library
5. Click ▶ to play a track, or drag it into your editor
6. Use **Select** mode for bulk tagging, episode assignment, or deletion

### Keyboard Shortcuts

| Key | Action |
|---|---|
| `Space` | Play / Pause |
| `S` | Toggle select mode |
| `J` / `K` | Previous / Next track |
| `N` | Add new track |
| `Ctrl+F` | Focus search |
| `←` / `→` | Rewind / Forward 5s |
| `↑` / `↓` | Volume up / down |
| `?` | Show shortcuts |
| `Esc` | Close modals |

### Batch Operations

Press **S** or click the **Select** button to enter selection mode. Each track gets a checkbox — select multiple tracks, then use the batch bar to:
- Add tags to all selected
- Assign episodes
- Mark as used / unused
- Delete permanently

## Building from Source

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
git clone https://github.com/BliTZN0va/SoundVault.git
cd SoundVault
pip install -r requirements.txt
```

### Run in Development

```bash
python main.py
```

### Build Executable

```bash
pip install pyinstaller
pyinstaller SoundVault.spec --noconfirm
```

The executable will be in `dist/SoundVault.exe` (Windows), `dist/SoundVault.app` (macOS), or `dist/SoundVault` (Linux).

### Build Installers

See `scripts/` for platform-specific build scripts:
- **Windows:** `scripts/build-windows.ps1` — builds `.exe` + NSIS installer + MSI
- **macOS:** `scripts/build-macos.sh` — builds `.app` + `.dmg`
- **Linux:** `scripts/build-linux.sh` — builds `.AppImage`

Or use the all-in-one: `scripts/build-all.ps1` / `scripts/build-all.sh`

## Project Structure

```
SoundVault/
├── main.py              # App entry point (pywebview window)
├── backend.py           # Flask server with REST API (26 endpoints)
├── config.json          # App configuration
├── VERSION              # Current version
├── requirements.txt     # Python dependencies
├── icon.ico             # App icon
├── SoundVault.spec      # PyInstaller build config
├── public/
│   └── index.html       # Frontend (HTML + CSS + JS, single file)
├── database/
│   ├── data.json        # Track database
│   └── backups/         # Auto-backups
├── music/               # Default music folder
├── installer/           # NSIS (.nsi) and WiX (.wxs) installer configs
├── scripts/             # Cross-platform build scripts
└── .github/workflows/   # CI: build + weekly release pipeline
```

## Technical Stack

- **Backend:** Python / Flask REST API
- **Frontend:** Single-file HTML + CSS + JavaScript (no frameworks, no build tools)
- **Desktop:** pywebview (native webview window)
- **File watching:** watchdog (auto-detect new files)
- **Packaging:** PyInstaller (cross-platform executable)

## License

MIT