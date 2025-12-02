# filename: text_fit_draw.py
from io import BytesIO
from typing import Tuple, Union, Literal
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
# import textwrap
import time
# import os

from load_utils import load_font_cached

Align = Literal["left", "center", "right"]
VAlign = Literal["top", "middle", "bottom"]

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

def draw_text_auto(
    image_source: Union[str, Image.Image],
    top_left: Tuple[int, int],
    bottom_right: Tuple[int, int],
    text: str,
    color: Tuple[int, int, int] = (0, 0, 0),
    max_font_height: int | None = None,
    font_name: str | None = None,  # 改为字体名称参数
    align: Align = "center",
    valign: VAlign = "middle",
    line_spacing: float = 0.15,#行距
    bracket_color: Tuple[int, int, int] = (137,177,251),  # 中括号及内部内容颜色
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

    x1, y1 = top_left
    x2, y2 = bottom_right
    if not (x2 > x1 and y2 > y1):
        raise ValueError("无效的文字区域。")
    region_w, region_h = x2 - x1, y2 - y1

    #字体加载 - 简化版本，直接使用字体名称
    def _load_font(size: int) -> ImageFont.FreeTypeFont:
        # 如果没有提供字体名称，使用默认字体
        font_to_use = font_name if font_name else "font3.ttf"
        return load_font_cached(font_to_use, size)
    
    #检测文本中是否有emoji
    has_emoji = False
    try:
        for ch in text:
            if is_emoji_unicode(ch):
                has_emoji = True
                break
    except Exception:
        has_emoji = False

    # def wrap_lines2(txt: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    #     """使用textwrap模块优化的文本分行函数"""
        
    #     # 计算平均字符宽度，用于估算每行字符数
    #     avg_char_width = temp_draw.textlength("中", font=font)  # 使用中文字符作为基准
    #     approx_chars_per_line = max(1, int(max_w / avg_char_width))
        
    #     # 使用textwrap.wrap进行智能分行
    #     lines = textwrap.wrap(
    #         txt, 
    #         width=approx_chars_per_line,
    #         expand_tabs=False,
    #         replace_whitespace=False,
    #         drop_whitespace=False,
    #         break_long_words=True,  # 允许长单词换行
    #         break_on_hyphens=False,
    #         fix_sentence_endings=True
    #     )
        
    #     # 如果textwrap没有返回任何行（空文本情况）
    #     if not lines and txt.strip():
    #         lines = [txt]
        
    #     return lines

    #文本分行
    def wrap_lines(txt: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
        lines: list[str] = []
        has_space=False

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
    st=time.time()
    print("搜索最大字号前耗时:",int((time.time()-st)*1000))
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
    print("搜索最大字号耗时:",int((time.time()-st)*1000))
    
    # --- 6. 解析着色片段 ---
    def parse_color_segments(s: str, bracket_stack: list) -> Tuple[list[tuple[str, Tuple[int, int, int]]], list]:
        """解析颜色片段，返回片段列表和更新后的括号栈"""
        segs: list[tuple[str, Tuple[int, int, int]]] = []
        buf = ""
        
        # 定义成对的括号和引号，包括左右相同的英文引号
        bracket_pairs = {
            '[': ']', '【': '】', '〔': '〕', '（': '）', '(': ')',
            '‘': '’', '「': '」', '｢': '｣','『': '』','〖': '〗','<':'>','《': '》', '〈': '〉','“': '”',
            '"': '"', "'": "'", '`': '`',
        }
        
        for ch in s:
            # 处理左括号或引号
            if ch in bracket_pairs.keys():
                if buf:
                    current_color = bracket_color if bracket_stack else color
                    segs.append((buf, current_color))
                    buf = ""
                
                # 如果是英文引号（左右相同），特殊处理
                if ch in ('"', "'", '`'):
                    # 如果栈顶是相同的引号，则这是关闭引号
                    if bracket_stack and bracket_stack[-1] == ch:
                        segs.append((ch, bracket_color))
                        bracket_stack.pop()  # 关闭引号
                    else:
                        segs.append((ch, bracket_color))
                        bracket_stack.append(ch)  # 打开引号
                else:
                    # 普通括号，直接打开
                    segs.append((ch, bracket_color))
                    bracket_stack.append(ch)  # 将左括号压栈
                    
            # 处理右括号
            elif ch in bracket_pairs.values():
                if buf:
                    segs.append((buf, bracket_color))
                    buf = ""
                
                segs.append((ch, bracket_color))
                
                # 如果栈不为空，尝试弹出匹配的左括号
                if bracket_stack:
                    last_bracket = bracket_stack[-1]
                    # 检查当前右括号是否匹配栈顶的左括号
                    if bracket_pairs.get(last_bracket) == ch:
                        bracket_stack.pop()
                # 注意：如果不匹配，我们不做任何操作，这个右括号可能是一个错误，但我们不处理
            else:
                buf += ch
                
        if buf:
            current_color = bracket_color if bracket_stack else color
            segs.append((buf, current_color))
            
        return segs, bracket_stack

    # --- 7. 垂直对齐 ---
    if valign == "top":
        y_start = y1
    elif valign == "middle":
        y_start = y1 + (region_h - best_block_h) // 2
    else:
        y_start = y2 - best_block_h

    # --- 8. 绘制---
    y = y_start
    bracket_stack = []  # 初始化括号栈，跨行传递状态

    for ln in best_lines:
        # 计算行宽
        line_w = temp_draw.textlength(ln, font=font)

        if align == "left":
            x = x1
        elif align == "center":
            x = x1 + (region_w - line_w) // 2
        else:
            x = x2 - line_w
        
        # 解析当前行的颜色片段，传递括号栈状态
        segments, bracket_stack = parse_color_segments(ln, bracket_stack)
        
        for seg_text, seg_color in segments:
            if not seg_text:
                continue
            seg_has_emoji = any(is_emoji_unicode(ch) for ch in seg_text)
            if seg_has_emoji:
                pilmoji.text((x, y), seg_text, font=font, fill=seg_color, emoji_position_offset=(0, 20))
                adv = pilmoji.getsize(seg_text, font=font)[0]
            else:
                # 纯文本片段使用ImageDraw
                temp_draw.text((x+4, y+4), seg_text, font=font, fill=(0,0,0))
                temp_draw.text((x, y), seg_text, font=font, fill=seg_color)
                # 测量宽度
                adv = int(temp_draw.textlength(seg_text, font=font))
            x += adv
        
        y += best_line_h
        if y - y_start > region_h:
            break

    # 压缩图片
    img = compress_image(img,compression_settings)
    
    # --- 9. 输出 BMP ---
    buf = BytesIO()
    img.convert("RGB").save(buf, format="BMP")
    bmp_data = buf.getvalue()[14:]
    return bmp_data

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