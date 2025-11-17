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
    image_overlay: Union[str, Image.Image,None]=None,
    max_image_size: Tuple[int, int] = (None, None),  # 添加最大图片尺寸限制 (width, height)
    role_name: str = "unknown",  # 添加角色名称参数
    text_configs_dict: dict = None,  # 添加文字配置字典参数
) -> bytes:
    """
    在指定矩形内放置一张图片（content_image），按比例缩放至“最大但不超过”该矩形。
    - base_image: 底图（会被复制，原图不改）
    - top_left / bottom_right: 指定矩形区域（左上/右下坐标）
    - content_image: 待放入的图片（PIL.Image.Image）
    - align / valign: 水平/垂直对齐方式
    - padding: 矩形内边距（像素），四边统一
    - allow_upscale: 是否允许放大（默认只缩小不放大）
    - keep_alpha: True 时保留透明通道并用其作为粘贴蒙版

    返回：最终 PNG 的 bytes。
    """
    if not isinstance(content_image, Image.Image):
        raise TypeError("content_image 必须为 PIL.Image.Image")

    if isinstance(image_source, Image.Image):
        img = image_source.copy()
    else:
        img = Image.open(image_source).convert("RGBA")

    if image_overlay is not None:
        if isinstance(image_overlay, Image.Image):
            img_overlay = image_overlay.copy()
        else:
            img_overlay = Image.open(image_overlay).convert("RGBA") if os.path.isfile(image_overlay) else None

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

    # 计算缩放比例（contain：不超过区域，并保持纵横比）
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
    resized = content_image.resize((new_w, new_h), Image.LANCZOS)

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

    # 处理透明度：若 keep_alpha=True 且有 alpha，则用 alpha 作为 mask 粘贴
    if keep_alpha and ("A" in resized.getbands()):
        img.paste(resized, (px, py), resized)
    else:
        # 没有 alpha 就直接粘贴（会覆盖底图该区域）
        img.paste(resized, (px, py))

    # 覆盖置顶图层（如果有）
    if image_overlay is not None and img_overlay is not None:
        img.paste(img_overlay, (0, 0), img_overlay)
    elif image_overlay is not None and img_overlay is None:
        print("Warning: overlay image is not exist.")

    # 输出 PNG bytes
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
