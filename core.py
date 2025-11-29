"""魔裁文本框核心逻辑"""

import os
import time
import random
import psutil
from pynput.keyboard import Key, Controller
from sys import platform
import keyboard as kb_module

if platform.startswith("win"):
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
    """魔裁文本框核心类"""

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
        self.image_processor = ImageProcessor(
            self.config.BASE_PATH,
            self.config.BOX_RECT,
            self.text_configs_dict,
            self.mahoshojo,  # 传递角色元数据用于字体获取
        )

        # 状态变量
        self.selected_emotion = None
        self.selected_background = None
        self.last_emotion = -1
        self.current_character_index = 3

        # 预览相关
        self.preview_emotion = None
        self.preview_background = None

        # GUI设置
        self.gui_settings = self.config_loader.load_gui_settings()

    def load_configs(self):
        """加载所有配置"""
        self.mahoshojo = self.config_loader.load_chara_meta()
        self.character_list = list(self.mahoshojo.keys())
        self.text_configs_dict = self.config_loader.load_text_configs()
        self.keymap = self.config_loader.load_keymap(platform)
        self.process_whitelist = self.config_loader.load_process_whitelist(platform)

    def get_character(self, index: str | None = None, full_name: bool = False) -> str:
        """获取角色名称"""
        if index is not None:
            return self.mahoshojo[index]["full_name"] if full_name else index
        else:
            chara = self.character_list[self.current_character_index - 1]
            return self.mahoshojo[chara]["full_name"] if full_name else chara

    def switch_character(self, index: int) -> bool:
        """切换到指定索引的角色"""
        self.image_processor.clear_cache()
        if 0 < index <= len(self.character_list):
            self.current_character_index = index
            character_name = self.get_character()
            # 预加载角色图片到内存
            self.image_processor.preload_character_images(character_name)
            return True
        return False

    def get_current_font(self) -> str:
        """返回当前角色的字体文件绝对路径"""
        return self.image_processor.get_character_font(self.get_character())

    def get_current_emotion_count(self) -> int:
        """获取当前角色的表情数量"""
        return self.mahoshojo[self.get_character()]["emotion_count"]

    def get_character_list(self):
        """获取角色列表"""
        return self.character_list

    def get_character_name(self, index=None, full_name=False):
        """获取角色名称（兼容性方法）"""
        return self.get_character(index, full_name)

    def get_gui_settings(self):
        """获取GUI设置"""
        return self.gui_settings

    def save_gui_settings(self, settings):
        """保存GUI设置"""
        self.gui_settings = settings
        return self.config_loader.save_gui_settings(settings)

    def generate_preview(self, preview_size=(400, 300)) -> tuple:
        """生成预览图片和相关信息"""
        character_name = self.get_character()
        emotion_count = self.get_current_emotion_count()

        # 确定表情和背景
        emotion_index = (
            self._get_random_emotion(emotion_count)
            if self.selected_emotion is None
            else self.selected_emotion
        )
        background_index = (
            self.image_processor.get_random_background()
            if self.selected_background is None
            else self.selected_background
        )

        # 保存预览使用的表情和背景
        self.preview_emotion = emotion_index
        self.preview_background = background_index

        # 生成预览图片
        preview_image = self.image_processor.generate_preview_image(
            character_name, background_index, emotion_index, preview_size
        )

        # 构建预览信息 - 显示实际使用的索引值
        emotion_text = (
            f"{emotion_index}" if self.selected_emotion is None else f"{emotion_index}"
        )
        background_text = (
            f"{background_index}"
            if self.selected_background is None
            else f"{background_index}"
        )

        info = f"角色: {character_name}\n表情: {emotion_text}\n背景: {background_text}"

        return preview_image, info

    def _get_random_emotion(self, emotion_count: int) -> int:
        """随机选择表情（避免连续相同）"""
        if self.last_emotion == -1:
            emotion_index = random.randint(1, emotion_count)
        else:
            # 避免连续相同表情
            available_emotions = [
                i for i in range(1, emotion_count + 1) if i != self.last_emotion
            ]
            emotion_index = (
                random.choice(available_emotions)
                if available_emotions
                else self.last_emotion
            )

        self.last_emotion = emotion_index
        return emotion_index

    def _active_process_allowed(self) -> bool:
        """校验当前前台进程是否在白名单"""
        if not self.process_whitelist:
            return True

        wl = {name.lower() for name in self.process_whitelist}

        if platform.startswith("win"):
            try:
                hwnd = win32gui.GetForegroundWindow()
                if not hwnd:
                    return False
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                name = psutil.Process(pid).name().lower()
                return name in wl
            except (psutil.Error, OSError):
                return False

        elif platform == "darwin":
            try:
                import subprocess

                result = subprocess.run(
                    [
                        "osascript",
                        "-e",
                        'tell application "System Events" to get name of first process whose frontmost is true',
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
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

        if platform == "darwin":
            self.kbd_controller.press(Key.cmd)
            self.kbd_controller.press("a")
            self.kbd_controller.release("a")
            self.kbd_controller.press("x")
            self.kbd_controller.release("x")
            self.kbd_controller.release(Key.cmd)
        elif platform.startswith("win"):
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

        # 使用预览时确定的表情和背景，应该不会报错吧这个
        emotion_index, background_index = self.preview_emotion, self.preview_background
        # if hasattr(self, "preview_emotion") and self.preview_emotion is not None:
        #     emotion_index = self.preview_emotion

        # if hasattr(self, "preview_background") and self.preview_background is not None:
        #     background_index = self.preview_background

        # 获取剪切板内容
        text = self.cut_all_and_get_text()
        image = self.clipboard_manager.get_image_from_clipboard()
        # if image is None:
        #     print("剪贴板没有图像")
        #     if  self.clipboard_manager.has_image_in_clipboard():
        #         print("有图像")
        # if text == "":
        #     print("剪贴板没有文本")

        if text == "" and image is None:
            return "错误: 没有文本或图像"

        try:
            # 使用GUI中设置的对话框字体，而不是角色专用字体
            font_path = None
            font_family = self.gui_settings.get("font_family")
            font_size = self.gui_settings.get("font_size", 120)

            # 如果设置了字体家族，查找对应的字体文件
            if font_family:
                # 查找字体文件
                fonts_dir = os.path.join(self.config.BASE_PATH, "assets", "fonts")
                if os.path.exists(fonts_dir):
                    for file in os.listdir(fonts_dir):
                        # 检查文件名是否包含字体家族名称（不区分大小写）
                        if (
                            font_family.lower() in file.lower()
                            and file.lower().endswith((".ttf", ".otf", ".ttc"))
                        ):
                            font_path = os.path.join(fonts_dir, file)
                            break

                # 如果没找到匹配的字体文件，使用默认字体
                if not font_path:
                    font_path = self.get_current_font()  # 回退到角色专用字体
            else:
                font_path = self.get_current_font()  # 使用角色专用字体

            # 获取压缩设置
            compression_settings = self.gui_settings.get("image_compression", {})

            png_bytes = self.image_processor.generate_image_fast(
                character_name,
                # background_index,
                # emotion_index,
                text,
                image,
                font_path,  # 使用GUI设置的字体而不是角色专用字体
                font_size,
                compression_settings,  # 传递压缩设置
            )

        except Exception as e:
            return f"生成图像失败: {e}"

        if png_bytes is None:
            return "生成图像失败！"

        # 复制到剪贴板
        if not self.clipboard_manager.copy_image_to_clipboard(png_bytes):
            return "复制到剪贴板失败"

        # 等待剪贴板确认（最多等待2.5秒）
        max_wait_time = 2.5
        wait_interval = 0.1

        while max_wait_time > 0:
            # 检查剪贴板中是否有图片
            if self.clipboard_manager.has_image_in_clipboard():
                break
            time.sleep(wait_interval)
            max_wait_time -= wait_interval

        # 自动粘贴和发送
        if self.config.AUTO_PASTE_IMAGE:
            self.kbd_controller.press(Key.ctrl if platform != "darwin" else Key.cmd)
            self.kbd_controller.press("v")
            self.kbd_controller.release("v")
            self.kbd_controller.release(Key.ctrl if platform != "darwin" else Key.cmd)

            time.sleep(0.3)

            if self.config.AUTO_SEND_IMAGE:
                self.kbd_controller.press(Key.enter)
                self.kbd_controller.release(Key.enter)

        # 重置最后使用的表情，确保下次随机不会重复
        self.last_emotion = -1

        return f"成功生成图片！角色: {character_name}, 表情: {emotion_index}, 背景: {background_index}"
