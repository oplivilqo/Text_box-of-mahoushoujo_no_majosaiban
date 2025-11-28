# filename: text_fit_draw.py
from io import BytesIO
from typing import Tuple, Union, Literal
from PIL import Image, ImageDraw, ImageFont
import os

Align = Literal["left", "center", "right"]
VAlign = Literal["top", "middle", "bottom"]

# 字体缓存字典
FONT_CACHE = {}
MAX_CACHE_SIZE = 2  # 最多缓存2个字体文件

IMAGE_SETTINGS = {
    "max_width": 1200,
    "max_height": 800,
    "quality": 65,
    "resize_ratio": 0.7
}

def _get_cached_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    """获取缓存的字体，如果不存在则加载并缓存"""
    cache_key = (font_path, size)
    
    # 如果字体已在缓存中，直接返回
    if cache_key in FONT_CACHE:
        return FONT_CACHE[cache_key]
    
    # 加载新字体
    try:
        font = ImageFont.truetype(font_path, size=size)
    except Exception as e:
        raise e
    
    # 如果缓存已满，移除最旧的一个（按插入顺序）
    if len(FONT_CACHE) >= MAX_CACHE_SIZE:
        # 移除第一个插入的键
        oldest_key = next(iter(FONT_CACHE))
        del FONT_CACHE[oldest_key]
    
    # 缓存新字体
    FONT_CACHE[cache_key] = font
    return font

def compress_image(image: Image.Image) -> Image.Image:
    """压缩图像大小"""
    width, height = image.size
    new_width = int(width * IMAGE_SETTINGS["resize_ratio"])
    new_height = int(height * IMAGE_SETTINGS["resize_ratio"])
    
    if new_width > IMAGE_SETTINGS["max_width"]:
        ratio = IMAGE_SETTINGS["max_width"] / new_width
        new_width, new_height = IMAGE_SETTINGS["max_width"], int(new_height * ratio)
    
    if new_height > IMAGE_SETTINGS["max_height"]:
        ratio = IMAGE_SETTINGS["max_height"] / new_height
        new_height, new_width = IMAGE_SETTINGS["max_height"], int(new_width * ratio)
    
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

