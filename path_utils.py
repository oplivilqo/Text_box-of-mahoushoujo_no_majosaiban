"""路径工具模块 - 处理打包环境下的路径问题"""

import os
import sys


def get_base_path():
    """获取程序的基础路径，支持打包环境和开发环境"""
    if getattr(sys, 'frozen', False):
        # 打包后的可执行文件
        base_path = os.path.dirname(sys.executable)
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return base_path


def get_resource_path(relative_path):
    """获取资源文件的绝对路径，支持打包环境"""
    base_path = get_base_path()
    
    # 在打包环境中，优先从程序所在目录查找
    if getattr(sys, 'frozen', False):
        # 首先尝试程序目录下的资源文件
        program_dir_path = os.path.join(base_path, relative_path)
        if os.path.exists(program_dir_path):
            return program_dir_path
    
    # 开发环境或打包环境未找到资源时，使用基础路径
    resource_path = os.path.join(base_path, relative_path)
    return resource_path


def ensure_path_exists(file_path):
    """确保文件路径的目录存在"""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    return file_path

def get_available_fonts():
    """获取可用的字体列表"""
    project_fonts = []
    
    # 在打包环境中，优先查找程序旁边的assets/fonts文件夹
    # 首先尝试程序目录下的assets/fonts
    base_path = get_base_path()  # 使用get_base_path()而不是__file__
    external_font_dir = os.path.join(base_path, "assets", "fonts")
    
    # 如果外部字体目录存在，优先使用
    if os.path.exists(external_font_dir):
        for file in os.listdir(external_font_dir):
            if file.lower().endswith(('.ttf', '.otf', '.ttc')):
                project_fonts.append(file)  # 只返回字体文件名
    
    # 如果外部目录没有找到字体，再尝试资源路径
    if not project_fonts:
        font_dir = get_resource_path(os.path.join("assets", "fonts"))
        if os.path.exists(font_dir):
            for file in os.listdir(font_dir):
                if file.lower().endswith(('.ttf', '.otf', '.ttc')):
                    project_fonts.append(file)  # 只返回字体文件名
    
    return project_fonts

def is_font_available(font_name: str) -> bool:
    """检查字体是否可用"""
    font_path = os.path.join("assets", "fonts", font_name)
    resolved_font_path = get_resource_path(font_path)
    return os.path.exists(resolved_font_path)