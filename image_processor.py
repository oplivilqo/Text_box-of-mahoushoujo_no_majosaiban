"""图片处理模块 - 优化版本"""

import os
import random
from PIL import Image, ImageDraw #, ImageFont

from text_fit_draw import draw_text_auto, load_font_cached
from image_fit_paste import paste_image_auto
from path_utils import get_resource_path
from load_utils import load_background_safe, load_character_safe


class ImageProcessor:
    """图片处理器 - 优化版本"""

    def __init__(
        self,
        base_path: str,
        box_rect: tuple,
        text_configs_dict: dict,
        mahoshojo: dict = None,
    ):
        self.base_path = base_path
        self.box_rect = box_rect
        self.text_configs_dict = text_configs_dict
        self.mahoshojo = mahoshojo or {}
        self.background_count = 16

        # 当前预览的基础图片（用于快速生成）
        self.current_base_image = None

    def _load_background(self, background_index: int) -> Image.Image:
        """加载背景图片 - 使用全局背景缓存"""
        # 使用资源路径获取
        background_path = get_resource_path(os.path.join("assets", "background", f"c{background_index}.png"))
        # 使用专门的背景图片加载函数
        return load_background_safe(
            background_path, 
            default_size=(800, 600), 
            default_color=(100, 100, 200)
        )

    def _load_character_image(
        self, character_name: str, emotion_index: int
    ) -> Image.Image:
        """加载角色图片 - 使用全局角色缓存"""
        # 使用资源路径获取
        overlay_path = get_resource_path(os.path.join(
            "assets",
            "chara",
            character_name,
            f"{character_name} ({emotion_index}).png"
        ))

        # 使用专门的角色图片加载函数
        return load_character_safe(
            overlay_path, 
            default_size=(800, 600), 
            default_color=(0, 0, 0, 0)
        )

    def preload_character_images(self, character_name: str):
        """预加载角色图片到内存"""
        if character_name not in self.mahoshojo:
            return

        emotion_count = self.mahoshojo[character_name].get("emotion_count", 0)

        for emotion_index in range(1, emotion_count + 1):
            # 触发加载并缓存到全局角色缓存
            self._load_character_image(character_name, emotion_index)

    def get_character_font(self, character_name: str) -> str:
        """获取角色字体文件路径"""
        if character_name in self.mahoshojo:
            font_file = self.mahoshojo[character_name].get("font", "font3.ttf")
            return get_resource_path(os.path.join("assets", "fonts", font_file))
        else:
            # 默认字体
            return get_resource_path(os.path.join("assets", "fonts", "font3.ttf"))

    def generate_base_image_with_text(
        self, character_name: str, background_index: int, emotion_index: int
    ) -> Image.Image:
        """生成带角色文字的基础图片"""
        # 生成基础图片（包含角色名称文字）
        background = self._load_background(background_index)
        overlay = self._load_character_image(character_name, emotion_index)

        # 合成基础图片
        result = background
        result.paste(overlay, (0, 134), overlay)

        # 添加角色名称文字
        if self.text_configs_dict and character_name in self.text_configs_dict:
            draw = ImageDraw.Draw(result)
            shadow_offset = (2, 2)
            shadow_color = (0, 0, 0)

            for config in self.text_configs_dict[character_name]:
                text = config["text"]
                position = tuple(config["position"])
                font_color = tuple(config["font_color"])
                font_size = config["font_size"]

                # 使用角色专用字体
                font_path = self.get_character_font(character_name)
                font = load_font_cached(font_path, font_size)

                # 绘制阴影文字
                shadow_position = (
                    position[0] + shadow_offset[0],
                    position[1] + shadow_offset[1],
                )
                draw.text(shadow_position, text, fill=shadow_color, font=font)

                # 绘制主文字
                draw.text(position, text, fill=font_color, font=font)

        return result

    def generate_image_fast(
        self,
        character_name: str,
        text: str = None,
        content_image: Image.Image = None,
        font_path: str = None,
        font_size: int = None,
        compression_settings: dict = None
    ) -> bytes:
        """快速生成图片 - 使用缓存的基础图片"""
        base_image = self.current_base_image

        text_box_topleft = (self.box_rect[0][0], self.box_rect[0][1])
        image_box_bottomright = (self.box_rect[1][0], self.box_rect[1][1])
        result = None

        if content_image is not None:
            # 调用粘贴图像函数，它返回的是字节数据
            result = paste_image_auto(
                image_source=base_image,
                # image_overlay=None,
                top_left=text_box_topleft,
                bottom_right=image_box_bottomright,
                content_image=content_image,
                align="center",
                valign="middle",
                padding=12,
                allow_upscale=True,
                keep_alpha=True,
                # role_name=character_name,
                # text_configs_dict=self.text_configs_dict,
                # base_path=self.base_path,
                # overlay_offset=(0, 134),
            )
            base_image=result
        if text is not None and text != "":
            # 使用设置的字体大小作为最大字体大小
            max_font_height = font_size if font_size else 145
            
            # 调用绘制文本函数，它返回的是字节数据
            result = draw_text_auto(
                image_source=base_image,
                # image_overlay=None,
                top_left=text_box_topleft,
                bottom_right=image_box_bottomright,
                text=text,
                align="left",
                valign="top",
                color=(255, 255, 255),
                max_font_height=max_font_height,
                font_path=font_path,
                # overlay_offset=(0, 134),
                compression_settings=compression_settings
            )
        return result

    def generate_preview_image(
        self,
        character_name: str,
        background_index: int,
        emotion_index: int,
        preview_size: tuple = (400, 300),
    ) -> Image.Image:
        """生成预览图片 - 同时缓存基础图片用于快速生成"""
        try:
            # 生成基础图片
            base_image = self.generate_base_image_with_text(
                character_name, background_index, emotion_index
            )

            # 记录当前图片用于快速生成
            self.current_base_image = base_image#.copy()

            # 调整大小用于预览
            preview_image = base_image.copy()
            preview_image.thumbnail(preview_size, Image.Resampling.BILINEAR)

            return preview_image
        except Exception as e:
            print(f"生成预览图片失败: {e}")
            return Image.new("RGB", preview_size, color="gray")

    def get_random_background(self) -> int:
        """随机选择背景"""
        return random.randint(1, self.background_count)