# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 单文件打包配置
# 使用方法: pyinstaller build_onefile.spec

import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# 收集所有资源文件
datas = [
    ('font3.ttf', '.'),
    ('text_fit_draw.py', '.'),
    ('image_fit_paste.py', '.'),
]

# 添加背景文件夹中的所有文件
if os.path.exists('background'):
    for file in os.listdir('background'):
        if file.endswith('.png'):
            datas.append((os.path.join('background', file), 'background'))

# 添加所有角色文件夹
character_folders = [
    'ema', 'hiro', 'sherri', 'hanna', 'anan', 'yuki',
    'meruru', 'noa', 'reia', 'miria', 'nanoka', 'mago', 'alisa', 'coco'
]

for folder in character_folders:
    if os.path.exists(folder):
        for file in os.listdir(folder):
            if file.endswith('.png'):
                datas.append((os.path.join(folder, file), folder))

# 收集 requests 的 SSL 证书（如果使用了emoji功能）
try:
    datas += collect_data_files('certifi')
except:
    pass

# 隐藏导入的模块
hiddenimports = [
    'PIL._tkinter_finder',
    'PIL._imaging',
    'requests',
    'certifi',
    'charset_normalizer',
    'idna',
    'urllib3',
    'win32clipboard',
    'win32gui',
    'win32process',
    'win32api',
    'win32con',
    'pywintypes',
    'keyboard',
    'pyperclip',
]

# 排除不需要的大型库以减小体积
excludes = [
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'tkinter',
    'test',
    'unittest',
    'email',
    'html',
    'http',
    'xml',
    'pydoc',
    'doctest',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='mahosojo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 改为 False 可隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 如果有图标文件，设置为 icon='icon.ico'
)
