# filename: text_fit_draw.py
from io import BytesIO
from typing import Tuple, Union, Literal
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
import os
# import sys
# import logging

# logger = logging.getLogger(__name__)

# 字体缓存
_font_cache = {}

#暂时用不上，总是先注释了

# ===== PyInstaller 资源路径处理函数 =====
# def get_resource_path(relative_path):
#     try:
#         # 打包后：sys.executable 是 exe 的路径
#         if getattr(sys, 'frozen', False):
#             # 获取 exe 所在目录
#             base_path = os.path.dirname(sys.executable)
#         else:
#             # 开发环境：脚本文件所在目录
#             base_path = os.path.dirname(os.path.abspath(__file__))
#     except Exception:
#         base_path = os.path.dirname(os.path.abspath(__file__))
    
#     return os.path.join(base_path, relative_path)

Align = Literal["left", "center", "right"]
VAlign = Literal["top", "middle", "bottom"]

# IMAGE_SETTINGS = {
#     "max_width": 1200,
#     "max_height": 800,
#     "quality": 65,
#     "resize_ratio": 0.7
# }

# def draw_name(base_img,text_configs_dict,role_name):
#     if text_configs_dict and role_name in text_configs_dict:
#         regular_draw = ImageDraw.Draw(base_img)
#         shadow_offset = (2, 2)
#         shadow_color = (0, 0, 0)
        
#         for config in text_configs_dict[role_name]:
#             char_text = config["text"]
#             if not char_text:  #跳过空文本
#                 continue
#             position = config["position"]
#             font_color = config["font_color"]
#             font_size = config["font_size"]
        
#             #使用新的assets/fonts路径
#             font_path_char = get_resource_path(os.path.join("assets", "fonts", "font3.ttf"))
#             char_font = _load_font_cached(font_path_char, font_size)
            
#             shadow_position = (position[0] + shadow_offset[0], position[1] + shadow_offset[1])
            
#             regular_draw.text(shadow_position, char_text, fill=shadow_color, font=char_font)
#             regular_draw.text(position, char_text, fill=font_color, font=char_font)
#         return base_img
#     else:
#         logger.warning("未找到角色 %s 的文字配置", role_name)
#         return base_img

# def compress_image(image: Image.Image) -> Image.Image:
#     width, height = image.size
    
#     new_width = int(width * IMAGE_SETTINGS["resize_ratio"])
#     new_height = int(height * IMAGE_SETTINGS["resize_ratio"])
    
#     # 限制最大尺寸
#     if new_width > IMAGE_SETTINGS["max_width"]:
#         ratio = IMAGE_SETTINGS["max_width"] / new_width
#         new_width, new_height = IMAGE_SETTINGS["max_width"], int(new_height * ratio)
    
#     if new_height > IMAGE_SETTINGS["max_height"]:
#         ratio = IMAGE_SETTINGS["max_height"] / new_height
#         new_height, new_width = IMAGE_SETTINGS["max_height"], int(new_width * ratio)
    
#     # 使用更快的BILINEAR插值（质量略降但速度更快）
#     return image.resize((new_width, new_height), Image.Resampling.BILINEAR)

# 方法1：Unicode范围检测（来自1.py）
def is_emoji_unicode(char: str) -> bool:
    code = ord(char)
    return (
        0x1F300 <= code <= 0x1F9FF or  # 常见表情符号
        0x2600 <= code <= 0x27BF or    # 杂项符号
        0x1F000 <= code <= 0x1F02F or  # 麻将牌等
        0xFE00 <= code <= 0xFE0F or    # 变体选择器
        0x1F200 <= code <= 0x1F251 or  # 方框符号
        0x1F600 <= code <= 0x1F64F or  # 表情符号
        0x1FA00 <= code <= 0x1FA6F or  # 扩展表情
        0x2700 <= code <= 0x27BF       # 装饰符号
    )

