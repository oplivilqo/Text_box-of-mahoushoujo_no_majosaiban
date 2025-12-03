# filename: image_fit_paste.py
from io import BytesIO
from typing import Tuple, Literal, Union
from PIL import Image #, ImageDraw , ImageFont
# import os
# from load_utils import load_font_cached
# from path_utils import get_resource_path

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
    max_image_size: Tuple[int, int] = (None, None),
) -> bytes:
    """
    在指定矩形内放置一张图片（content_image），按比例缩放至"最大但不超过"该矩形。
    """
    if isinstance(image_source, Image.Image):
        img = image_source
    else:
        img = Image.open(image_source).convert("RGBA")

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

    # 选择双线性插值
    resized = content_image.resize((new_w, new_h), Image.Resampling.BILINEAR)

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

    return img