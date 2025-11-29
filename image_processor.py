"""图片处理模块 - 优化版本"""

import os
import random
import io
from PIL import Image, ImageDraw, ImageFont

from text_fit_draw import draw_text_auto
from image_fit_paste import paste_image_auto


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

        # 缓存系统
        self.background_cache = {}
        self.character_cache = {}
        self.base_image_cache = {}

        # 字体缓存
        self.font_cache = {}

        # 当前预览的基础图片（用于快速生成）
        self.current_base_image = None
        self.current_base_key = None

    def _compress_image(self, image: Image.Image, compression_settings: dict) -> Image.Image:
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
                
                # 使用高质量下采样
                compressed_image = compressed_image.resize(
                    (new_width, new_height), 
                    Image.Resampling.LANCZOS
                )
        
        return compressed_image

    def _load_background(self, background_index: int) -> Image.Image:
        """加载背景图片到缓存"""
        if background_index not in self.background_cache:
            background_path = os.path.join(
                self.base_path, "assets", "background", f"c{background_index}.png"
            )
            if os.path.exists(background_path):
                self.background_cache[background_index] = Image.open(
                    background_path
                ).convert("RGBA")
            else:
                # 如果背景文件不存在，创建一个默认的背景
                self.background_cache[background_index] = Image.new(
                    "RGBA", (800, 600), (100, 100, 200)
                )
        return self.background_cache[background_index].copy()

    def _load_character_image(
        self, character_name: str, emotion_index: int
    ) -> Image.Image:
        """加载角色图片"""
        # 检查缓存
        cache_key = f"{character_name}_{emotion_index}"
        if cache_key in self.character_cache:
            return self.character_cache[cache_key].copy()

        # 缓存未命中，从文件加载
        overlay_path = os.path.join(
            self.base_path,
            "assets",
            "chara",
            character_name,
            f"{character_name} ({emotion_index}).png",
        )

        if os.path.exists(overlay_path):
            image = Image.open(overlay_path).convert("RGBA")
            self.character_cache[cache_key] = image
            return image.copy()
        else:
            # 如果角色图片不存在，创建一个透明的占位图
            placeholder = Image.new("RGBA", (800, 600), (0, 0, 0, 0))
            self.character_cache[cache_key] = placeholder
            return placeholder.copy()

    def preload_character_images(self, character_name: str):
        """预加载角色图片到内存"""
        if character_name not in self.mahoshojo:
            return

        emotion_count = self.mahoshojo[character_name].get("emotion_count", 0)

        for emotion_index in range(1, emotion_count + 1):
            # 触发加载并缓存
            self._load_character_image(character_name, emotion_index)

    def get_character_font(self, character_name: str) -> str:
        """获取角色字体文件路径"""
        if character_name in self.mahoshojo:
            font_file = self.mahoshojo[character_name].get("font", "font3.ttf")
            return os.path.join(self.base_path, "assets", "fonts", font_file)
        else:
            # 默认字体
            return os.path.join(self.base_path, "assets", "fonts", "font3.ttf")

    def _get_font(self, font_path: str, font_size: int) -> ImageFont.FreeTypeFont:
        """获取字体对象，带缓存"""
        cache_key = f"{font_path}_{font_size}"
        if cache_key not in self.font_cache:
            try:
                self.font_cache[cache_key] = ImageFont.truetype(font_path, font_size)
            except Exception as e:
                print(f"加载字体失败 {font_path}: {e}")
                # 回退到默认字体
                default_font_path = os.path.join(
                    self.base_path, "assets", "fonts", "font3.ttf"
                )
                try:
                    self.font_cache[cache_key] = ImageFont.truetype(
                        default_font_path, font_size
                    )
                except:
                    self.font_cache[cache_key] = ImageFont.load_default()
        return self.font_cache[cache_key]

    def _get_available_fonts(self):
        """获取可用的字体列表"""
        font_dir = os.path.join(self.base_path, "assets", "fonts")
        project_fonts = []
        system_fonts = []
        
        # 获取项目字体
        if os.path.exists(font_dir):
            for file in os.listdir(font_dir):
                if file.lower().endswith(('.ttf', '.otf', '.ttc')):
                    project_fonts.append(os.path.join(font_dir, file))
        
        # 获取系统字体（作为备选）
        # 这里可以添加系统字体扫描逻辑，但为了简化，我们只返回项目字体
        # 实际使用时可以根据需要添加系统字体扫描
        
        return project_fonts, system_fonts

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
        result = background#.copy()
        result.paste(overlay, (0, 134), overlay)

        # 添加角色名称文字 - 使用角色专用字体，保持不变
        if self.text_configs_dict and character_name in self.text_configs_dict:
            draw = ImageDraw.Draw(result)
            shadow_offset = (2, 2)
            shadow_color = (0, 0, 0)

            for config in self.text_configs_dict[character_name]:
                text = config["text"]
                position = tuple(config["position"])
                font_color = tuple(config["font_color"])
                font_size = config["font_size"]

                # 使用角色专用字体（保持不变）
                font_path = self.get_character_font(character_name)
                font = self._get_font(font_path, font_size)

                # 绘制阴影文字
                shadow_position = (
                    position[0] + shadow_offset[0],
                    position[1] + shadow_offset[1],
                )
                draw.text(shadow_position, text, fill=shadow_color, font=font)

                # 绘制主文字
                draw.text(position, text, fill=font_color, font=font)

        self.base_image_cache[cache_key] = result
        return result#.copy()

    def generate_image_fast(
        self,
        character_name: str,
        # background_index: int,
        # emotion_index: int,
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
            # 使用设置的字体大小作为最大字体大小
            max_font_height = font_size if font_size else 145
            
            # 调用绘制文本函数，它返回的是字节数据
            result = draw_text_auto(
                image_source=base_image,
                image_overlay=None,
                top_left=text_box_topleft,
                bottom_right=image_box_bottomright,
                text=text,
                align="left",
                valign="top",
                color=(255, 255, 255),
                max_font_height=max_font_height,
                font_path=font_path,
                role_name=character_name,
                text_configs_dict=self.text_configs_dict,
                base_path=self.base_path,
                overlay_offset=(0, 134),
            )

        # 统一处理结果
        if isinstance(result, bytes):
            # 如果是字节数据，转换为图像进行处理
            result_image = Image.open(io.BytesIO(result))
        elif isinstance(result, Image.Image):
            # 如果是图像对象，直接使用
            result_image = result
        else:
            raise ValueError(f"返回了未知类型: {type(result)}")

        # 应用压缩
        if compression_settings and compression_settings.get("pixel_reduction_enabled", False):
            result_image = self._compress_image(result_image, compression_settings)

        # 转换为PNG字节
        output_bytes = io.BytesIO()
        result_image.save(output_bytes, format="PNG")
        return output_bytes.getvalue()

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
            self.current_base_image = base_image#.copy()
            self.current_base_key = (
                f"{character_name}_{background_index}_{emotion_index}"
            )

            # 调整大小用于预览
            preview_image = base_image.copy()
            preview_image.thumbnail(preview_size, Image.Resampling.LANCZOS)

            return preview_image
        except Exception as e:
            print(f"生成预览图片失败: {e}")
            return Image.new("RGB", preview_size, color="gray")

    def get_random_background(self) -> int:
        """随机选择背景"""
        return random.randint(1, self.background_count)

    def clear_cache(self):
        """清理缓存以释放内存"""
        self.background_cache.clear()
        self.character_cache.clear()
        self.base_image_cache.clear()
        # self.font_cache.clear()
        self.current_base_image = None
        self.current_base_key = None