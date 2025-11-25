from io import BytesIO
from typing import Tuple, Union, Literal, Optional
from PIL import Image, ImageDraw, ImageFont
import os
import sys
import time
import urllib.request
from urllib.error import URLError, HTTPError

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


# ---------------- Emoji 识别与 cluster 拆分 ----------------

ZWJ = 0x200D
VS16 = 0xFE0F

def is_regional_indicator(cp: int) -> bool:
    return 0x1F1E6 <= cp <= 0x1F1FF

def is_skin_tone(cp: int) -> bool:
    return 0x1F3FB <= cp <= 0x1F3FF

def is_emoji_base(cp: int) -> bool:
    # 覆盖主要 emoji 区 + 常见符号区（含⭐ 2B50）
    return (
        0x1F000 <= cp <= 0x1FAFF or
        0x2600 <= cp <= 0x27BF or
        0x2300 <= cp <= 0x23FF or
        0x2B00 <= cp <= 0x2BFF
    )

def is_emoji_char(ch: str) -> bool:
    cp = ord(ch)
    return is_emoji_base(cp) or cp in (ZWJ, VS16) or is_skin_tone(cp) or is_regional_indicator(cp)

def iter_emoji_clusters(s: str):
    """
    把字符串拆成 cluster（尽量贴近现实 emoji 组合规则）：
    - 单 emoji
    - emoji + VS16
    - emoji + skin tone
    - ZWJ 连接的组合
    - 区旗（regional indicators）
    """
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        cp = ord(ch)

        if not is_emoji_base(cp):
            yield ch, False
            i += 1
            continue

        cluster = ch
        i += 1

        while i < n:
            nxt = s[i]
            ncp = ord(nxt)

            if ncp == VS16 or is_skin_tone(ncp):
                cluster += nxt
                i += 1
                continue

            if ncp == ZWJ:
                if i + 1 < n:
                    cluster += nxt + s[i + 1]
                    i += 2
                    continue
                else:
                    cluster += nxt
                    i += 1
                    continue

            if is_regional_indicator(ncp) and is_regional_indicator(ord(cluster[-1])):
                cluster += nxt
                i += 1
                continue

            break

        yield cluster, True


def emoji_cluster_to_filename(cluster: str) -> str:
    """
    Twemoji/OpenMoji 常用命名：codepoints 用 '-' 连接，去掉 VS16。
    例：⭐ U+2B50 -> "2b50.png"
        👨‍👩‍👧‍👦 -> "1f468-200d-1f469-200d-1f467-200d-1f466.png"
    """
    cps = []
    for ch in cluster:
        cp = ord(ch)
        if cp == VS16:
            continue
        cps.append(cp)
    return "-".join(f"{cp:x}" for cp in cps) + ".png"


# ---------------- Twemoji CDN 下载与缓存 ----------------

TWEMOJI_BASE = "https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/"

