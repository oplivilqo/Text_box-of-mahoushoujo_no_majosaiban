# filename: text_fix_draw.py
from io import BytesIO
from typing import Tuple, Union, Literal, List
from PIL import Image, ImageDraw, ImageFont
import os
import time
import emoji  # 添加emoji库

from load_utils import load_font_cached
from path_utils import get_resource_path

Align = Literal["left", "center", "right"]
VAlign = Literal["top", "middle", "bottom"]

# 保留括号定义
bracket_pairs = {
    "[": "]",
    "【": "】",
    "〔": "〕",
    "‘": "’",
    "「": "」",
    "｢": "｣",
    "『": "』",
    "〖": "〗",
    "<": ">",
    "《": "》",
    "〈": "〉",
    "「": "」",
    "｢": "｣",
    "『": "』",
    "〖": "〗",
    "<": ">",
    "《": "》",
    "〈": "〉",
    "“": "”",
    '"': '"',
}

def draw_text_auto(
    image_source: Union[str, Image.Image],
    top_left: Tuple[int, int],
    bottom_right: Tuple[int, int],
    text: str,
    color: Tuple[int, int, int] = (0, 0, 0),
    max_font_height: int = None,
    font_name: str = None,
    align: Align = "center",
    valign: VAlign = "middle",
    line_spacing: float = 0.15,
    bracket_color: Tuple[int, int, int] = (137, 177, 251),
    compression_settings: dict = None,
) -> bytes:
    """
    在指定矩形内自适应字号绘制文本
    中括号及括号内文字使用 bracket_color
    """

    PLACEHOLDER_CHAR = "田"  # 用来占位 emoji 的字符（宽度为一个普通汉字）
    EMOJI_FALLBACK_CHAR = "□"  # emoji 加载/绘制失败时使用的单字符替代（不改变布局宽度）
    
    # --- 辅助：把文本中的 emoji 序列提取出来，并返回替换为占位符后的文本以及 emoji 列表 ---
    def extract_emojis_and_replace(src: str, placeholder: str = PLACEHOLDER_CHAR):
        """
        使用 emoji.emoji_list 抽取所有 emoji 序列（会包含组合 emoji），并用单个 placeholder 替换每个序列。
        返回 (placeholder_text, emoji_list)。
        emoji_list 按文本顺序排列，每项是原始 emoji 序列字符串。
        """
        emoji_infos = emoji.emoji_list(src)
        if not emoji_infos:
            return src, []
        out_chars = []
        emojis = []
        last = 0
        for info in emoji_infos:
            s = info['match_start']
            e = info['match_end']
            # 普通文本段
            if s > last:
                out_chars.append(src[last:s])
            # 占位符代替整个 emoji 序列
            out_chars.append(placeholder)
            emojis.append(src[s:e])
            last = e
        # 剩余普通文本
        if last < len(src):
            out_chars.append(src[last:])
        placeholder_text = "".join(out_chars)
        return placeholder_text, emojis

    def get_emoji_filename(emoji_char_or_seq: str) -> str:
        """为emoji字符或序列生成对应的文件名"""
        hex_codes = []
        for char in emoji_char_or_seq:
            code_point = ord(char)
            hex_code = hex(code_point)[2:].lower()
            hex_codes.append(hex_code)
        return f"emoji_u{'_'.join(hex_codes)}.png"

    def load_emoji_image(emoji_char_or_seq: str, emoji_size: int) -> Image.Image:
        """加载emoji图片并调整到指定尺寸"""
        try:
            filename = get_emoji_filename(emoji_char_or_seq)
            emoji_path = get_resource_path(os.path.join("assets", "emoji", filename))

            if not os.path.exists(emoji_path):
                # 尝试加载基础emoji（第一个字符）
                base_char = emoji_char_or_seq[0]
                base_filename = get_emoji_filename(base_char)
                base_path = get_resource_path(os.path.join("assets", "emoji", base_filename))

                if not os.path.exists(base_path):
                    # 如果仍然不存在，尝试返回 None（上层会回退为单字符绘制）
                    print(f"[load_emoji_image] emoji asset not found: {emoji_path} nor {base_path}")
                    return None

                emoji_img = Image.open(base_path).convert("RGBA")
            else:
                emoji_img = Image.open(emoji_path).convert("RGBA")

            # 调整到目标尺寸，保持宽高比
            if emoji_img.width != emoji_size or emoji_img.height != emoji_size:
                emoji_img = emoji_img.resize((emoji_size, emoji_size), Image.Resampling.BILINEAR)

            return emoji_img
        except Exception as e:
            print(f"[load_emoji_image] 加载emoji图片失败 {emoji_char_or_seq}: {e}")
            return None

    def draw_text_or_emoji(
        draw: ImageDraw.Draw,
        x: int,
        y: int,
        text: str,
        font: ImageFont.FreeTypeFont,
        color: Tuple[int, int, int],
        emoji_size: int = None,
        shadow_offset: int = 4,
    ) -> int:
        """
        绘制文本或emoji，返回绘制的宽度
        如果提供了emoji_size，则绘制emoji（text 为 emoji 序列），否则绘制普通文本
        """
        if emoji_size is not None:
            # 绘制emoji（text 是 emoji 序列）
            emoji_img = load_emoji_image(text, emoji_size)
            if emoji_img is None:
                # 失败则使用单字符替代（不回退布局）
                try:
                    # 阴影 + 正文替代字符绘制
                    draw.text((x + shadow_offset, y + shadow_offset), EMOJI_FALLBACK_CHAR, font=font, fill=(0, 0, 0))
                    draw.text((x, y), EMOJI_FALLBACK_CHAR, font=font, fill=color)
                    w = int(draw.textlength(EMOJI_FALLBACK_CHAR, font=font))
                    print(f"[draw_text_or_emoji] emoji 加载失败，使用替代字符绘制: {text}")
                    return w
                except Exception as e:
                    print(f"[draw_text_or_emoji] emoji 绘制失败且替代字符绘制也失败: {text} -> {e}")
                    return 0

            # 计算绘制位置：使emoji在视觉上接近文字基线
            try:
                ascent, _ = font.getmetrics()
                emoji_y = y + ascent - emoji_size + int(emoji_size * 0.1)
                img = draw._image  # 直接获取底层图像用于 paste
                # 计算动态偏移（保留你原有的思路）
                font_size_ratio = emoji_size / 90 if 90 != 0 else 1
                dynamic_offset = int(emoji_size * 0.1 * font_size_ratio)
                paste_y = emoji_y + dynamic_offset
                img.paste(emoji_img, (x, paste_y), emoji_img)
                return emoji_img.width
            except Exception as e:
                # 如果贴图失败，回退为单字符替代（并记录）
                print(f"[draw_text_or_emoji] emoji paste 失败 {text}: {e}")
                try:
                    draw.text((x + shadow_offset, y + shadow_offset), EMOJI_FALLBACK_CHAR, font=font, fill=(0, 0, 0))
                    draw.text((x, y), EMOJI_FALLBACK_CHAR, font=font, fill=color)
                    w = int(draw.textlength(EMOJI_FALLBACK_CHAR, font=font))
                    return w
                except Exception as e2:
                    print(f"[draw_text_or_emoji] 替代字符绘制也失败: {e2}")
                    return 0
        else:
            # 绘制普通文本（带阴影效果）
            draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0))
            draw.text((x, y), text, font=font, fill=color)
            return int(draw.textlength(text, font=font))

    # --- 主函数逻辑开始 ---
    if isinstance(image_source, Image.Image):
        img = image_source
    else:
        img = Image.open(image_source).convert("RGBA")

    draw = ImageDraw.Draw(img)

    x1, y1 = top_left
    x2, y2 = bottom_right
    if not (x2 > x1 and y2 > y1):
        raise ValueError("无效的文字区域。")

    region_w, region_h = x2 - x1, y2 - y1

    # 字体加载函数
    def _load_font(size: int) -> ImageFont.FreeTypeFont:
        font_to_use = font_name if font_name else "font3.ttf"
        return load_font_cached(font_to_use, size)

    # --- 换行函数（保持原有逻辑，只用于处理 placeholder_text） ---
    def wrap_lines(txt: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
        """将文本按最大宽度换行"""
        lines: list[str] = []

        for para in txt.splitlines() or [""]:
            has_space = " " in para
            units = para.split(" ") if has_space else list(para)
            buf = ""

            def unit_join(a: str, b: str) -> str:
                if not a:
                    return b
                return f"{a} {b}" if has_space else f"{a}{b}"

            i = 0
            units_len = len(units)

            while i < units_len:
                # 尝试将当前单位加入缓冲区
                trial = unit_join(buf, units[i])
                w = draw.textlength(trial, font=font)

                if w <= max_w:
                    buf = trial
                    i += 1
                else:
                    # 缓冲区有内容，先输出
                    if buf:
                        lines.append(buf)
                        buf = ""
                    else:
                        # 缓冲区为空，当前单位单独处理
                        if has_space and len(units[i]) > 1:
                            # 优化：使用二分查找找到最大可容纳字符数
                            word = units[i]
                            left, right = 1, len(word)

                            while left <= right:
                                mid = (left + right) // 2
                                prefix = word[:mid]
                                if draw.textlength(prefix, font=font) <= max_w:
                                    left = mid + 1
                                else:
                                    right = mid - 1

                            # right是最大可容纳字符数
                            if right > 0:
                                # 可以放一部分
                                lines.append(word[:right])
                                # 更新当前单位为剩余部分
                                units[i] = word[right:]
                                # 不增加i，继续处理剩余部分
                            else:
                                # 单个字符就超宽
                                lines.append(word)
                                i += 1
                        else:
                            # 单个字符或无空格情况
                            u_w = draw.textlength(units[i], font=font)
                            if u_w <= max_w:
                                buf = units[i]
                            else:
                                lines.append(units[i])
                            i += 1

            # 处理缓冲区剩余内容
            if buf:
                lines.append(buf)

            # 处理空行
            if para == "" and (not lines or lines[-1] != ""):
                lines.append("")

        return lines

    # --- 测量文本块尺寸函数 ---
    def measure_block(
        lines: list[str], font: ImageFont.FreeTypeFont
    ) -> tuple[int, int, int]:
        ascent, descent = font.getmetrics()
        line_h = int((ascent + descent) * (1 + line_spacing))  # 单行高度
        max_w = 0  # 最大行宽

        for ln in lines:
            w = draw.textlength(ln, font=font)
            max_w = max(max_w, int(w))
        total_h = max(line_h * max(1, len(lines)), 1)  # 总高
        return max_w, total_h, line_h

    # --- 先提取 emoji 并替换为占位符（保证组合 emoji 不会被拆开） ---
    placeholder_text, emoji_list = extract_emojis_and_replace(text, PLACEHOLDER_CHAR)

    # --- 搜索最大字号（基于 placeholder_text） ---
    hi = min(region_h, max_font_height) if max_font_height else region_h
    lo, best_size, best_lines, best_line_h, best_block_h = 1, 0, [], 0, 0

    st = time.time()

    # 二分查找最佳字号（使用替换后的文本测量）
    while lo <= hi:
        mid = (lo + hi) // 2
        font = _load_font(mid)
        lines = wrap_lines(placeholder_text, font, region_w)
        w, h, lh = measure_block(lines, font)
        if w <= region_w and h <= region_h:
            best_size, best_lines, best_line_h, best_block_h = mid, lines, lh, h
            lo = mid + 1
        else:
            hi = mid - 1

    if best_size == 0:
        font = _load_font(1)
        best_lines = wrap_lines(placeholder_text, font, region_w)
        _, best_block_h, best_line_h = 0, 1, 1
        best_size = 1
    else:
        font = _load_font(best_size)

    print("分行耗时:", int((time.time() - st) * 1000))

    # 注意：此处不要用原始 text 再次 wrap —— 必须使用 placeholder_text 对齐
    # best_lines 已经是用 placeholder_text 计算的
    # 重新测量真实行高与总高（在最终 font 下）
    _, best_block_h, best_line_h = measure_block(best_lines, font)

    # 计算emoji尺寸（以字体大小为基准）
    emoji_size = best_size

    # 计算垂直起始位置
    if valign == "top":
        y_start = y1
    elif valign == "middle":
        y_start = y1 + (region_h - best_block_h) // 2
    else:  # bottom
        y_start = y2 - best_block_h

    # --- 绘制 ---
    st = time.time()
    y_pos = y_start
    bracket_stack = []  # 初始化括号栈，跨行传递状态

    # 解析颜色片段的内部函数（使用占位符文本）
    def parse_color_segments(
        s: str, bracket_stack: list
    ) -> Tuple[list[tuple[str, Tuple[int, int, int]]], list]:
        """解析颜色片段，返回片段列表和更新后的括号栈"""
        segs: list[tuple[str, Tuple[int, int, int]]] = []
        buf = ""

        for ch in s:
            # 处理左括号或引号
            if ch in bracket_pairs.keys():
                if buf:
                    current_color = bracket_color if bracket_stack else color
                    segs.append((buf, current_color))
                    buf = ""

                # 如果是英文引号（左右相同），特殊处理
                if ch in ('"', "'", "`"):
                    if bracket_stack and bracket_stack[-1] == ch:
                        segs.append((ch, bracket_color))
                        bracket_stack.pop()  # 关闭引号
                    else:
                        segs.append((ch, bracket_color))
                        bracket_stack.append(ch)  # 打开引号
                else:
                    segs.append((ch, bracket_color))
                    bracket_stack.append(ch)  # 将左括号压栈

            # 处理右括号
            elif ch in bracket_pairs.values():
                if buf:
                    segs.append((buf, bracket_color))
                    buf = ""

                segs.append((ch, bracket_color))

                if bracket_stack:
                    last_bracket = bracket_stack[-1]
                    if bracket_pairs.get(last_bracket) == ch:
                        bracket_stack.pop()
            else:
                buf += ch
        if buf:
            current_color = bracket_color if bracket_stack else color
            segs.append((buf, current_color))

        return segs, bracket_stack

    # emoji_iter 用来按顺序从 emoji_list 中取出下一个 emoji 序列
    emoji_iter_index = 0
    total_emojis = len(emoji_list)

    for ln in best_lines:
        # 计算行宽（基于 placeholder 文本）
        line_w = draw.textlength(ln, font=font)

        if align == "left":
            x_pos = x1
        elif align == "center":
            x_pos = x1 + (region_w - line_w) // 2
        else:
            x_pos = x2 - line_w

        # 解析当前行的颜色片段，传递括号栈状态
        segments, bracket_stack = parse_color_segments(ln, bracket_stack)

        for seg_text, seg_color in segments:
            if not seg_text:
                continue

            # seg_text 已经是占位符文本的一段（可能包含占位符）
            i = 0
            L = len(seg_text)
            while i < L:
                ch = seg_text[i]
                if ch == PLACEHOLDER_CHAR:
                    # 用下一个 emoji 绘制（如果没有剩余 emoji，则绘制替代字符）
                    if emoji_iter_index < total_emojis:
                        emoji_seq = emoji_list[emoji_iter_index]
                        emoji_iter_index += 1
                        width = draw_text_or_emoji(draw, x_pos, y_pos, emoji_seq, font, seg_color, emoji_size)
                        x_pos += width
                    else:
                        # 占位符多于 emoji（不应出现），绘制替代字符
                        print("[draw] 占位符多于实际 emoji，绘制替代字符")
                        width = draw_text_or_emoji(draw, x_pos, y_pos, EMOJI_FALLBACK_CHAR, font, seg_color, None)
                        x_pos += width
                    i += 1
                else:
                    # 连续的普通字符片段（直到下一个占位符或段末）
                    j = i
                    while j < L and seg_text[j] != PLACEHOLDER_CHAR:
                        j += 1
                    text_fragment = seg_text[i:j]
                    # 绘制这段普通文本（含中文、英文、标点等）
                    width = draw_text_or_emoji(draw, x_pos, y_pos, text_fragment, font, seg_color, None)
                    x_pos += width
                    i = j

        y_pos += best_line_h
        if y_pos - y_start > region_h:
            break

    # 如果有剩余 emoji 没被绘制，则记录（通常说明占位符数量少于 emoji 数量）
    if emoji_iter_index < total_emojis:
        print(f"[draw] 警告：有 {total_emojis - emoji_iter_index} 个 emoji 未被绘制（占位符不足）")

    print("绘制耗时:", int((time.time() - st) * 1000))
    st = time.time()

    # 压缩图片（可选）
    if compression_settings and compression_settings.get("pixel_reduction_enabled", False):
        reduction_ratio = compression_settings.get("pixel_reduction_ratio", 50) / 100.0
        if 0 < reduction_ratio < 1:
            new_width = max(int(img.width * (1 - reduction_ratio)), 300)
            new_height = max(int(img.height * (1 - reduction_ratio)), 100)
            img = img.resize((new_width, new_height), Image.Resampling.BILINEAR)

    print("压缩耗时:", int((time.time() - st) * 1000))
    st = time.time()

    # --- 输出 BMP ---
    buf = BytesIO()
    img.convert("RGB").save(buf, format="BMP")
    bmp_data = buf.getvalue()[14:]
    print("转换BMP耗时:", int((time.time() - st) * 1000))

    return bmp_data
