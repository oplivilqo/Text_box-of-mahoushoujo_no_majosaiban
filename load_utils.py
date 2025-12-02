"""文件加载工具"""
import os
import threading
from PIL import ImageFont, Image

from path_utils import get_resource_path

# 字体缓存
_font_cache = {}

# 图片缓存
_background_cache = {}  # 背景图片缓存（长期缓存）
_character_cache = {}   # 角色图片缓存（可释放）
_general_image_cache = {}  # 通用图片缓存

# 预加载状态
_preload_status = {
    "backgrounds_loaded": False,
    "characters_loaded": False,
    "total_backgrounds": 0,
    "total_characters": 0,
    "loaded_backgrounds": 0,
    "loaded_characters": 0
}

def preload_all_images_async(base_path: str, mahoshojo: dict, callback=None):
    """异步预加载所有背景和角色图片到缓存"""
    def preload_task():
        try:
            # 预加载背景图片
            _preload_backgrounds(base_path)
            
            # 预加载角色图片
            _preload_characters(base_path, mahoshojo)
            
            # 通知预加载完成
            if callback:
                callback(True, "预加载完成")
        except Exception as e:
            if callback:
                callback(False, f"预加载失败: {e}")
    
    # 在后台线程中执行预加载
    preload_thread = threading.Thread(target=preload_task, daemon=True)
    preload_thread.start()

def _preload_backgrounds(base_path: str):
    """预加载所有背景图片"""
    # 使用get_resource_path获取正确的资源路径，支持打包环境
    background_dir = get_resource_path(os.path.join("assets", "background"))
    if not os.path.exists(background_dir):
        print(f"警告：背景图片目录不存在: {background_dir}")
        # 即使目录不存在，也要标记为已完成，避免卡在0%
        _preload_status["backgrounds_loaded"] = True
        _preload_status["total_backgrounds"] = 0
        _preload_status["loaded_backgrounds"] = 0
        return
    
    # 获取所有背景图片文件
    background_files = [f for f in os.listdir(background_dir) if f.endswith('.png')]
    _preload_status["total_backgrounds"] = len(background_files)
    _preload_status["loaded_backgrounds"] = 0
    
    for bg_file in background_files:
        try:
            bg_path = os.path.join(background_dir, bg_file)
            # 使用安全加载函数，这会自动缓存图片
            load_background_safe(bg_path)
            _preload_status["loaded_backgrounds"] += 1
        except Exception as e:
            print(f"预加载背景图片失败 {bg_file}: {e}")
    
    _preload_status["backgrounds_loaded"] = True

def _preload_characters(base_path: str, mahoshojo: dict):
    """预加载所有角色图片"""
    if not mahoshojo:
        _preload_status["characters_loaded"] = True
        _preload_status["total_characters"] = 0
        _preload_status["loaded_characters"] = 0
        return
    
    # 使用get_resource_path获取正确的资源路径，支持打包环境
    chara_dir = get_resource_path(os.path.join("assets", "chara"))
    if not os.path.exists(chara_dir):
        print(f"警告：角色图片目录不存在: {chara_dir}")
        # 即使目录不存在，也要标记为已完成，避免卡在0%
        _preload_status["characters_loaded"] = True
        _preload_status["total_characters"] = 0
        _preload_status["loaded_characters"] = 0
        return
    
    total_characters = 0
    
    # 计算总角色图片数量
    for character_name in mahoshojo.keys():
        character_dir = os.path.join(chara_dir, character_name)
        if os.path.exists(character_dir):
            emotion_count = mahoshojo[character_name].get("emotion_count", 0)
            total_characters += emotion_count
    
    _preload_status["total_characters"] = total_characters
    _preload_status["loaded_characters"] = 0
    
    # 预加载每个角色的每个表情图片
    for character_name in mahoshojo.keys():
        character_dir = os.path.join(chara_dir, character_name)
        if not os.path.exists(character_dir):
            continue
            
        emotion_count = mahoshojo[character_name].get("emotion_count", 0)
        for emotion_index in range(1, emotion_count + 1):
            try:
                chara_path = os.path.join(character_dir, f"{character_name} ({emotion_index}).png")
                # 使用安全加载函数，这会自动缓存图片
                load_character_safe(chara_path)
                _preload_status["loaded_characters"] += 1
            except Exception as e:
                print(f"预加载角色图片失败 {character_name} 表情{emotion_index}: {e}")
    
    _preload_status["characters_loaded"] = True

def get_preload_progress():
    """获取预加载进度"""
    total_items = _preload_status["total_backgrounds"] + _preload_status["total_characters"]
    loaded_items = _preload_status["loaded_backgrounds"] + _preload_status["loaded_characters"]
    
    if total_items == 0:
        # 如果没有可加载的项目，直接返回100%完成
        return 1.0
    
    return loaded_items / total_items

def get_preload_status():
    """获取预加载状态"""
    return _preload_status.copy()

def is_preloading_complete():
    """检查预加载是否完成"""
    return _preload_status["backgrounds_loaded"] and _preload_status["characters_loaded"]


#缓存字体
def load_font_cached(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    """使用字体名称加载字体，支持打包环境"""
    cache_key = f"{font_name}_{size}"
    if cache_key not in _font_cache:
        # 构建字体路径
        font_path = os.path.join("assets", "fonts", font_name)
        resolved_font_path = get_resource_path(font_path)
        
        if os.path.exists(resolved_font_path):
            _font_cache[cache_key] = ImageFont.truetype(resolved_font_path, size=size)
        else:
            # 如果字体文件不存在，尝试使用默认字体
            default_font_path = get_resource_path(os.path.join("assets", "fonts", "font3.ttf"))
            if os.path.exists(default_font_path):
                _font_cache[cache_key] = ImageFont.truetype(default_font_path, size=size)
                print(f"警告：字体文件不存在，使用默认字体: {font_name}")
            else:
                # 如果默认字体也不存在，使用系统默认字体
                _font_cache[cache_key] = ImageFont.load_default()
                print(f"警告：字体文件不存在，使用系统默认字体: {font_name}")
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
    
    if cache_type in ("font", "all"):
        _font_cache.clear()
    if cache_type in ("background", "all"):
        _background_cache.clear()
    if cache_type in ("character", "all"):
        _character_cache.clear()
    if cache_type in ("image", "all"):
        _general_image_cache.clear()