def download_emoji_png(
    url: str,
    save_path: str,
    timeout: float = 6.0,
    retries: int = 2,
    backoff: float = 0.25
) -> Optional[Image.Image]:
    """
    从网络下载 emoji PNG，保存到本地并返回 PIL Image。
    retries 为重试次数（失败后会重试）。
    失败则返回 None，不抛异常。
    """
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (emoji-downloader)"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()

            im = Image.open(BytesIO(data)).convert("RGBA")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            im.save(save_path, format="PNG")
            return im

        except (HTTPError, URLError, OSError, ValueError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
            else:
                print(f"[emoji] download failed: {url} -> {e}")
                return None

    return None


# ---------------- 主绘制函数 ----------------

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
    """

    if isinstance(image_source, Image.Image):
        img = image_source.copy()
    else:
        img = Image.open(image_source).convert("RGBA")

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


    # ----------- 测宽/换行（根据 emoji_enabled 选择逻辑） -----------
    def emoji_advance_px(font_main: ImageFont.FreeTypeFont) -> int:
        ascent, descent = font_main.getmetrics()
        line_px = ascent + descent
        return max(1, int(line_px * emoji_scale))

    def text_width(txt: str, font_main: ImageFont.FreeTypeFont) -> float:
        if not emoji_enabled:
            return draw.textlength(txt, font=font_main)

        w = 0.0
        em_px = emoji_advance_px(font_main)
        for cluster, is_em in iter_emoji_clusters(txt):
            if is_em:
                w += em_px
            else:
                w += draw.textlength(cluster, font=font_main)
        return w

    def wrap_lines(txt: str, font_main: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
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
                w = text_width(trial, font_main)
                if w <= max_w:
                    buf = trial
                else:
                    if buf:
                        lines.append(buf)

                    if has_space and len(u) > 1:
                        tmp = ""
                        for ch in u:
                            if text_width(tmp + ch, font_main) <= max_w:
                                tmp += ch
                            else:
                                if tmp:
                                    lines.append(tmp)
                                tmp = ch
                        buf = tmp
                    else:
                        if text_width(u, font_main) <= max_w:
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
            max_w = max(max_w, int(text_width(ln, font_main)))
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


    # ----------- 解析中括号着色 -----------
    def parse_color_segments(s: str, in_bracket: bool):
        segs = []
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


    # ----------- 绘制 -----------
    y = y_start
    in_bracket = False
    shadow_offset = (4, 4)

    for ln in best_lines:
        line_w = int(text_width(ln, font_main))

        if align == "left":
            x = x1
        elif align == "center":
            x = x1 + (region_w - line_w) // 2
        else:
            x = x2 - line_w

        segments, in_bracket = parse_color_segments(ln, in_bracket)

        for seg_text, seg_color in segments:
            if not emoji_enabled:
                # 不启用 emoji：整段直接画
                draw.text((x + shadow_offset[0], y + shadow_offset[1]),
                          seg_text, font=font_main, fill=(0,0,0))
                draw.text((x, y), seg_text, font=font_main, fill=seg_color)
                x += int(draw.textlength(seg_text, font=font_main))
                continue

            # 启用 emoji：逐 cluster 画
            for cluster, is_em in iter_emoji_clusters(seg_text):
                if is_em:
                    em_img = _load_emoji_png(cluster)
                    if em_img is None:
                        draw.text((x, y), "□", font=font_main, fill=seg_color)
                        x += int(draw.textlength("□", font=font_main))
                        continue

                    em_draw = em_img.resize((em_px, em_px), Image.Resampling.LANCZOS)
                    em_y = y + ascent - em_px

                    img.paste(em_draw, (x + shadow_offset[0], em_y + shadow_offset[1]), em_draw)
                    img.paste(em_draw, (x, em_y), em_draw)

                    x += em_px
                else:
                    draw.text((x + shadow_offset[0], y + shadow_offset[1]),
                              cluster, font=font_main, fill=(0, 0, 0))
                    draw.text((x, y), cluster, font=font_main, fill=seg_color)
                    x += int(draw.textlength(cluster, font=font_main))

        y += best_line_h
        if y - y_start > region_h:
            break


    # 覆盖置顶图层
    if image_overlay is not None and img_overlay is not None:
        img.paste(img_overlay, (0, 0), img_overlay)
    elif image_overlay is not None and img_overlay is None:
        print("Warning: overlay image is not exist.")


    # 角色专属文字
    if text_configs_dict and role_name in text_configs_dict:
        shadow_offset2 = (2, 2)
        shadow_color2 = (0, 0, 0)
        for config in text_configs_dict[role_name]:
            t = config["text"]
            position = config["position"]
            font_color = config["font_color"]
            font_size = config["font_size"]

            font_path2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "font3.ttf")
            font2 = ImageFont.truetype(font_path2, font_size)

            shadow_position = (position[0] + shadow_offset2[0], position[1] + shadow_offset2[1])
            draw.text(shadow_position, t, fill=shadow_color2, font=font2)
            draw.text(position, t, fill=font_color, font=font2)

    img = compress_image(img)

    buf = BytesIO()
    img.save(buf, "png")
    return buf.getvalue()
