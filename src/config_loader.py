"""配置加载模块"""
import os
import yaml
from sys import platform

PLATFORM = platform.lower()


class ConfigLoader:
    """配置加载器"""

    def __init__(self, base_path: str):
        self.base_path = base_path
        self.config_path = os.path.join(base_path, "config")
        self.assets_path = os.path.join(base_path, "assets")

    def load_chara_meta(self) -> tuple[dict, list, dict]:
        """
        从各个角色文件夹中的meta.yml加载配置
        Returns:
            (mahoshojo, character_list, text_configs_dict)
        """
        mahoshojo = {}
        chara_base_path = os.path.join(self.assets_path, "chara")

        if not os.path.exists(chara_base_path):
            print("[red]错误: 角色文件夹不存在[/red]")
            return {}, [], {}

        for chara_name in os.listdir(chara_base_path):
            chara_dir = os.path.join(chara_base_path, chara_name)
            if not os.path.isdir(chara_dir):
                continue
            meta_file = os.path.join(chara_dir, "meta.yml")

            if not os.path.exists(meta_file):
                print(f"[yellow]警告: {chara_name} 文件夹中没有 meta.yml，已跳过[/yellow]")
                continue

            try:
                with open(meta_file, 'r', encoding="utf-8") as fp:
                    meta = yaml.safe_load(fp)

                    if not all(key in meta for key in ['full_name', 'font']):
                        print(f"[yellow]警告: {chara_name} 的 meta.yml 缺少必需字段，已跳过[/yellow]")
                        continue

                    # 支持 png、jpg、jpeg 格式
                    image_files = [f for f in os.listdir(chara_dir)
                                   if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                    emotion_cnt = len(image_files)
                    if emotion_cnt == 0:
                        print(f"[yellow]警告: {chara_name} 文件夹中没有图片文件（PNG/JPG），已跳过[/yellow]")
                        continue
                    meta['emotion_count'] = emotion_cnt
                    mahoshojo[chara_name] = meta

            except Exception as e:
                print(f"[yellow]警告: 加载 {chara_name} 的 meta.yml 失败: {e}[/yellow]")
                continue

        character_list = list(mahoshojo.keys())

        text_configs_dict = {}
        for chara_name, meta in mahoshojo.items():
            if 'text_config' in meta:
                text_configs_dict[chara_name] = meta['text_config']

        return mahoshojo, character_list, text_configs_dict

    def load_keymap(self) -> dict:
        """加载快捷键配置"""
        with open(os.path.join(self.config_path, "keymap.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
            return config.get(PLATFORM, {})

    def load_process_whitelist(self) -> list:
        """加载进程白名单"""
        with open(os.path.join(self.config_path, "process_whitelist.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
            return config.get(PLATFORM, [])

