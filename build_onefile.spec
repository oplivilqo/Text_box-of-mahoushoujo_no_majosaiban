# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 单文件打包配置 - 修复版本
# 使用方法: pyinstaller build_onefile.spec

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

def collect_folder_files(folder_path, dest_folder):
    """安全地收集文件夹中的所有文件"""
    files = []
    try:
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            for root, dirs, filenames in os.walk(folder_path):
                for filename in filenames:
                    full_path = os.path.join(root, filename)
                    # 计算相对路径，用于保持目录结构
                    rel_path = os.path.relpath(root, folder_path)
                    if rel_path == '.':
                        final_dest = dest_folder
                    else:
                        final_dest = os.path.join(dest_folder, rel_path)
                    files.append((full_path, final_dest))
    except Exception:
        pass
    return files

# 收集所有资源文件
datas = []

# 添加核心Python文件
core_files = [
    'core.py',
    'gui.py', 
    'config.py',
    'clipboard_utils.py',
    'image_processor.py',
    'text_fit_draw.py',
    'image_fit_paste.py'
]

for file in core_files:
    if os.path.exists(file):
        datas.append((file, '.'))

# 添加字体文件
datas.extend(collect_files('assets/fonts/*.ttf', 'assets/fonts'))
datas.extend(collect_files('assets/fonts/*.otf', 'assets/fonts'))

# 添加配置文件 - 使用具体文件而不是通配符
config_files = [
    'config/character_meta.json',
    'config/keymap.json',
    'config/process_whitelist.json',
    'config/text_config.json'
]

for config_file in config_files:
    if os.path.exists(config_file):
        datas.append((config_file, 'config'))

# 添加背景资源
datas.extend(collect_folder_files('assets/background', 'assets/background'))

# 添加角色资源
character_base_path = 'assets/chara'
if os.path.exists(character_base_path):
    for char_folder in os.listdir(character_base_path):
        char_path = os.path.join(character_base_path, char_folder)
        if os.path.isdir(char_path):
            dest_path = os.path.join('assets/chara', char_folder)
            datas.extend(collect_folder_files(char_path, dest_path))

# 收集证书文件
try:
    certifi_data = collect_data_files('certifi')
    datas.extend(certifi_data)
except:
    pass

# 隐藏导入的模块
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
    'win32gui',
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
]

# 尝试收集一些可能被动态导入的模块
try:
    hiddenimports.extend(collect_submodules('pynput'))
except:
    pass

# 排除不需要的库
excludes = [
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'test',
    'unittest',
    'email',
    'pydoc',
    'doctest',
    'setuptools',
    'pip',
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
    name='mahoshojo_textbox',
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