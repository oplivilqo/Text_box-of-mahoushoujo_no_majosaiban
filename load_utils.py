"""文件加载工具"""
from path_utils import get_resource_path
from PIL import ImageFont, Image
import os
# import yaml

# 字体缓存
_font_cache = {}

# 图片缓存
_background_cache = {}  # 背景图片缓存（长期缓存）
_character_cache = {}   # 角色图片缓存（可释放）
_general_image_cache = {}  # 通用图片缓存

#缓存字体
def load_font_cached(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    cache_key = f"{font_path}_{size}"
    if cache_key not in _font_cache:
        if font_path and os.path.exists(font_path):
            _font_cache[cache_key] = ImageFont.truetype(font_path, size=size)
        else:
            # logger.exception("字体文件不存在")
            raise FileNotFoundError("字体文件不存在")
    return _font_cache[cache_key]

# 缓存背景图片加载（长期缓存）
def load_background_cached(image_path: str) -> Image.Image:
    """缓存加载背景图片，支持透明通道"""
    cache_key = image_path
    if cache_key not in _background_cache:
        if image_path and os.path.exists(image_path):
            _background_cache[cache_key] = Image.open(image_path).convert("RGBA")
        else:
            raise FileNotFoundError(f"背景图片文件不存在: {image_path}")
    return _background_cache[cache_key].copy()

# 缓存角色图片加载（可释放）
def load_character_cached(image_path: str) -> Image.Image:
    """缓存加载角色图片，支持透明通道"""
    cache_key = image_path
    if cache_key not in _character_cache:
        if image_path and os.path.exists(image_path):
            _character_cache[cache_key] = Image.open(image_path).convert("RGBA")
        else:
            raise FileNotFoundError(f"角色图片文件不存在: {image_path}")
    return _character_cache[cache_key].copy()

# 通用图片缓存
def load_image_cached(image_path: str) -> Image.Image:
    """通用图片缓存加载，支持透明通道"""
    cache_key = image_path
    if cache_key not in _general_image_cache:
        if image_path and os.path.exists(image_path):
            _general_image_cache[cache_key] = Image.open(image_path).convert("RGBA")
        else:
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
    return _general_image_cache[cache_key].copy()

# 安全加载背景图片（文件不存在时返回默认值）
def load_background_safe(image_path: str, default_size: tuple = (800, 600), default_color: tuple = (100, 100, 200)) -> Image.Image:
    """安全加载背景图片，文件不存在时返回默认图片"""
    try:
        return load_background_cached(image_path)
    except FileNotFoundError:
        # 创建默认图片
        return Image.new("RGBA", default_size, default_color)

# 安全加载角色图片（文件不存在时返回默认值）
def load_character_safe(image_path: str, default_size: tuple = (800, 600), default_color: tuple = (0, 0, 0, 0)) -> Image.Image:
    """安全加载角色图片，文件不存在时返回默认图片"""
    try:
        return load_character_cached(image_path)
    except FileNotFoundError:
        # 创建默认透明图片
        return Image.new("RGBA", default_size, default_color)

# 安全加载图片
def load_image_safe(image_path: str, default_size: tuple = (800, 600), default_color: tuple = (100, 100, 200)) -> Image.Image:
    """安全加载图片，文件不存在时返回默认图片"""
    try:
        return load_image_cached(image_path)
    except FileNotFoundError:
        # 创建默认图片
        return Image.new("RGBA", default_size, default_color)

# 获取资源路径并加载图片
def load_resource_image(relative_path: str) -> Image.Image:
    """获取资源路径并加载图片"""
    image_path = get_resource_path(relative_path)
    return load_image_cached(image_path)

# 清理所有缓存
def clear_all_cache():
    """清理所有缓存以释放内存"""
    global _font_cache, _background_cache, _character_cache, _general_image_cache, _config_cache
    _font_cache.clear()
    _background_cache.clear()
    _character_cache.clear()
    _general_image_cache.clear()
    _config_cache.clear()

# 清理角色图片缓存（切换角色时调用）
def clear_character_cache():
    """清理角色图片缓存以释放内存"""
    global _character_cache
    _character_cache.clear()

# 清理特定类型的缓存
def clear_cache(cache_type: str = "all"):
    """清理特定类型的缓存"""
    global _font_cache, _background_cache, _character_cache, _general_image_cache
    
    if cache_type == "font" or cache_type == "all":
        _font_cache.clear()
    if cache_type == "background" or cache_type == "all":
        _background_cache.clear()
    if cache_type == "character" or cache_type == "all":
        _character_cache.clear()
    if cache_type == "image" or cache_type == "all":
        _general_image_cache.clear()