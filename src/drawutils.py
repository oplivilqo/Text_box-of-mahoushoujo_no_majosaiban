from io import BytesIO
from typing import Tuple, Literal, Union
from PIL import Image, ImageDraw, ImageFont
import os

Align = Literal["left", "center", "right"]
VAlign = Literal["top", "middle", "bottom"]

IMG_SETTINGS = {
    "max_width": 1200,
    "max_height": 800,
    "quality": 65,
    "resize_ratio": 0.7
}

def compress_image(img: Image.Image) -> Image.Image:
    """压缩图像大小"""
    w, h = img.size
    new_w = int(w * IMG_SETTINGS["resize_ratio"])
    new_h = int(h * IMG_SETTINGS["resize_ratio"])

    # 限制最大尺寸
    if new_w > IMG_SETTINGS["max_width"]:
        ratio = IMG_SETTINGS["max_width"] / new_w
        new_w, new_h = IMG_SETTINGS["max_width"], int(new_h * ratio)

    if new_h > IMG_SETTINGS["max_height"]:
        ratio = IMG_SETTINGS["max_height"] / new_h
        new_h, new_w = IMG_SETTINGS["max_height"], int(new_w * ratio)

    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)

def draw_text_auto(
    img_src: Union[str, Image.Image],
    top_left: Tuple[int, int],
    bottom_right: Tuple[int, int],
    text: str,
    color: Tuple[int, int, int] = (0, 0, 0),
    font_path: str | None = None,
    max_font_h: int | None = None,
    align: Align = "center",
    valign: VAlign = "middle",
    line_spacing: float = 0.15,
    bracket_color: Tuple[int, int, int] = (137, 177, 251),
    img_overlay: Union[str, Image.Image, None] = None,
    role_name: str = "unknown",
    text_cfgs: dict | None = None,
) -> bytes:
    """
    在指定矩形内自适应字号绘制文本
    中括号及括号内文字使用 bracket_color
    """
    # 打开图像
    img = img_src.copy() if isinstance(img_src, Image.Image) else Image.open(img_src).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # 处理覆盖图层
    overlay = None
    if img_overlay is not None:
        if isinstance(img_overlay, Image.Image):
            overlay = img_overlay.copy()
        elif os.path.isfile(img_overlay):
            overlay = Image.open(img_overlay).convert("RGBA")

    x1, y1 = top_left
    x2, y2 = bottom_right
    if not (x2 > x1 and y2 > y1):
        raise ValueError("无效的文字区域")
    region_w, region_h = x2 - x1, y2 - y1

    # 字体加载
    def _load_font(size: int) -> ImageFont.FreeTypeFont:
        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, size=size)
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size=size)
        except Exception:
            return ImageFont.load_default()

    # 文本换行
    def wrap_lines(txt: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
        lines: list[str] = []
        for para in txt.splitlines() or [""]:
            has_space = " " in para
            units = para.split(" ") if has_space else list(para)
            buf = ""

            def unit_join(a: str, b: str) -> str:
                return (a + " " + b) if (a and has_space) else (a + b) if a else b

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
                        buf = u if draw.textlength(u, font=font) <= max_w else ""
                        if not buf:
                            lines.append(u)
            if buf:
                lines.append(buf)
            if para == "" and (not lines or lines[-1] != ""):
                lines.append("")
        return lines

    # 测量文本块
    def measure_block(lines: list[str], font: ImageFont.FreeTypeFont) -> Tuple[int, int, int]:
        ascent, descent = font.getmetrics()
        line_h = int((ascent + descent) * (1 + line_spacing))
        max_w = max((int(draw.textlength(ln, font=font)) for ln in lines), default=0)
        total_h = max(line_h * max(1, len(lines)), 1)
        return max_w, total_h, line_h

    # 搜索最大字号
    hi = min(region_h, max_font_h) if max_font_h else region_h
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

    # 解析着色片段
    def parse_color_segs(s: str, in_bracket: bool) -> Tuple[list[Tuple[str, Tuple[int, int, int]]], bool]:
        segs: list[Tuple[str, Tuple[int, int, int]]] = []
        buf = ""
        for ch in s:
            if ch in ["[", "【"]:
                if buf:
                    segs.append((buf, bracket_color if in_bracket else color))
                    buf = ""
                segs.append((ch, bracket_color))
                in_bracket = True
            elif ch in ["]", "】"]:
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

    # 垂直对齐
    y_start = y1 if valign == "top" else (y1 + (region_h - best_block_h) // 2 if valign == "middle" else y2 - best_block_h)

    # 绘制文本
    y = y_start
    in_bracket = False
    for ln in best_lines:
        line_w = int(draw.textlength(ln, font=font))
        x = x1 if align == "left" else (x1 + (region_w - line_w) // 2 if align == "center" else x2 - line_w)
        segs, in_bracket = parse_color_segs(ln, in_bracket)
        for seg_text, seg_color in segs:
            if seg_text:
                draw.text((x + 4, y + 4), seg_text, font=font, fill=(0, 0, 0))  # 阴影
                draw.text((x, y), seg_text, font=font, fill=seg_color)
                x += int(draw.textlength(seg_text, font=font))
        y += best_line_h
        if y - y_start > region_h:
            break

    # 覆盖置顶图层
    if overlay is not None:
        img.paste(overlay, (0, 0), overlay)

    # 绘制角色专属文字
    if text_cfgs and role_name in text_cfgs:
        shadow_offset = (2, 2)
        shadow_color = (0, 0, 0)

        for cfg in text_cfgs[role_name]:
            txt = cfg["text"]
            pos = tuple(cfg["position"])
            font_color = tuple(cfg["font_color"])
            font_size = cfg["font_size"]

            font_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'fonts', "font3.ttf")
            font = ImageFont.truetype(font_file, font_size)

            shadow_pos = (pos[0] + shadow_offset[0], pos[1] + shadow_offset[1])
            draw.text(shadow_pos, txt, fill=shadow_color, font=font)
            draw.text((pos[0], pos[1]), txt, fill=font_color, font=font)

    img = compress_image(img)

    # 输出 PNG
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def paste_image_auto(
    img_src: Union[str, Image.Image],
    top_left: Tuple[int, int],
    bottom_right: Tuple[int, int],
    content_img: Image.Image,
    align: Align = "center",
    valign: VAlign = "middle",
    padding: int = 0,
    allow_upscale: bool = False,
    keep_alpha: bool = True,
    img_overlay: Union[str, Image.Image, None] = None,
    max_img_size: Tuple[int | None, int | None] = (None, None),
    role_name: str = "unknown",
    text_cfgs: dict | None = None,
) -> bytes:
    """
    在指定矩形内放置图片，按比例缩放至最大但不超过该矩形
    """
    if not isinstance(content_img, Image.Image):
        raise TypeError("content_img 必须为 PIL.Image.Image")

    # 打开底图
    img = img_src.copy() if isinstance(img_src, Image.Image) else Image.open(img_src).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # 处理覆盖图层
    overlay = None
    if img_overlay is not None:
        if isinstance(img_overlay, Image.Image):
            overlay = img_overlay.copy()
        elif os.path.isfile(img_overlay):
            overlay = Image.open(img_overlay).convert("RGBA")

    x1, y1 = top_left
    x2, y2 = bottom_right
    if not (x2 > x1 and y2 > y1):
        raise ValueError("无效的粘贴区域")

    # 计算可用区域
    region_w = max(1, (x2 - x1) - 2 * padding)
    region_h = max(1, (y2 - y1) - 2 * padding)

    cw, ch = content_img.size
    if cw <= 0 or ch <= 0:
        raise ValueError("content_img 尺寸无效")

    # 计算缩放比例
    scale_w = region_w / cw
    scale_h = region_h / ch
    scale = min(scale_w, scale_h)

    if not allow_upscale:
        scale = min(1.0, scale)

    # 应用最大尺寸限制
    max_w, max_h = max_img_size
    if max_w is not None:
        scale = min(scale, max_w / cw)
    if max_h is not None:
        scale = min(scale, max_h / ch)

    # 至少 1x1
    new_w = max(1, int(round(cw * scale)))
    new_h = max(1, int(round(ch * scale)))

    resized = content_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # 计算粘贴坐标
    px = x1 + padding if align == "left" else (x1 + padding + (region_w - new_w) // 2 if align == "center" else x2 - padding - new_w)
    py = y1 + padding if valign == "top" else (y1 + padding + (region_h - new_h) // 2 if valign == "middle" else y2 - padding - new_h)

    # 粘贴图片
    if keep_alpha and "A" in resized.getbands():
        img.paste(resized, (px, py), resized)
    else:
        img.paste(resized, (px, py))

    # 覆盖置顶图层
    if overlay is not None:
        img.paste(overlay, (0, 0), overlay)

    # 绘制角色专属文字
    if text_cfgs and role_name in text_cfgs:
        shadow_offset = (2, 2)
        shadow_color = (0, 0, 0)

        for cfg in text_cfgs[role_name]:
            txt = cfg["text"]
            pos = tuple(cfg["position"])
            font_color = tuple(cfg["font_color"])
            font_size = cfg["font_size"]

            font_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'fonts', "font3.ttf")
            font = ImageFont.truetype(font_file, font_size)

            shadow_pos = (pos[0] + shadow_offset[0], pos[1] + shadow_offset[1])
            draw.text(shadow_pos, txt, fill=shadow_color, font=font)
            draw.text((pos[0], pos[1]), txt, fill=font_color, font=font)

    # 输出 PNG
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
