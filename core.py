"""魔裁文本框核心逻辑 - 优化版本"""
import os
import time
import random
import psutil
import threading
import io
from pynput.keyboard import Key, Controller
from sys import platform
import keyboard as kb_module
from PIL import Image

if platform.startswith('win'):
    try:
        import win32gui
        import win32process
    except ImportError:
        print("[red]请先安装 Windows 运行库: pip install pywin32[/red]")
        raise

from config import ConfigLoader, AppConfig
from clipboard_utils import ClipboardManager
from image_processor import ImageProcessor


class ManosabaCore:
    """魔裁文本框核心类 - 优化版本"""

    def __init__(self):
        # 初始化配置
        self.config = AppConfig(os.path.dirname(os.path.abspath(__file__)))
        self.kbd_controller = Controller()
        self.clipboard_manager = ClipboardManager()

        # 加载配置
        self.config_loader = ConfigLoader(self.config.BASE_PATH)
        self.mahoshojo = {}
        self.text_configs_dict = {}
        self.character_list = []
        self.keymap = {}
        self.process_whitelist = []
        self.load_configs()

        # 初始化图片处理器
        self.image_processor = ImageProcessor(self.config.BASE_PATH, self.config.BOX_RECT, self.text_configs_dict)

        # 状态变量
        self.selected_emotion = None
        self.selected_background = None
        self.last_emotion = -1
        self.current_character_index = 3
        
        # 预览相关
        self.preview_emotion = None
        self.preview_background = None
        
        # 角色图片缓存
        self.character_cache = {}
        
        # 当前预览的基础图片缓存（用于快速生成）
        self.current_base_image = None
        self.current_base_image_key = None
        
        # 启动热键监听线程
        self.hotkey_thread = threading.Thread(target=self._setup_hotkeys, daemon=True)
        self.hotkey_thread.start()

    def load_configs(self):
        """加载所有配置"""
        self.mahoshojo = self.config_loader.load_chara_meta()
        self.character_list = list(self.mahoshojo.keys())
        self.text_configs_dict = self.config_loader.load_text_configs()
        self.keymap = self.config_loader.load_keymap(platform)
        self.process_whitelist = self.config_loader.load_process_whitelist(platform)

    def _setup_hotkeys(self):
        """设置全局热键"""
        if platform.startswith('win'):
            try:
                import keyboard
                hotkey = self.keymap.get('start_generate', 'ctrl+alt+g')
                keyboard.add_hotkey(hotkey, self.generate_image)
            except ImportError:
                print("键盘模块不可用，热键功能禁用")

    def get_character(self, index: str | None = None, full_name: bool = False) -> str:
        """获取角色名称"""
        if index is not None:
            return self.mahoshojo[index]['full_name'] if full_name else index
        else:
            chara = self.character_list[self.current_character_index - 1]
            return self.mahoshojo[chara]['full_name'] if full_name else chara

    def switch_character(self, index: int) -> bool:
        """切换到指定索引的角色"""
        if 0 < index <= len(self.character_list):
            self.current_character_index = index
            character_name = self.get_character()
            # 预加载角色图片到内存
            self._preload_character_images(character_name)
            return True
        return False

    def _preload_character_images(self, character_name: str):
        """预加载角色图片到内存"""
        if character_name not in self.character_cache:
            self.character_cache[character_name] = {}
            emotion_count = self.get_current_emotion_count()
            
            for emotion_index in range(1, emotion_count + 1):
                overlay_path = os.path.join(
                    self.config.BASE_PATH, 'assets', 'chara', character_name,
                    f"{character_name} ({emotion_index}).png"
                )
                if os.path.exists(overlay_path):
                    try:
                        self.character_cache[character_name][emotion_index] = Image.open(overlay_path).convert("RGBA")
                    except Exception as e:
                        print(f"加载角色图片失败 {overlay_path}: {e}")

    def get_current_font(self) -> str:
        """返回当前角色的字体文件绝对路径"""
        return os.path.join(self.config.BASE_PATH, 'assets', 'fonts',
                           self.mahoshojo[self.get_character()]["font"])

    def get_current_emotion_count(self) -> int:
        """获取当前角色的表情数量"""
        return self.mahoshojo[self.get_character()]["emotion_count"]

    def delete_cache(self) -> None:
        """删除缓存"""
        for filename in os.listdir(self.config.CACHE_PATH):
            if filename.lower().endswith('.jpg'):
                os.remove(os.path.join(self.config.CACHE_PATH, filename))

    def generate_preview(self, preview_size=(400, 300)) -> tuple:
        """生成预览图片和相关信息"""
        character_name = self.get_character()
        emotion_count = self.get_current_emotion_count()
        
        # 确定表情和背景
        if self.selected_emotion is None:
            emotion_index = self._get_random_emotion(emotion_count)
        else:
            emotion_index = self.selected_emotion
            
        if self.selected_background is None:
            background_index = self.image_processor.get_random_background()
        else:
            background_index = self.selected_background
        
        # 保存预览使用的表情和背景
        self.preview_emotion = emotion_index
        self.preview_background = background_index
        
        # 生成预览图片
        preview_image = self.image_processor.generate_preview_image(
            character_name, background_index, emotion_index, preview_size
        )
        
        # 构建预览信息
        emotion_text = "随机" if self.selected_emotion is None else f"{emotion_index}"
        background_text = "随机" if self.selected_background is None else f"{background_index}"
        
        info = f"角色: {character_name}\n表情: {emotion_text}\n背景: {background_text}"
        
        return preview_image, info

    def _get_random_emotion(self, emotion_count: int) -> int:
        """随机选择表情（避免连续相同）"""
        if self.last_emotion == -1:
            emotion_index = random.randint(1, emotion_count)
        else:
            # 避免连续相同表情
            available_emotions = [i for i in range(1, emotion_count + 1) if i != self.last_emotion]
            emotion_index = random.choice(available_emotions) if available_emotions else self.last_emotion
        
        self.last_emotion = emotion_index
        return emotion_index

    def _active_process_allowed(self) -> bool:
        """校验当前前台进程是否在白名单"""
        if not self.process_whitelist:
            return True

        wl = {name.lower() for name in self.process_whitelist}

        if platform.startswith('win'):
            try:
                hwnd = win32gui.GetForegroundWindow()
                if not hwnd:
                    return False
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                name = psutil.Process(pid).name().lower()
                return name in wl
            except (psutil.Error, OSError):
                return False

        elif platform == 'darwin':
            try:
                import subprocess
                result = subprocess.run(
                    ["osascript", "-e",
                     'tell application "System Events" to get name of first process whose frontmost is true'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                name = result.stdout.strip().lower()
                return name in wl
            except subprocess.SubprocessError:
                return False

        else:
            # Linux 支持
            return True

    def cut_all_and_get_text(self) -> str:
        """模拟全选和剪切操作，返回剪切得到的文本内容"""
        self.clipboard_manager.copy_text_to_clipboard("")
        
        if platform == 'darwin':
            self.kbd_controller.press(Key.cmd)
            self.kbd_controller.press('a')
            self.kbd_controller.release('a')
            self.kbd_controller.press('x')
            self.kbd_controller.release('x')
            self.kbd_controller.release(Key.cmd)
        elif platform.startswith('win'):
            kb_module.send("CTRL+A")
            kb_module.send("CTRL+X")
        
        # 增加重试机制来确保剪贴板中有内容
        new_clip = ""
        max_retries = 3
        for attempt in range(max_retries):
            time.sleep(self.config.KEY_DELAY)
            new_clip = self.clipboard_manager.get_text_from_clipboard()
            if new_clip.strip():
                break
            elif attempt < max_retries - 1:
                time.sleep(self.config.KEY_DELAY * (attempt + 1))

        return new_clip.strip()

    def generate_image(self) -> str:
        """生成并发送图片 - 优化版本"""
        if not self._active_process_allowed():
            return "前台应用不在白名单内"
        
        character_name = self.get_character()
        
        # 使用预览时确定的表情和背景，确保一致
        if self.preview_emotion is not None:
            emotion_index = self.preview_emotion
        elif self.selected_emotion is None:
            emotion_index = self._get_random_emotion(self.get_current_emotion_count())
        else:
            emotion_index = self.selected_emotion
            
        if self.preview_background is not None:
            background_index = self.preview_background
        elif self.selected_background is None:
            background_index = self.image_processor.get_random_background()
        else:
            background_index = self.selected_background

        # 获取内容
        text = self.cut_all_and_get_text()
        image = self.clipboard_manager.get_image_from_clipboard()

        if text == "" and image is None:
            return "错误: 没有文本或图像"

        try:
            # 使用快速生成方法
            png_bytes = self.image_processor.generate_image_fast(
                character_name, background_index, emotion_index, 
                text, image, self.get_current_font()
            )
        except Exception as e:
            return f"生成图像失败: {e}"

        if png_bytes is None:
            return "生成图像失败！"

        # 复制到剪贴板
        if not self.clipboard_manager.copy_image_to_clipboard(png_bytes):
            return "复制到剪贴板失败"

        # 自动粘贴和发送
        if self.config.AUTO_PASTE_IMAGE:
            self.kbd_controller.press(Key.ctrl if platform != 'darwin' else Key.cmd)
            self.kbd_controller.press('v')
            self.kbd_controller.release('v')
            self.kbd_controller.release(Key.ctrl if platform != 'darwin' else Key.cmd)

            time.sleep(0.3)

            if self.config.AUTO_SEND_IMAGE:
                self.kbd_controller.press(Key.enter)
                self.kbd_controller.release(Key.enter)

        # 重置预览状态
        # 保存当前生成使用的值，用于返回信息
        used_emotion = emotion_index
        used_background = background_index
        
        # 强制重置预览状态，确保下次预览会重新生成
        self.preview_emotion = None
        self.preview_background = None
        # 重置最后使用的表情，确保下次随机不会重复
        self.last_emotion = -1

        return f"成功生成图片！角色: {character_name}, 表情: {used_emotion}, 背景: {used_background}"