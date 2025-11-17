# filename: text_fit_draw.py
from io import BytesIO
from typing import Tuple, Union, Literal
from PIL import Image, ImageDraw, ImageFont
import os

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
    
    # 限制最大尺寸
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
    bracket_color: Tuple[int, int, int] = (137,177,251),  # 中括号及内部内容颜色
    image_overlay: Union[str, Image.Image,None]=None,
    role_name: str = "unknown",  # 添加角色名称参数
    text_configs_dict: dict = None,  # 添加文字配置字典参数
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
    
    # 压缩底图
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

    # --- 2. 字体加载 ---
    def _load_font(size: int) -> ImageFont.FreeTypeFont:
        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, size=size)
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size=size)
        except Exception:
            return ImageFont.load_default()

    # --- 3. 文本包行 ---
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
                w = draw.textlength(trial, font=font)
                if w <= max_w:
                    buf = trial
                else:
                    if buf:
                        lines.append(buf)
                    if has_space and len(u) > 1:
                        tmp = ""
                        for ch in u:
                            if draw.textlength(tmp + ch, font=font) <= max_w:
                                tmp += ch
                            else:
                                if tmp:
                                    lines.append(tmp)
                                tmp = ch
                        buf = tmp
                    else:
                        if draw.textlength(u, font=font) <= max_w:
                            buf = u
                        else:
                            lines.append(u)
                            buf = ""
            if buf != "":
                lines.append(buf)
            if para == "" and (not lines or lines[-1] != ""):
                lines.append("")
        return lines

    # --- 4. 测量 ---
    def measure_block(lines: list[str], font: ImageFont.FreeTypeFont) -> tuple[int, int, int]:
        ascent, descent = font.getmetrics()
        line_h = int((ascent + descent) * (1 + line_spacing))
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
    def parse_color_segments(s: str,in_bracket: bool) -> Tuple[list[tuple[str, Tuple[int, int, int]]],bool]:
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
        return segs,in_bracket

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
        segments,in_bracket = parse_color_segments(ln,in_bracket)
        for seg_text, seg_color in segments:
            if seg_text:
                draw.text((x+4, y+4), seg_text, font=font, fill=(0,0,0))# 文字阴影
                draw.text((x, y), seg_text, font=font, fill=seg_color)
                x += int(draw.textlength(seg_text, font=font))
        y += best_line_h
        if y - y_start > region_h:
            break

    # 覆盖置顶图层（如果有）
    if image_overlay is not None and img_overlay is not None:
        img.paste(img_overlay, (0, 0), img_overlay)
    elif image_overlay is not None and img_overlay is None:
        print("Warning: overlay image is not exist.")

    # 自动在图片上写角色专属文字
    # 如果提供了文字配置字典且角色名称存在，则使用对应的文字配置
    if text_configs_dict and role_name in text_configs_dict:
        shadow_offset = (2, 2)  # 阴影偏移量
        shadow_color = (0, 0, 0)  # 黑色阴影
        
        for config in text_configs_dict[role_name]:
            text = config["text"]
            position = config["position"]
            font_color = config["font_color"]
            font_size = config["font_size"]
        
            # 使用绝对路径加载字体文件
            font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "font3.ttf")
            font = ImageFont.truetype(font_path, font_size)
            
            # 计算阴影位置
            shadow_position = (position[0] + shadow_offset[0], position[1] + shadow_offset[1])
            
            # 先绘制阴影文字
            draw.text(shadow_position, text, fill=shadow_color, font=font)
            
            # 再绘制主文字（覆盖在阴影上方）
            draw.text(position, text, fill=font_color, font=font)
    img = compress_image(img)
    # --- 9. 输出 PNG ---
    # img = img.convert('RGB')
    # buf = BytesIO()
    # img.save(buf, format="JPEG", quality=20)
    # return buf.getvalue()
    buf = BytesIO()
    img.save(buf, format="png")
    return buf.getvalue()
