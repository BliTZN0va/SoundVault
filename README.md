# SoundVault

A desktop tag library manager for music and sound effects. Organize your audio files with tags, episodes, notes, and a built-in player.


## Features

- **Tag-based organization** — Assign custom tags with colors to categorize your audio files
- **Episode tracking** — Group tracks by episode/project
- **Built-in audio player** — Play, pause, seek, and control volume
- **Drag & drop** — Drag tracks from the app directly into your DAW or editor
- **Star & use tracking** — Mark favorites and track which files you've already used
- **Auto-detect** — Automatically scans your music folder for new audio files
- **File browser** — Browse and filter by folder structure
- **Multiple themes** — Dark, Light, Neon, Cyberpunk, Ocean, Sunset
- **Custom backgrounds** — Solid colors, gradient presets, or your own background image
- **Glass UI** — Frosted glass effect with adjustable blur and opacity
 
## Tag_Colors

- **ambient**    #27ae60
- **chill**      #16a085
- **cinematic**  #8e44ad
- **comedy**     #f39c12
- **cuts**       #7f8c8d
- **dramatic**   #c0392b
- **emotional**  #e67e22
- **epic**       #d35400
- **fantasy**    #1abc9c
- **horror**     #2c3e50
- **mystery**    #2980b9
- **pvp**        #c0392b
- **run**        #e67e22
- **sad**        #7f8c8d
- **sfx**        #95a5a6
- **tension**    #8e44ad
- **trailer**    #3498db
- **trap**       #9b59b6
- **uplifting**  #2ecc71
- **voice**      #f1c40f

## Download

Grab the latest installer from the [Releases](https://github.com/BliTZN0va/SoundVault/releases) page.

**Requirements:** Windows 10 or later. No additional software needed.

## Usage

1. Launch SoundVault
2. Set your music folder path in Settings (or let it auto-detect from the `music` folder)
3. Click **Scan** to find audio files, or **+ Add** to manually add tracks
4. Assign tags, episodes, and notes to organize your library
5. Click ▶ to play a track, or drag it into your editor

### Keyboard Shortcuts

| Key | Action |
|---|---|
| `Space` | Play / Pause |
| `J` | Previous track |
| `K` | Next track |
| `N` | Add new track |
| `Ctrl+F` | Focus search |
| `←` / `→` | Rewind / Forward 5s |
| `↑` / `↓` | Volume up / down |
| `Esc` | Close modals |

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

### Build .exe

```bash
pip install pyinstaller
pyinstaller SoundVault.spec
```

The executable will be in `dist/SoundVault.exe`.

### Build Installer (Setup .exe)

```bash
python -m PyInstaller installer/installer.spec --distpath dist
```

The installer will be at `dist/SoundVault_Setup.exe`. It bundles `SoundVault.exe` and installs it with desktop shortcuts and uninstall support.

Or run `build_release.bat` to build everything in one step.

## Project Structure

```
SoundVault/
├── main.py              # App entry point (pywebview window)
├── backend.py           # Flask server with REST API
├── config.json          # App configuration
├── requirements.txt     # Python dependencies
├── icon.ico             # App icon
├── SoundVault.spec      # PyInstaller build config
├── public/
│   └── index.html       # Frontend (HTML + CSS + JS)
├── database/
│   └── data.json        # Track database
├── music/               # Default music folder
├── installer/
│   ├── installer.py     # Python installer script
│   └── installer.spec   # PyInstaller config for installer
└── dist/                # Built executables output
```

## Creating Your Own Version

Fork the repo and modify:

- **`public/index.html`** — The entire UI is here. Change colors, layout, or add features.
- **`backend.py`** — Modify the API (add new endpoints, change metadata extraction).
- **`config.json`** — Set default configuration values.
- **`icon.ico`** — Replace with your own icon (256x256 recommended).

The `requirements.txt` keeps dependencies minimal: Flask, pywebview, and watchdog. The frontend is a single-file HTML app — no build tools needed.

## License

MIT