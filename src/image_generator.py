"""图片生成模块"""
import os
import random
from PIL import Image

BG_CNT = 16 # 背景图片数量

class ImageGenerator:
    """图片生成器"""

    def __init__(self, base_path: str, cache_path: str):
        self.base_path = base_path
        self.cache_path = cache_path
        os.makedirs(self.cache_path, exist_ok=True)

    def generate_and_save_images(self, character_name: str, emotion_cnt: int,
                                  progress_callback=None) -> None:
        """生成并保存指定角色的所有表情图片"""
        # 检查是否已经生成过
        for filename in os.listdir(self.cache_path):
            if filename.startswith(character_name):
                return

        total_images = BG_CNT * emotion_cnt

        for j in range(emotion_cnt):
            for i in range(BG_CNT):
                background_path = os.path.join(
                    self.base_path, 'assets', "background", f"c{i + 1}.png"
                )
                overlay_path = os.path.join(
                    self.base_path, 'assets', 'chara', character_name,
                    f"{character_name} ({j + 1}).png"
                )

                background = Image.open(background_path).convert("RGBA")
                overlay = Image.open(overlay_path).convert("RGBA")

                img_num = j * BG_CNT + i + 1
                result = background.copy()
                result.paste(overlay, (0, 134), overlay)

                save_path = os.path.join(
                    self.cache_path, f"{character_name} ({img_num}).jpg"
                )
                result.convert("RGB").save(save_path)

                if progress_callback:
                    progress_callback(j * BG_CNT + i + 1, total_images)

    def get_random_image_name(self, character_name: str, emotion_cnt: int,
                              emote: int | None, value_1: int) -> tuple[str, int]:
        """
        随机获取表情图片名称
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

