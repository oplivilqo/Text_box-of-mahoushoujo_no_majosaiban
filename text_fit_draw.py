from io import BytesIO
from typing import Tuple, Union, Literal, Optional
from PIL import Image, ImageDraw, ImageFont
import os
import re
import sys

# ===== PyInstaller 资源路径处理函数 =====
def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和打包后的环境"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

try:
    from pilmoji import Pilmoji
    PILMOJI_AVAILABLE = True
except ImportError:
    PILMOJI_AVAILABLE = False
    print("警告: pilmoji未安装，emoji将以黑白显示。安装方法: pip install pilmoji")

Align = Literal["left", "center", "right"]
VAlign = Literal["top", "middle", "bottom"]

IMAGE_SETTINGS = {
    "max_width": 1200,
    "max_height": 800,
    "quality": 65,
    "resize_ratio": 0.7
}

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

def is_emoji(char: str) -> bool:
    """判断字符是否为emoji"""
    code = ord(char)
    # Emoji常见Unicode范围
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
    image_overlay: Union[str, Image.Image,None]=None,
    role_name: str = "unknown",
    text_configs_dict: dict = None,

    # ✅ 新增参数
    emoji_enabled: bool = True,              # 是否启用 emoji PNG 渲染
    emoji_download_retries: int = 2,         # emoji 下载重试次数（main 传）
    emoji_image_dir: str | None = None,      # emoji png目录
    emoji_scale: float = 1.0,                # emoji 相对字号缩放
    emoji_download_timeout: float = 6.0,     # 下载超时（可选）
) -> bytes:
    """
    在指定矩形内自适应字号绘制文本；
    emoji_enabled=True 时：emoji 用 PNG inline 彩色贴图（本地无则自动下载并缓存）。
    emoji_enabled=False 时：所有字符都按普通文字渲染，不下载 emoji。
    中括号及括号内文字使用 bracket_color。
    支持彩色emoji表情显示。
    """

    if isinstance(image_source, Image.Image):
        img = image_source.copy()
    else:
        img = Image.open(image_source).convert("RGBA")
    
    # 创建Pilmoji对象用于彩色emoji
    if PILMOJI_AVAILABLE:
        pilmoji = Pilmoji(img)
        draw = pilmoji  # 使用pilmoji替代draw
    else:
        draw = ImageDraw.Draw(img)

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

    # emoji png 默认目录：脚本同级 emoji_png/
    if emoji_image_dir is None:
        emoji_image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emoji_png")

    emoji_cache: dict[str, Image.Image] = {}

    def _load_emoji_png(cluster: str) -> Optional[Image.Image]:
        """
        仅在 emoji_enabled=True 时起作用：
        本地有 => 读本地
        本地无 => Twemoji CDN 下载（重试次数由 emoji_download_retries 控制）
        """
        if not emoji_enabled:
            return None

        fn = emoji_cluster_to_filename(cluster)
        path = os.path.join(emoji_image_dir, fn)

        if path in emoji_cache:
            return emoji_cache[path]

        if os.path.exists(path):
            try:
                im = Image.open(path).convert("RGBA")
                emoji_cache[path] = im
                return im
            except Exception:
                try:
                    os.remove(path)
                except:
                    pass

        url = TWEMOJI_BASE + fn
        im = download_emoji_png(
            url,
            path,
            timeout=emoji_download_timeout,
            retries=max(0, int(emoji_download_retries))
        )
        if im is not None:
            emoji_cache[path] = im
            return im

        return None


    def _load_font(size: int) -> ImageFont.FreeTypeFont:
        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, size=size)
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size=size)
        except Exception:
            return ImageFont.load_default()

    # --- 3. 文本包行 (使用pilmoji的textsize) ---
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
                # 使用pilmoji计算宽度
                if PILMOJI_AVAILABLE:
                    w = pilmoji.getsize(trial, font=font)[0]
                else:
                    # 回退到普通draw
                    temp_draw = ImageDraw.Draw(img)
                    w = temp_draw.textlength(trial, font=font)
                
                if w <= max_w:
                    buf = trial
                else:
                    if buf:
                        lines.append(buf)

                    if has_space and len(u) > 1:
                        tmp = ""
                        for ch in u:
                            if PILMOJI_AVAILABLE:
                                tmp_w = pilmoji.getsize(tmp + ch, font=font)[0]
                            else:
                                temp_draw = ImageDraw.Draw(img)
                                tmp_w = temp_draw.textlength(tmp + ch, font=font)
                            if tmp_w <= max_w:
                                tmp += ch
                            else:
                                if tmp:
                                    lines.append(tmp)
                                tmp = ch
                        buf = tmp
                    else:
                        if PILMOJI_AVAILABLE:
                            u_w = pilmoji.getsize(u, font=font)[0]
                        else:
                            temp_draw = ImageDraw.Draw(img)
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

    def measure_block(lines: list[str], font_main: ImageFont.FreeTypeFont):
        ascent, descent = font_main.getmetrics()
        line_h = int((ascent + descent) * (1 + line_spacing))
        max_w = 0
        
        for ln in lines:
            if PILMOJI_AVAILABLE:
                w = pilmoji.getsize(ln, font=font)[0]
            else:
                temp_draw = ImageDraw.Draw(img)
                w = temp_draw.textlength(ln, font=font)
            max_w = max(max_w, int(w))
        total_h = max(line_h * max(1, len(lines)), 1)
        return max_w, total_h, line_h


    # ----------- 二分最大字号 -----------
    hi = min(region_h, max_font_height) if max_font_height else region_h
    lo, best_size, best_lines, best_line_h, best_block_h = 1, 0, [], 0, 0

    while lo <= hi:
        mid = (lo + hi) // 2
        font_main = _load_font(mid)
        lines = wrap_lines(text, font_main, region_w)
        w, h, lh = measure_block(lines, font_main)
        if w <= region_w and h <= region_h:
            best_size, best_lines, best_line_h, best_block_h = mid, lines, lh, h
            lo = mid + 1
        else:
            hi = mid - 1

    if best_size == 0:
        font_main = _load_font(1)
        best_lines = wrap_lines(text, font_main, region_w)
        best_line_h, best_block_h = 1, 1
        best_size = 1
    else:
        font_main = _load_font(best_size)

    em_px = emoji_advance_px(font_main)
    ascent, descent = font_main.getmetrics()

    # --- 6. 解析着色片段 ---
    def parse_color_segments(s: str, in_bracket: bool) -> Tuple[list[tuple[str, Tuple[int, int, int]]], bool]:
        segs: list[tuple[str, Tuple[int, int, int]]] = []
        buf = ""
        for ch in s:
            if ch in ("[", "【"):
                if buf:
                    segs.append((buf, bracket_color if in_bracket else color))
                    buf = ""
                segs.append((ch, bracket_color))
                in_bracket = True
            elif ch in ("]", "】"):
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

    # ----------- 垂直对齐 -----------
    if valign == "top":
        y_start = y1
    elif valign == "middle":
        y_start = y1 + (region_h - best_block_h) // 2
    else:
        y_start = y2 - best_block_h

    # --- 8. 绘制 (支持彩色emoji) ---
    y = y_start
    in_bracket = False
    
    for ln in best_lines:
        # 计算行宽
        if PILMOJI_AVAILABLE:
            line_w = pilmoji.getsize(ln, font=font)[0]
        else:
            temp_draw = ImageDraw.Draw(img)
            line_w = int(temp_draw.textlength(ln, font=font))
        
        if align == "left":
            x = x1
        elif align == "center":
            x = x1 + (region_w - line_w) // 2
        else:
            x = x2 - line_w
        
        segments, in_bracket = parse_color_segments(ln, in_bracket)
        
        for seg_text, seg_color in segments:
            if seg_text:
                if PILMOJI_AVAILABLE:
                    # 使用pilmoji绘制彩色emoji
                    # 先绘制阴影
                    pilmoji.text((x+4, y+4), seg_text, font=font, fill=(0,0,0), emoji_position_offset=(0, 0))
                    # 绘制主文字
                    pilmoji.text((x, y), seg_text, font=font, fill=seg_color, emoji_position_offset=(0, 0))
                    x += pilmoji.getsize(seg_text, font=font)[0]
                else:
                    # 回退到普通绘制
                    temp_draw = ImageDraw.Draw(img)
                    temp_draw.text((x+4, y+4), seg_text, font=font, fill=(0,0,0))
                    temp_draw.text((x, y), seg_text, font=font, fill=seg_color)
                    x += int(temp_draw.textlength(seg_text, font=font))
        
        y += best_line_h
        if y - y_start > region_h:
            break


    # 覆盖置顶图层
    if image_overlay is not None and img_overlay is not None:
        img.paste(img_overlay, (0, 0), img_overlay)
    elif image_overlay is not None and img_overlay is None:
        print("Warning: overlay image is not exist.")

    # 自动在图片上写角色专属文字
    if text_configs_dict and role_name in text_configs_dict:
        # 重新创建普通draw对象用于绘制角色名字
        regular_draw = ImageDraw.Draw(img)
        shadow_offset = (2, 2)
        shadow_color = (0, 0, 0)
        
        for config in text_configs_dict[role_name]:
            text = config["text"]
            position = tuple(config["position"])
            font_color = tuple(config["font_color"])
            font_size = config["font_size"]
        
            # 使用绝对路径加载字体文件
            font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'fonts', "font3.ttf")
            font = ImageFont.truetype(font_path, font_size)
            
            shadow_position = (position[0] + shadow_offset[0], position[1] + shadow_offset[1])
            
            regular_draw.text(shadow_position, char_text, fill=shadow_color, font=char_font)
            regular_draw.text(position, char_text, fill=font_color, font=char_font)
    
    img = compress_image(img)
    
    # --- 9. 输出 PNG ---
    buf = BytesIO()
    img.save(buf, "png")
    return buf.getvalue()
