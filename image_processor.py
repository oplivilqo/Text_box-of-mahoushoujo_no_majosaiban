"""图片处理模块 - 优化版本"""

import os
import random
import io
from PIL import Image, ImageDraw, ImageFont
from typing import Optional

from text_fit_draw import draw_text_auto
from image_fit_paste import paste_image_auto


class ImageProcessor:
    """图片处理器 - 优化版本"""

    def __init__(self, base_path: str, box_rect: tuple, text_configs_dict: dict):
        self.base_path = base_path
        self.box_rect = box_rect
        self.text_configs_dict = text_configs_dict
        self.background_count = 16

        # 缓存预生成的带文字的基础图片
        self.base_image_cache = {}

        # 缓存背景图片
        self.background_cache = {}

        # 当前预览的基础图片（用于快速生成）
        self.current_base_image = None
        self.current_base_key = None

    def _load_background(self, background_index: int) -> Image.Image:
        """加载背景图片到缓存"""
        if background_index not in self.background_cache:
            background_path = os.path.join(
                self.base_path, "assets", "background", f"c{background_index}.png"
            )
            self.background_cache[background_index] = Image.open(
                background_path
            ).convert("RGBA")
        return self.background_cache[background_index] #.copy()

    def _load_character_image(
        self, character_name: str, emotion_index: int
    ) -> Image.Image:
        """加载角色图片"""

        #缓存未命中
        overlay_path = os.path.join(
            self.base_path,
            "assets",
            "chara",
            character_name,
            f"{character_name} ({emotion_index}).png",
        )
        return Image.open(overlay_path).convert("RGBA")

    def generate_base_image_with_text(
        self, character_name: str, background_index: int, emotion_index: int
    ) -> Image.Image:
        """生成带角色文字的基础图片"""
        cache_key = f"{character_name}_{background_index}_{emotion_index}"

        if cache_key in self.base_image_cache:
            return self.base_image_cache[cache_key].copy()

        # 生成基础图片（包含角色名称文字）
        background = self._load_background(background_index)
        overlay = self._load_character_image(character_name, emotion_index)

        # 合成基础图片
        result = background.copy()
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

                font_dir = os.path.join(self.base_path, "assets", "fonts")
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

        self.base_image_cache[cache_key] = result
        return result #.copy()

    # def generate_image_directly(
    #     self,
    #     character_name: str,
    #     background_index: int,
    #     emotion_index: int,
    #     text: str = None,
    #     content_image: Image.Image = None,
    #     font_path: str = None,
    # ) -> bytes:
    #     """直接生成图片"""
    #     # 获取预生成的基础图片
    #     base_image = self.generate_base_image_with_text(
    #         character_name, background_index, emotion_index
    #     )

    #     text_box_topleft = (self.box_rect[0][0], self.box_rect[0][1])
    #     image_box_bottomright = (self.box_rect[1][0], self.box_rect[1][1])

    #     if content_image is not None:
    #         return paste_image_auto(
    #             image_source=base_image,
    #             image_overlay=None,
    #             top_left=text_box_topleft,
    #             bottom_right=image_box_bottomright,
    #             content_image=content_image,
    #             align="center",
    #             valign="middle",
    #             padding=12,
    #             allow_upscale=True,
    #             keep_alpha=True,
    #             role_name=character_name,
    #             text_configs_dict=self.text_configs_dict,
    #             base_path=self.base_path,
    #             overlay_offset=(0, 134),
    #         )
    #     elif text is not None and text != "":
    #         return draw_text_auto(
    #             image_source=base_image,
    #             image_overlay=None,
    #             top_left=text_box_topleft,
    #             bottom_right=image_box_bottomright,
    #             text=text,
    #             align="left",
    #             valign="top",
    #             color=(255, 255, 255),
    #             max_font_height=145,
    #             font_path=font_path,
    #             role_name=character_name,
    #             text_configs_dict=self.text_configs_dict,
    #             base_path=self.base_path,
    #             overlay_offset=(0, 134),
    #         )
    #     else:
    #         raise ValueError("没有文本或图像内容")

    def generate_image_fast(
        self,
        character_name: str,
        # background_index: int,
        # emotion_index: int,
        text: str = None,
        content_image: Image.Image = None,
        font_path: str = None,
    ) -> bytes:
        """快速生成图片 - 使用当前预览的基础图片"""
        # cache_key = f"{character_name}_{background_index}_{emotion_index}"

        # 如果当前缓存的基础图片与目标一致，直接使用
        # if self.current_base_key == cache_key and self.current_base_image:
            # base_image = self.current_base_image.copy()
        # else:
        #     # 否则生成新的基础图片
        #     base_image = self.generate_base_image_with_text(
        #         character_name, background_index, emotion_index
        #     )
        #     self.current_base_image = base_image.copy()
        #     self.current_base_key = cache_key

        text_box_topleft = (self.box_rect[0][0], self.box_rect[0][1])
        image_box_bottomright = (self.box_rect[1][0], self.box_rect[1][1])

        if content_image is not None:
            return paste_image_auto(
                image_source=self.current_base_image,
                image_overlay=None,
                top_left=text_box_topleft,
                bottom_right=image_box_bottomright,
                content_image=content_image,
                align="center",
                valign="middle",
                padding=12,
                allow_upscale=True,
                keep_alpha=True,
                role_name=character_name,
                text_configs_dict=self.text_configs_dict,
                base_path=self.base_path,
                overlay_offset=(0, 134),
            )
        elif text is not None and text != "":
            return draw_text_auto(
                image_source=self.current_base_image,
                image_overlay=None,
                top_left=text_box_topleft,
                bottom_right=image_box_bottomright,
                text=text,
                align="left",
                valign="top",
                color=(255, 255, 255),
                max_font_height=145,
                font_path=font_path,
                role_name=character_name,
                text_configs_dict=self.text_configs_dict,
                base_path=self.base_path,
                overlay_offset=(0, 134),
            )
        else:
            raise ValueError("没有文本或图像内容")

    def generate_preview_image(
        self,
        character_name: str,
        background_index: int,
        emotion_index: int,
        preview_size: tuple = (400, 300),
    ) -> Image.Image:
        """生成预览图片 - 同时缓存基础图片用于快速生成"""
        try:
            # 生成基础图片并缓存
            base_image = self.generate_base_image_with_text(
                character_name, background_index, emotion_index
            )

            # 缓存当前基础图片用于快速生成
            self.current_base_image = base_image #.copy()
            self.current_base_key = (
                f"{character_name}_{background_index}_{emotion_index}"
            )

            # 调整大小用于预览
            preview_image = base_image #.copy()
            preview_image.thumbnail(preview_size, Image.Resampling.LANCZOS)

            return preview_image
        except Exception as e:
            print(f"生成预览图片失败: {e}")
            return Image.new("RGB", preview_size, color="gray")

    def get_random_background(self) -> int:
        """随机选择背景"""
        return random.randint(1, self.background_count)
