# filename: image_fit_paste.py
from io import BytesIO
from typing import Tuple, Literal, Union
from PIL import Image, ImageDraw, ImageFont
import os

Align = Literal["left", "center", "right"]
VAlign = Literal["top", "middle", "bottom"]


def paste_image_auto(
    image_source: Union[str, Image.Image],
    top_left: Tuple[int, int],
    bottom_right: Tuple[int, int],
    content_image: Image.Image,
    align: Align = "center",
    valign: VAlign = "middle",
    padding: int = 0,
    allow_upscale: bool = False,
    keep_alpha: bool = True,
    image_overlay: Union[str, Image.Image, None] = None,
    max_image_size: Tuple[int, int] = (None, None),
    role_name: str = "unknown",
    text_configs_dict: dict = None,
    base_path: str = None,
    overlay_offset: Tuple[int, int] = (0, 0),
) -> bytes:
    """
    在指定矩形内放置一张图片（content_image），按比例缩放至"最大但不超过"该矩形。
    """
    if not isinstance(content_image, Image.Image):
        raise TypeError("content_image 必须为 PIL.Image.Image")

    if isinstance(image_source, Image.Image):
        img = image_source#.copy()
    else:
        img = Image.open(image_source).convert("RGBA")

    # 创建绘图对象
    draw = ImageDraw.Draw(img)

    # 处理覆盖图层
    if image_overlay is not None:
        if isinstance(image_overlay, Image.Image):
            img_overlay = image_overlay.copy()
        else:
            img_overlay = (
                Image.open(image_overlay).convert("RGBA")
                if os.path.isfile(image_overlay)
                else None
            )

    x1, y1 = top_left
    x2, y2 = bottom_right
    if not (x2 > x1 and y2 > y1):
        raise ValueError("无效的粘贴区域。")

    # 计算可用区域（考虑 padding）
    region_w = max(1, (x2 - x1) - 2 * padding)
    region_h = max(1, (y2 - y1) - 2 * padding)

    cw, ch = content_image.size
    if cw <= 0 or ch <= 0:
        raise ValueError("content_image 尺寸无效。")

    # 计算缩放比例
    scale_w = region_w / cw
    scale_h = region_h / ch
    scale = min(scale_w, scale_h)

    if not allow_upscale:
        scale = min(1.0, scale)

    # 应用最大图片尺寸限制
    max_width, max_height = max_image_size
    if max_width is not None:
        scale_w_limit = max_width / cw
        scale = min(scale, scale_w_limit)
    if max_height is not None:
        scale_h_limit = max_height / ch
        scale = min(scale, scale_h_limit)

    # 至少保证 1x1
    new_w = max(1, int(round(cw * scale)))
    new_h = max(1, int(round(ch * scale)))

    # 选择高质量插值
    resized = content_image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # 计算粘贴坐标（考虑对齐与 padding）
    if align == "left":
        px = x1 + padding
    elif align == "center":
        px = x1 + padding + (region_w - new_w) // 2
    else:  # "right"
        px = x2 - padding - new_w

    if valign == "top":
        py = y1 + padding
    elif valign == "middle":
        py = y1 + padding + (region_h - new_h) // 2
    else:  # "bottom"
        py = y2 - padding - new_h

    # 处理透明度
    if keep_alpha and ("A" in resized.getbands()):
        img.paste(resized, (px, py), resized)
    else:
        img.paste(resized, (px, py))

    # 覆盖置顶图层（如果有）- 应用偏移
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
                font_dir = os.path.join(base_path, "assets", "fonts")
            else:
                font_dir = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "assets", "fonts"
                )

            font_files = ["font3.ttf", "arial.ttf", "DejaVuSans.ttf"]
            font = None

            for font_file in font_files:
                font_path = os.path.join(font_dir, font_file)
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        break
                    except Exception as e:
                        print(f"加载字体 {font_path} 失败: {e}")
                        continue

            if font is None:
                try:
                    font = ImageFont.load_default()
                except:
                    print("无法加载任何字体，跳过文字绘制")
                    continue

            # 绘制阴影文字
            shadow_position = (
                position[0] + shadow_offset[0],
                position[1] + shadow_offset[1],
            )
            draw.text(shadow_position, text, fill=shadow_color, font=font)

            # 绘制主文字
            draw.text(position, text, fill=font_color, font=font)

    # 输出 PNG bytes
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
