# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 单文件打包配置 - 优化版本
# 使用方法: pyinstaller build_onefile_optimized.spec

import os
import glob
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

def collect_files(pattern, dest_folder='.'):
    """安全地收集文件，如果文件不存在则跳过"""
    files = []
    try:
        matches = glob.glob(pattern, recursive=True)
        for match in matches:
            if os.path.isfile(match):
                files.append((match, dest_folder))
    except Exception:
        pass
    return files

# 收集所有资源文件
datas = []

# 添加核心Python文件 - 不包含tui.py
core_files = [
    'main.py',
    'core.py',
    'gui.py', 
    'config.py',
    'clipboard_utils.py',
    'image_processor.py',
    'text_fit_draw.py',
    'image_fit_paste.py',
    'ai_client.py',
    'sentiment_analyzer.py',
    'gui_components.py',
    'gui_hotkeys.py',
    'gui_settings.py',
    'path_utils.py',
    'load_utils.py'
]

for file in core_files:
    if os.path.exists(file):
        datas.append((file, '.'))


# 收集证书文件
try:
    certifi_data = collect_data_files('certifi')
    datas.extend(certifi_data)
except:
    pass

# 隐藏导入的模块 - 只包含必要的模块
hiddenimports = [
    # PIL相关
    'PIL._tkinter_finder',
    'PIL._imaging',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL.ImageOps',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    
    # GUI相关
    'tkinter',
    'tkinter.ttk',
    
    # 网络请求
    'openai',
    'requests',
    'requests.utils',
    'requests.auth',
    'requests.models',
    'certifi',
    'charset_normalizer',
    'idna',
    'urllib3',
    'urllib3.util',
    'urllib3.contrib',
    
    # Windows API
    'win32clipboard',
    # 'win32gui',
    'win32process',
    'win32api',
    'win32con',
    'pywintypes',
    
    # 键盘和输入
    'keyboard',
    'pynput',
    'pynput.keyboard',
    
    # 系统工具
    'psutil',
    
    # 剪贴板
    'pyperclip',
    'pyclip',
    
    # 其他必要模块
    'yaml'
]

# 尝试收集一些可能被动态导入的模块
try:
    hiddenimports.extend(collect_submodules('pynput'))
except:
    pass

# 排除不需要的库 - 增加更多排除项以减小体积
excludes = [
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'test',
    'unittest',
    'pydoc',
    'doctest',
    'setuptools',
    'pip',
    'jupyter',
    'IPython',
    'notebook',
    'rich',
    'textual',  # 不使用的TUI库
    'pytest',
    'sphinx',
    'bz2',
    'lzma',
    'sqlite3',
    'tkinter.test',
    'tkinter.ttk.test'
]

a = Analysis(
    ['main.py'],
    pathex=[os.getcwd()],
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
    name='魔裁文本框',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)