#缓存字体
def _load_font_cached(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    cache_key = f"{font_path}_{size}"
    if cache_key not in _font_cache:
        if font_path and os.path.exists(font_path):
            _font_cache[cache_key] = ImageFont.truetype(font_path, size=size)
        else:
            # logger.exception("字体文件不存在")
            raise FileNotFoundError("字体文件不存在")
    return _font_cache[cache_key]

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
    line_spacing: float = 0.15,#行距
    bracket_color: Tuple[int, int, int] = (137,177,251),  # 中括号及内部内容颜色
    image_overlay: Union[str, Image.Image,None]=None,
    # role_name: str = "unknown",  # 添加角色名称参数
    # text_configs_dict: dict = None,  # 添加文字配置字典参数
    # base_path: str = None,
    overlay_offset: Tuple[int, int] = (0, 0),
    compression_settings: dict = None
) -> bytes:
    """
    在指定矩形内自适应字号绘制文本；
    中括号及括号内文字使用 bracket_color。
    """

    if isinstance(image_source, Image.Image):
        img = image_source
    else:
        img = Image.open(image_source).convert("RGBA")
    
    #延迟创建pilmoji，先创建普通draw
    pilmoji = None
    temp_draw = ImageDraw.Draw(img)

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

    #字体加载
    def _load_font(size: int) -> ImageFont.FreeTypeFont:
        return _load_font_cached(font_path, size)
    
    #检测文本中是否有emoji
    has_emoji = False
    try:
        for ch in text:
            if is_emoji_unicode(ch):
                has_emoji = True
                break
    except Exception:
        has_emoji = False

    #文本分行
    def wrap_lines(txt: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
        lines: list[str] = []
        
        for para in txt.splitlines() or [""]:
            has_space = (" " in para)
            units = para.split(" ") if has_space else list(para)
            buf = ""

            def unit_join(a: str, b: str) -> str:
                if not a:
                    return b
                return (a + " " + b) if has_space else (a + b)

            for u in units:
                trial = unit_join(buf, u)
                w = temp_draw.textlength(trial, font=font)

                if w <= max_w:
                    buf = trial
                else:  #超出宽度，需换行
                    if buf:
                        lines.append(buf)
                    if has_space and len(u) > 1:
                        tmp = ""
                        for ch in u:
                            tmp_w = temp_draw.textlength(tmp + ch, font=font)
                            if tmp_w <= max_w:
                                tmp += ch
                            else: #切行
                                if tmp:
                                    lines.append(tmp)
                                tmp = ch
                        buf = tmp
                    else:
                        u_w = temp_draw.textlength(u, font=font)
                        if u_w <= max_w:
                            buf = u
                        else:
                            lines.append(u)
                            buf = ""
            if buf != "":
                lines.append(buf)
            if para == "" and (not lines or lines[-1] != ""):
                lines.append("")
        return lines

    #测量文本块尺寸
    def measure_block(lines: list[str], font: ImageFont.FreeTypeFont) -> tuple[int, int, int]:
        ascent, descent = font.getmetrics()
        line_h = int((ascent + descent) * (1 + line_spacing)) #单行高度
        max_w = 0 #最大行宽
        
        for ln in lines:
            w = temp_draw.textlength(ln, font=font)
            max_w = max(max_w, int(w))
        total_h = max(line_h * max(1, len(lines)), 1)#总高
        return max_w, total_h, line_h

    #搜索最大字号
    hi = min(region_h, max_font_height) if max_font_height else region_h
    lo, best_size, best_lines, best_line_h, best_block_h = 1, 0, [], 0, 0

    #如果文本包含emoji，则在搜索阶段使用"田"占位
    if has_emoji:
        measurement_text = ''.join('田' if is_emoji_unicode(ch) else ch for ch in text)
        pilmoji = Pilmoji(img)
    else:
        measurement_text = text

    while lo <= hi:
        mid = (lo + hi) // 2
        font = _load_font(mid)
        lines = wrap_lines(measurement_text, font, region_w)
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
    
    # 直接使用best_lines进行绘制；pilmoji会在需要时延迟创建
    best_lines = wrap_lines(text, font, region_w)
    #重新测量真实行高与总高
    _, best_block_h, best_line_h = measure_block(best_lines, font)

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

    # --- 8. 绘制---
    y = y_start
    in_bracket = False
    # 延迟创建pilmoji：只在需要绘制emoji段时创建一次
    # pilmoji_created = False

    for ln in best_lines:
        #计算行宽
        line_w = temp_draw.textlength(ln, font=font)

        if align == "left":
            x = x1
        elif align == "center":
            x = x1 + (region_w - line_w) // 2
        else:
            x = x2 - line_w
        
        segments, in_bracket = parse_color_segments(ln, in_bracket)
        
        for seg_text, seg_color in segments:
            if not seg_text:
                continue
            seg_has_emoji = any(is_emoji_unicode(ch) for ch in seg_text)
            if seg_has_emoji:
                # if not pilmoji_created:
                #     pilmoji = Pilmoji(img)
                #     pilmoji_created = True
                # pilmoji.text((x+4, y+4), seg_text, font=font, fill=(0,0,0), emoji_position_offset=(0, 20))
                pilmoji.text((x, y), seg_text, font=font, fill=seg_color, emoji_position_offset=(0, 20))
                adv = pilmoji.getsize(seg_text, font=font)[0]
            else:
                #纯文本片段使用ImageDraw
                temp_draw.text((x+4, y+4), seg_text, font=font, fill=(0,0,0))
                temp_draw.text((x, y), seg_text, font=font, fill=seg_color)
                #测量宽度
                adv = int(temp_draw.textlength(seg_text, font=font))
            x += adv
        
        y += best_line_h
        if y - y_start > region_h:
            break

    #覆盖置顶图层
    if image_overlay is not None and img_overlay is not None:
        img.paste(img_overlay, overlay_offset, img_overlay)
    elif image_overlay is not None:
        print("Warning: overlay image is not exist.")

    # 自动在图片上写角色专属文字 （预览图上已经有名字了）
    # if text_configs_dict and role_name in text_configs_dict:
    #     shadow_offset = (2, 2)
    #     shadow_color = (0, 0, 0)

    #     for config in text_configs_dict[role_name]:
    #         text = config["text"]
    #         position = tuple(config["position"])
    #         font_color = tuple(config["font_color"])
    #         font_size = config["font_size"]

    #         # 使用优化的字体加载
    #         font_path_char = get_resource_path(os.path.join("assets", "fonts", "font3.ttf"))
    #         try:
    #             role_font = _load_font_cached(font_path_char, font_size)
    #         except:
    #             try:
    #                 role_font = ImageFont.load_default()
    #             except:
    #                 print("无法加载任何字体，跳过角色专属文字绘制")
    #                 continue

    #         # 绘制阴影文字
    #         shadow_position = (
    #             position[0] + shadow_offset[0],
    #             position[1] + shadow_offset[1],
    #         )
    #         temp_draw.text(shadow_position, text, fill=shadow_color, font=role_font)

    #         # 绘制主文字
    #         temp_draw.text(position, text, fill=font_color, font=role_font)

    img = compress_image(img,compression_settings)
    
    # --- 9. 输出 PNG ---
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def compress_image(image: Image.Image, compression_settings: dict) -> Image.Image:
    """压缩图像"""
    if not compression_settings.get("pixel_reduction_enabled", False):
        return image

    compressed_image = image
    
    # 应用像素减少压缩
    if compression_settings.get("pixel_reduction_enabled", False):
        reduction_ratio = compression_settings.get("pixel_reduction_ratio", 50) / 100.0
        
        if reduction_ratio > 0 and reduction_ratio < 1:
            new_width = int(image.width * (1 - reduction_ratio))
            new_height = int(image.height * (1 - reduction_ratio))
            
            # 确保最小尺寸
            new_width = max(new_width, 300) #保持大致比例
            new_height = max(new_height, 100)
            
            # 试试原本用的BILINEAR(
            compressed_image = compressed_image.resize(
                (new_width, new_height), 
                Image.Resampling.BILINEAR   #LANCZOS
            )
    
    return compressed_image