def draw_text_auto(
    image_source: Union[str, Image.Image],
    top_left: Tuple[int, int],
    bottom_right: Tuple[int, int],
    text: str,
    color: Tuple[int, int, int] = (0, 0, 0),
    max_font_height: int | None = None,
    font_path: str | None = None,
    align: Align = "center",
    valign: VAlign = "middle",
    line_spacing: float = 0.15,
    bracket_color: Tuple[int, int, int] = (137,177,251),
    image_overlay: Union[str, Image.Image, None] = None,
    role_name: str = "unknown",
    text_configs_dict: dict = None,
    base_path: str = None,
    overlay_offset: Tuple[int, int] = (0, 0),
) -> bytes:
    """
    在指定矩形内自适应字号绘制文本；
    中括号及括号内文字使用 bracket_color。
    """

    # --- 1. 打开图像 ---
    if isinstance(image_source, Image.Image):
        img = image_source.copy()
    else:
        img = Image.open(image_source).convert("RGBA")
    
    # 创建绘图对象
    draw = ImageDraw.Draw(img)

    # 处理覆盖图层
    if image_overlay is not None:
        if isinstance(image_overlay, Image.Image):
            img_overlay = image_overlay.copy()
        else:
            img_overlay = Image.open(image_overlay).convert("RGBA") if os.path.isfile(image_overlay) else None

    x1, y1 = top_left
    x2, y2 = bottom_right
    if not (x2 > x1 and y2 > y1):
        raise ValueError("无效的文字区域。")
    region_w, region_h = x2 - x1, y2 - y1

    # --- 2. 字体加载 ---
    def _load_font(size: int) -> ImageFont.FreeTypeFont:
        if font_path and os.path.exists(font_path):
            try:
                return _get_cached_font(font_path, size)
            except Exception as e:
                print(f"加载指定字体失败 {font_path}: {e}")
        
        font_files = ["arial.ttf", "DejaVuSans.ttf"]
        if base_path:
            font_dir = os.path.join(base_path, 'assets', 'fonts')
            project_fonts = ["font3.ttf"] + font_files
            for font_file in project_fonts:
                try_path = os.path.join(font_dir, font_file)
                if os.path.exists(try_path):
                    try:
                        return _get_cached_font(try_path, size)
                    except Exception:
                        continue
        
        for font_file in font_files:
            try:
                return _get_cached_font(font_file, size)
            except Exception:
                continue
        
        try:
            return ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()

    # --- 3. 文本包行 ---
    def wrap_lines(txt: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
        lines: list[str] = []
        
        # 预计算常用字符宽度缓存
        char_width_cache = {}
        
        def get_text_width(text: str) -> int:
            """带缓存的文本宽度计算"""
            return int(draw.textlength(text, font=font))
        
        def split_long_word(word: str, max_width: int) -> list[str]:
            """分割过长的单词"""
            parts = []
            current_part = ""
            
            for char in word:
                # 使用缓存避免重复计算字符宽度
                if char not in char_width_cache:
                    char_width_cache[char] = get_text_width(char)
                
                char_width = char_width_cache[char]
                test_part = current_part + char
                test_width = get_text_width(test_part) if len(test_part) > 1 else (
                    get_text_width(current_part) + char_width if current_part else char_width
                )
                
                if test_width <= max_width:
                    current_part = test_part
                else:
                    if current_part:
                        parts.append(current_part)
                    current_part = char
                    
                    # 如果单个字符就超宽，强制换行
                    if char_width > max_width:
                        parts.append(current_part)
                        current_part = ""
            
            if current_part:
                parts.append(current_part)
            return parts

        for para in txt.splitlines() or [""]:
            if not para.strip():  # 空行处理
                lines.append("")
                continue
                
            has_space = " " in para
            
            if has_space:
                # 对于有空格的文本（英文或中英混合）
                words = para.split(" ")
                current_line = ""
                
                for i, word in enumerate(words):
                    # 测试将单词加入当前行
                    test_line = current_line + (" " + word if current_line else word)
                    test_width = get_text_width(test_line)
                    
                    if test_width <= max_w:
                        current_line = test_line
                    else:
                        # 当前行已经有内容，先保存当前行
                        if current_line:
                            lines.append(current_line)
                        
                        # 检查单词本身是否超宽
                        word_width = get_text_width(word)
                        if word_width <= max_w:
                            current_line = word
                        else:
                            # 单词超宽，需要分割
                            word_parts = split_long_word(word, max_w)
                            if word_parts:
                                current_line = word_parts[0]
                                # 将剩余部分添加到后续行
                                for part in word_parts[1:]:
                                    lines.append(current_line)
                                    current_line = part
                            else:
                                current_line = ""
                
                # 添加最后一行
                if current_line:
                    lines.append(current_line)
            else:
                # 对于没有空格的文本（如纯中文）
                current_line = ""
                
                for char in para:
                    test_line = current_line + char
                    test_width = get_text_width(test_line)
                    
                    if test_width <= max_w:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = char
                
                if current_line:
                    lines.append(current_line)
        
        return lines

    # --- 4. 测量 ---
    def measure_block(lines: list[str], font: ImageFont.FreeTypeFont) -> tuple[int, int, int]:
        try:
            ascent, descent = font.getmetrics()
            line_h = int((ascent + descent) * (1 + line_spacing))
        except:
            line_h = int(font.size * (1 + line_spacing))
        
        max_w = 0
        for ln in lines:
            max_w = max(max_w, int(draw.textlength(ln, font=font)))
        total_h = max(line_h * max(1, len(lines)), 1)
        return max_w, total_h, line_h

    # --- 5. 搜索最大字号 ---
    hi = min(region_h, max_font_height) if max_font_height else region_h
    lo, best_size, best_lines, best_line_h, best_block_h = 1, 0, [], 0, 0

    while lo <= hi:
        mid = (lo + hi) // 2
        font = _load_font(mid)
        lines = wrap_lines(text, font, region_w)
        w, h, lh = measure_block(lines, font)
        if w <= region_w and h <= region_h:
            best_size, best_lines, best_line_h, best_block_h = mid, lines, lh, h
            lo = mid + 1
        else:
            hi = mid - 1

    if best_size == 0:
        font = _load_font(1)
        best_lines = wrap_lines(text, font, region_w)
        _, best_block_h, best_line_h = 0, 1, 1
        best_size = 1
    else:
        font = _load_font(best_size)

    # --- 6. 解析着色片段 ---
    def parse_color_segments(s: str, in_bracket: bool) -> Tuple[list[tuple[str, Tuple[int, int, int]]], bool]:
        segs: list[tuple[str, Tuple[int, int, int]]] = []
        buf = ""
        for ch in s:
            if ch == "[" or ch == "【":
                if buf:
                    segs.append((buf, bracket_color if in_bracket else color))
                    buf = ""
                segs.append((ch, bracket_color))
                in_bracket = True
            elif ch == "]" or ch == "】":
                if buf:
                    segs.append((buf, bracket_color))
                    buf = ""
                segs.append((ch, bracket_color))
                in_bracket = False
            else:
                buf += ch
        if buf:
            segs.append((buf, bracket_color if in_bracket else color))
        return segs, in_bracket

    # --- 7. 垂直对齐 ---
    if valign == "top":
        y_start = y1
    elif valign == "middle":
        y_start = y1 + (region_h - best_block_h) // 2
    else:
        y_start = y2 - best_block_h

    # --- 8. 绘制 ---
    y = y_start
    in_bracket = False
    for ln in best_lines:
        line_w = int(draw.textlength(ln, font=font))
        if align == "left":
            x = x1
        elif align == "center":
            x = x1 + (region_w - line_w) // 2
        else:
            x = x2 - line_w
        segments, in_bracket = parse_color_segments(ln, in_bracket)
        for seg_text, seg_color in segments:
            if seg_text:
                # 绘制文字阴影
                draw.text((x+2, y+2), seg_text, font=font, fill=(0, 0, 0, 128))
                # 绘制主文字
                draw.text((x, y), seg_text, font=font, fill=seg_color)
                x += int(draw.textlength(seg_text, font=font))
        y += best_line_h
        if y - y_start > region_h:
            break

    # 覆盖置顶图层（如果有）
    if image_overlay is not None and img_overlay is not None:
        offset_x, offset_y = overlay_offset
        img.paste(img_overlay, (offset_x, offset_y), img_overlay)
    elif image_overlay is not None and img_overlay is None:
        print("Warning: overlay image is not exist.")

    # 自动在图片上写角色专属文字
    if text_configs_dict and role_name in text_configs_dict:
        shadow_offset = (2, 2)
        shadow_color = (0, 0, 0)
        
        for config in text_configs_dict[role_name]:
            text = config["text"]
            position = tuple(config["position"])
            font_color = tuple(config["font_color"])
            font_size = config["font_size"]
        
            if base_path:
                font_dir = os.path.join(base_path, 'assets', 'fonts')
            else:
                font_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'fonts')
            
            font_files = ["font3.ttf", "arial.ttf", "DejaVuSans.ttf"]
            role_font = None
            
            for font_file in font_files:
                try_path = os.path.join(font_dir, font_file)
                if os.path.exists(try_path):
                    try:
                        role_font = _get_cached_font(try_path, font_size)
                        break
                    except Exception as e:
                        print(f"加载字体 {try_path} 失败: {e}")
                        continue
            
            if role_font is None:
                try:
                    role_font = ImageFont.load_default()
                except:
                    print("无法加载任何字体，跳过角色专属文字绘制")
                    continue
            
            # 绘制阴影文字
            shadow_position = (position[0] + shadow_offset[0], position[1] + shadow_offset[1])
            draw.text(shadow_position, text, fill=shadow_color, font=role_font)
            
            # 绘制主文字
            draw.text(position, text, fill=font_color, font=role_font)

    # 输出 PNG
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()