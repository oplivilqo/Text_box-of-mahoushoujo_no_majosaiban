# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules
import os

datas = []
binaries = []
hiddenimports = ['PIL._tkinter_finder', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont', 'win32clipboard', 'win32con', 'win32api', 'win32gui', 'win32process', 'pywintypes', 'keyboard', 'pyperclip', 'psutil']

# Include pilmoji and emoji packages' data
_tmp = collect_all('pilmoji')
datas += _tmp[0]; binaries += _tmp[1]; hiddenimports += _tmp[2]
_tmp = collect_all('emoji')
datas += _tmp[0]; binaries += _tmp[1]; hiddenimports += _tmp[2]

# Ensure PyYAML submodules are included
hiddenimports += collect_submodules('yaml')

# NOTE: We intentionally DO NOT bundle external resources (assets/, config/).
# They must be placed next to the built executable and will be loaded at runtime.


a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MagicGirlTextBox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='MagicGirlTextBox',
)
