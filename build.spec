# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for onefolder build (no console window)

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[('font3.ttf', '.'), ('background', 'background'), ('D:\\user\\document\\Text_box-of-mahoushoujo_no_majosaiban\\alisa', 'alisa'), ('D:\\user\\document\\Text_box-of-mahoushoujo_no_majosaiban\\anan', 'anan'), ('D:\\user\\document\\Text_box-of-mahoushoujo_no_majosaiban\\background', 'background'), ('D:\\user\\document\\Text_box-of-mahoushoujo_no_majosaiban\\coco', 'coco'), ('D:\\user\\document\\Text_box-of-mahoushoujo_no_majosaiban\\ema', 'ema'), ('D:\\user\\document\\Text_box-of-mahoushoujo_no_majosaiban\\hanna', 'hanna'), ('D:\\user\\document\\Text_box-of-mahoushoujo_no_majosaiban\\hiro', 'hiro'), ('D:\\user\\document\\Text_box-of-mahoushoujo_no_majosaiban\\mago', 'mago'), ('D:\\user\\document\\Text_box-of-mahoushoujo_no_majosaiban\\meruru', 'meruru'), ('D:\\user\\document\\Text_box-of-mahoushoujo_no_majosaiban\\miria', 'miria'), ('D:\\user\\document\\Text_box-of-mahoushoujo_no_majosaiban\\nanoka', 'nanoka'), ('D:\\user\\document\\Text_box-of-mahoushoujo_no_majosaiban\\noa', 'noa'), ('D:\\user\\document\\Text_box-of-mahoushoujo_no_majosaiban\\reia', 'reia'), ('D:\\user\\document\\Text_box-of-mahoushoujo_no_majosaiban\\sherri', 'sherri'), ('D:\\user\\document\\Text_box-of-mahoushoujo_no_majosaiban\\yuki', 'yuki')],
    hiddenimports=['keyboard', 'pyperclip', 'win32clipboard'],
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
    name='gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name='gui',
)
