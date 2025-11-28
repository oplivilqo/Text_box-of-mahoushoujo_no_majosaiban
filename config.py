"""配置管理模块"""
import os
import yaml


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, base_path):
        self.base_path = base_path
        self.config_path = os.path.join(base_path, "config")
        
    def load_chara_meta(self):
        """加载角色元数据"""
        with open(os.path.join(self.config_path, "chara_meta.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
            return config["mahoshojo"]
    
    def load_text_configs(self):
        """加载文本配置"""
        with open(os.path.join(self.config_path, "text_configs.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
            return config["text_configs"]
    
    def load_keymap(self, platform):
        """加载快捷键映射"""
        with open(os.path.join(self.config_path, "keymap.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
            return config.get(platform, {})
    
    def load_process_whitelist(self, platform):
        """加载进程白名单"""
        with open(os.path.join(self.config_path, "process_whitelist.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
            return config.get(platform, [])


class AppConfig:
    """应用配置类"""
    
    def __init__(self, base_path):
        self.BOX_RECT = ((728, 355), (2339, 800))  # 文本框区域坐标
        self.KEY_DELAY = 0.1  # 按键延迟
        self.AUTO_PASTE_IMAGE = True
        self.AUTO_SEND_IMAGE = True
        self.BASE_PATH = base_path
        self.ASSETS_PATH = os.path.join(base_path, "assets")
        # self.CACHE_PATH = os.path.join(self.ASSETS_PATH, "cache")
        
        # 确保缓存目录存在
        # os.makedirs(self.CACHE_PATH, exist_ok=True)