"""图片生成模块"""
import os
import random
from collections import OrderedDict
from PIL import Image

BG_CNT = 16  # 背景图片数量

class ImageGenerator:
    """图片生成器（内存缓存版本）"""

    def __init__(self, base_path: str, cache_path: str, max_cached_chars: int = 3):
        self.IMG_SETTINGS = {
            # 角色图尺寸限制
            "avatar_width": 800,
            "avatar_height": 700,
        }
        self.base_path = base_path
        self.cache_path = cache_path
        self.max_cached_chars = max_cached_chars
        os.makedirs(self.cache_path, exist_ok=True)

        # 内存缓存
        self._bg_cache: list[Image.Image] = []  # 背景图缓存（16张）
        self._char_cache: OrderedDict[str, list[Image.Image]] = OrderedDict()  # 角色表情缓存（LRU）

        # 预加载所有背景
        self._preload_backgrounds()

    def _preload_backgrounds(self) -> None:
        """预加载所有背景图到内存"""
        self._bg_cache.clear()
        for i in range(BG_CNT):
            # 尝试多种图片格式
            bg_path = None
            for ext in ['.png', '.jpg', '.jpeg']:
                candidate = os.path.join(
                    self.base_path, 'assets', "background", f"c{i + 1}{ext}"
                )
                if os.path.exists(candidate):
                    bg_path = candidate
                    break

            if bg_path is None:
                raise FileNotFoundError(
                    f"找不到背景图 c{i + 1} 文件（支持PNG/JPG/JPEG格式）"
                )

            bg_img = Image.open(bg_path).convert("RGBA")
            self._bg_cache.append(bg_img)

    def _load_character_emotions(self, character_name: str, emotion_cnt: int) -> list[Image.Image]:
        """加载指定角色的所有表情到内存"""
        emotions = []
        for j in range(emotion_cnt):
            avatar_path = None
            for ext in ['.png', '.jpg', '.jpeg']:
                candidate = os.path.join(
                    self.base_path, 'assets', 'chara', character_name,
                    f"{character_name} ({j + 1}){ext}"
                )
                if os.path.exists(candidate):
                    avatar_path = candidate
                    break

            if avatar_path is None:
                raise FileNotFoundError(
                    f"找不到角色 {character_name} 的表情 {j + 1} 图片文件（支持PNG/JPG/JPEG格式）"
                )

            avatar = self.fit_image(Image.open(avatar_path).convert("RGBA"))
            emotions.append(avatar)
        return emotions

    def _ensure_character_loaded(self, character_name: str, emotion_cnt: int) -> None:
        """确保角色已加载到缓存，使用LRU策略"""
        if character_name in self._char_cache:
            # 移到最后（最近使用）
            self._char_cache.move_to_end(character_name)
            return

        # 加载角色
        emotions = self._load_character_emotions(character_name, emotion_cnt)
        self._char_cache[character_name] = emotions

        # LRU淘汰
        while len(self._char_cache) > self.max_cached_chars:
            self._char_cache.popitem(last=False)

    def fit_image(self, img: Image.Image) -> Image.Image:
        """
        调整图像大小以适应尺寸限制
        保持原图比例不变进行缩放
        """
        max_w, max_h = self.IMG_SETTINGS['avatar_width'], self.IMG_SETTINGS['avatar_height']
        w, h = img.size

        # 计算缩放比例，取较小的那个以确保两个维度都不超限
        scale = min(max_w / w, max_h / h)

        new_w = int(w * scale)
        new_h = int(h * scale)

        return img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    def generate_image_in_memory(self, character_name: str, emotion_cnt: int,
                                  emotion_idx: int, bg_idx: int) -> Image.Image:
        """
        在内存中生成单张图片（不保存到磁盘）
        Args:
            character_name: 角色名称
            emotion_cnt: 表情总数
            emotion_idx: 表情索引（0-based）
            bg_idx: 背景索引（0-based）
        Returns:
            PIL.Image对象（RGB模式）
        """
        # 确保角色已加载
        self._ensure_character_loaded(character_name, emotion_cnt)

        # 获取背景和角色
        background = self._bg_cache[bg_idx]
        avatar = self._char_cache[character_name][emotion_idx]

        # 合成图像
        target_x = 0  # 左侧对齐
        target_y = background.size[1] - avatar.size[1]  # 底端对齐

        result = background.copy()
        result.paste(avatar, (target_x, target_y), avatar)

        return result.convert("RGB")

    def generate_and_save_images(self, character_name: str, emotion_cnt: int,
                                  progress_callback=None) -> None:
        """生成并保存指定角色的所有表情图片（兼容旧版，仍保存到磁盘）"""
        # 检查是否已经生成过
        for filename in os.listdir(self.cache_path):
            if filename.startswith(character_name):
                return

        # 确保角色已加载到内存
        self._ensure_character_loaded(character_name, emotion_cnt)

        total_images = BG_CNT * emotion_cnt

        for j in range(emotion_cnt):
            for i in range(BG_CNT):
                # 使用内存合成
                result = self.generate_image_in_memory(character_name, emotion_cnt, j, i)

                img_num = j * BG_CNT + i + 1
                save_path = os.path.join(
                    self.cache_path, f"{character_name} ({img_num}).jpg"
                )
                result.save(save_path)

                if progress_callback:
                    progress_callback(j * BG_CNT + i + 1, total_images)

    def get_random_image(self, character_name: str, emotion_cnt: int,
                         emote: int | None, value_1: int) -> tuple[Image.Image, int]:
        """
        随机获取表情图片（内存模式）
        Args:
            character_name: 角色名称
            emotion_cnt: 表情总数
            emote: 指定表情（1-based），None表示随机
            value_1: 上一次的图片序号（用于避免重复）
        Returns:
            (PIL.Image对象, new_value_1)
        """
        # 确保角色已加载
        self._ensure_character_loaded(character_name, emotion_cnt)

        total_images = BG_CNT * emotion_cnt

        if emote:
            i = random.randint((emote - 1) * BG_CNT + 1, emote * BG_CNT)
        else:
            max_attempts = 100
            attempts = 0
            i = random.randint(1, total_images)

            while attempts < max_attempts:
                i = random.randint(1, total_images)
                current_emotion = (i - 1) // BG_CNT

                if value_1 == -1:
                    break

                if current_emotion != (value_1 - 1) // BG_CNT:
                    break

                attempts += 1

        # 计算表情和背景索引（0-based）
        emotion_idx = (i - 1) // BG_CNT
        bg_idx = (i - 1) % BG_CNT

        # 生成图像
        img = self.generate_image_in_memory(character_name, emotion_cnt, emotion_idx, bg_idx)

        return img, i

    def get_random_image_name(self, character_name: str, emotion_cnt: int,
                              emote: int | None, value_1: int) -> tuple[str, int]:
        """
        随机获取表情图片名称（兼容旧版API）
        Returns:
            (image_name, new_value_1)
        """
        total_images = BG_CNT * emotion_cnt

        if emote:
            i = random.randint((emote - 1) * BG_CNT + 1, emote * BG_CNT)
            return f"{character_name} ({i})", i

        max_attempts = 100
        attempts = 0
        i = random.randint(1, total_images)

        while attempts < max_attempts:
            i = random.randint(1, total_images)
            current_emotion = (i - 1) // BG_CNT

            if value_1 == -1:
                return f"{character_name} ({i})", i

            if current_emotion != (value_1 - 1) // BG_CNT:
                return f"{character_name} ({i})", i

            attempts += 1

        return f"{character_name} ({i})", i

    def delete_cache(self) -> None:
        """删除缓存文件夹中的所有jpg文件"""
        for filename in os.listdir(self.cache_path):
            if filename.lower().endswith('.jpg'):
                os.remove(os.path.join(self.cache_path, filename))

    def clear_memory_cache(self) -> None:
        """清空内存中的角色缓存（背景缓存保留）"""
        self._char_cache.clear()

    def get_cache_info(self) -> dict:
        """获取缓存信息"""
        return {
            'bg_cached': len(self._bg_cache),
            'chars_cached': list(self._char_cache.keys()),
            'chars_cnt': len(self._char_cache),
            'max_chars': self.max_cached_chars
        }

