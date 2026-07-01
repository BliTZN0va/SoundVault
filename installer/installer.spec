# -*- mode: python ; coding: utf-8 -*-
# Build the installer: pyinstaller installer/installer.spec --distpath dist

a = Analysis(
    ['installer.py'],
    pathex=[],
    binaries=[],
    datas=[('../dist/SoundVault.exe', '.'), ('../icon.ico', '.')],
    hiddenimports=['win32com'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'PIL', 'Pygments'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SoundVault_Setup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['../icon.ico'],
)
