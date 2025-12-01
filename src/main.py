import psutil
from pynput.keyboard import GlobalHotKeys
import os
from sys import platform

from rich import print

from config_loader import ConfigLoader
from image_generator import ImageGenerator
from image_generator import BG_CNT
from clipboard_handler import ClipboardHandler
from drawutils import draw_text, draw_image

PLATFORM = platform.lower()

if PLATFORM.startswith('win'):
    try:
        import win32gui
        import win32process
        import keyboard
    except ImportError:
        print("[red]请先安装 Windows 运行库: pip install pywin32 keyboard[/red]")
        raise


class ManosabaTextBox:
    """主逻辑类"""

    def __init__(self):
        # 常量定义
        self.BOX_RECT = ((728, 355), (2339, 800))
        self.KEY_DELAY = 0.1
        self.AUTO_PASTE_IMAGE = True
        self.AUTO_SEND_IMAGE = True

        self.hotkey_listener = None

        # 初始化路径
        self.BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.ASSETS_PATH = os.path.join(self.BASE_PATH, "assets")
        self.CACHE_PATH = os.path.join(self.ASSETS_PATH, "cache")

        # 初始化模块
        self.config_loader = ConfigLoader(self.BASE_PATH)
        self.img_generator = ImageGenerator(self.BASE_PATH, self.CACHE_PATH)
        self.clipboard_handler = ClipboardHandler(self.KEY_DELAY)

        # 加载配置
        self.mahoshojo = {}
        self.text_configs_dict = {}
        self.character_list = []
        self.keymap = {}
        self.process_whitelist = []
        self.load_configs()

        # 状态变量
        self.active = True
        self.emote = None
        self.value_1 = -1
        self.current_character_index = 3

    def load_configs(self):
        """从yaml加载配置文件"""
        self.mahoshojo, self.character_list, self.text_configs_dict = self.config_loader.load_chara_meta()
        self.keymap = self.config_loader.load_keymap()
        self.process_whitelist = self.config_loader.load_process_whitelist()

    def get_character(self, index: str | None = None, full_name: bool = False) -> str:
        """
        获取角色名称
        Args:
            index: 角色索引名（不是序号，如果为None则返回当前角色）
            full_name: 是否返回全名
        Returns:
            角色名称 (str)
        """
        if index is not None:
            return self.mahoshojo[index]['full_name'] if full_name else index
        else:
            chara = self.character_list[self.current_character_index - 1]
            return self.mahoshojo[chara]['full_name'] if full_name else chara

    def switch_character(self, index: int) -> str:
        """切换到指定索引的角色"""
        if 0 < index <= len(self.character_list):
            self.current_character_index = index
            return f"[green]已切换角色: {self.get_character()}[/green]"
        return "[red]切换角色失败[/red]"

    def switch_emote(self, emote_index: int) -> str:
        """切换到指定表情索引"""
        character_name = self.get_character()
        emotion_cnt = self.mahoshojo[character_name]["emotion_count"]
        if 1 <= emote_index <= emotion_cnt:
            self.emote = emote_index
            return f"[green]已切换表情: {emote_index}[/green]"
        return "[red]切换表情失败[/red]"

    def get_current_font(self) -> str:
        """返回当前角色的字体文件绝对路径"""
        return os.path.join(self.BASE_PATH, 'assets', 'fonts',
                            self.mahoshojo[self.get_character()]["font"])

    def get_current_emotion_count(self) -> int:
        """获取当前角色的表情数量"""
        return self.mahoshojo[self.get_character()]["emotion_count"]

    def get_current_emotion_names(self) -> list[str]:
        """获取当前角色的表情文件名列表"""
        character_name = self.get_character()
        emotion_cnt = self.get_current_emotion_count()
        # 确保角色已加载
        self.img_generator._ensure_character_loaded(character_name, emotion_cnt)
        return self.img_generator.get_emotion_names(character_name)

    def delete_cache(self) -> None:
        """清除缓存（包括内存和磁盘）"""
        self.img_generator.clear_memory_cache()
        self.img_generator.delete_cache()

    def generate_and_save_images(self, character_name: str, progress_callback=None) -> None:
        """生成并保存指定角色的所有表情图片"""
        emotion_cnt = self.mahoshojo[character_name]["emotion_count"]
        self.img_generator.generate_and_save_images(character_name, emotion_cnt, progress_callback)

    def get_random_value(self) -> str:
        """随机获取表情图片名称（已弃用，保留兼容性）"""
        character_name = self.get_character()
        emotion_cnt = self.get_current_emotion_count()

        img_name, self.value_1 = self.img_generator.get_random_image_name(
            character_name, emotion_cnt, self.emote, self.value_1
        )
        self.emote = None
        return img_name

    def get_random_image(self):
        """随机获取表情图片（内存模式）"""
        character_name = self.get_character()
        emotion_cnt = self.get_current_emotion_count()

        img, self.value_1 = self.img_generator.get_random_image(
            character_name, emotion_cnt, self.emote, self.value_1
        )
        self.emote = None
        return img

    def _active_process_allowed(self) -> bool:
        """校验当前前台进程是否在白名单"""
        if not self.process_whitelist:
            return True

        wl = {name.lower() for name in self.process_whitelist}

        if PLATFORM.startswith('win'):
            try:
                hwnd = win32gui.GetForegroundWindow()
                if not hwnd:
                    return False
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                name = psutil.Process(pid).name().lower()
                return name in wl
            except (psutil.Error, OSError):
                return False

        elif PLATFORM == 'darwin':
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
            # todo: Linux 支持
            return True

    def start(self) -> str:
        """生成并发送图片，返回状态消息"""
        if not self.active:
            return "程序处于暂停状态"
        if not self._active_process_allowed():
            return "前台应用不在白名单内"
        character_name = self.get_character()

        # 使用内存模式获取图片（不再依赖磁盘缓存）
        baseimage = self.get_random_image()

        text_box_topleft = (self.BOX_RECT[0][0], self.BOX_RECT[0][1])
        image_box_bottomright = (self.BOX_RECT[1][0], self.BOX_RECT[1][1])
        text = self.clipboard_handler.cut_all_and_get_text()
        image = self.clipboard_handler.try_get_image()

        if text == "" and image is None:
            return "错误: 没有文本或图像"

        png_bytes = None

        if image is not None:
            try:
                png_bytes = draw_image(
                    img_src=baseimage,
                    top_left=text_box_topleft,
                    bottom_right=image_box_bottomright,
                    content_img=image,
                    align="center",
                    valign="middle",
                    padding=12,
                    allow_upscale=True,
                    keep_alpha=True,
                    img_overlay=None,
                    role_name=character_name,
                    text_cfgs=self.text_configs_dict,
                )
            except Exception as e:
                return f"生成图像失败: {e}"

        elif text is not None and text != "":
            try:
                png_bytes = draw_text(
                    img_src=baseimage,
                    top_left=text_box_topleft,
                    bottom_right=image_box_bottomright,
                    text=text,
                    color=(255, 255, 255),
                    font_path=self.get_current_font(),
                    max_font_h=145,
                    align="left",
                    valign='top',
                    img_overlay=None,
                    role_name=character_name,
                    text_cfgs=self.text_configs_dict,
                )

            except Exception as e:
                return f"生成图像失败: {e}"

        if png_bytes is None:
            return "生成图像失败！"

        self.clipboard_handler.copy_png_bytes_to_clipboard(png_bytes)
        self.clipboard_handler.paste_and_send(self.AUTO_PASTE_IMAGE, self.AUTO_SEND_IMAGE, self.keymap['send_image'])

        return (f"生成成功！角色: {character_name}, 表情: {1 + (self.value_1 // BG_CNT)}，"
                f"内容：{'[图片]' if image else text[:20]}{'...' if len(text) > 20 else ''}")

    def toggle_active(self):
        """切换程序激活状态"""
        self.active = not self.active
        status = "激活" if self.active else "暂停"
        print(f"[green]程序已{status}[/green]")

    def setup_global_hotkeys(self):
        """设置全局热键监听器"""
        keymap = self.keymap
        if PLATFORM == "darwin":
            hotkeys = {
                keymap['start_generate']: lambda: print(self.start()),
                keymap['pause']: self.toggle_active,
                keymap['delete_cache']: self.delete_cache,
                keymap['quit']: lambda: self.hotkey_listener.stop()
            }
            hotkeys.update({
                mapping['key']: (lambda param=mapping['param']: print(self.switch_character(param)))
                for mapping in keymap['switch_character']
            })
            hotkeys.update({
                mapping['key']: (lambda param=mapping['param']: print(self.switch_emote(param)))
                for mapping in keymap['get_expression']
            })
            hotkeys[keymap['show_current_character']] = lambda: print(self.get_character())
            self.hotkey_listener = GlobalHotKeys(hotkeys)
            self.hotkey_listener.start()
            print("[green]全局热键监听器已启动[/green]")
            self.hotkey_listener.join()
        elif PLATFORM.startswith('win'):
            for mapping in keymap['switch_character']:
                keyboard.add_hotkey(mapping['key'], lambda param=mapping['param']: print(self.switch_character(param)))
            for mapping in keymap['get_expression']:
                keyboard.add_hotkey(mapping['key'], lambda param=mapping['param']: print(self.switch_emote(param)))
            keyboard.add_hotkey(keymap['show_current_character'], lambda: print(self.get_character()))
            keyboard.add_hotkey(keymap['start_generate'], lambda: print(self.start()))
            keyboard.add_hotkey(keymap['pause'], self.toggle_active)
            keyboard.add_hotkey(keymap['delete_cache'], self.delete_cache)
            keyboard.add_hotkey(keymap['quit'], lambda: os._exit(0))
            print("[green]全局热键监听器已启动[/green]")
            keyboard.wait('esc')

    def run(self):
        """运行主程序"""
        print("魔裁文本框生成器 v1.2.0")
        print(f"\n定义的角色列表: ")
        for idx, chara in enumerate(self.mahoshojo):
            print(f"  {idx + 1}: {self.mahoshojo[chara]['full_name']} ({chara})")
        print("\n定义的快捷键列表")
        for mapping in self.keymap['switch_character']:
            print(f"  [cyan]{mapping['key']}[/cyan]: 切换角色 {mapping['param']}")
        for mapping in self.keymap['get_expression']:
            print(f"  [cyan]{mapping['key']}[/cyan]: 切换表情 {mapping['param']}")
        print(f"  {self.keymap['show_current_character']}: 显示当前角色")
        print(f"""
  {self.keymap['start_generate']}: 生成图片
  {self.keymap['quit']}: 退出程序
  {self.keymap['pause']}: 暂停/激活程序
  {self.keymap['delete_cache']}: 清除缓存图片
感谢各位的支持""")
        self.setup_global_hotkeys()


if __name__ == "__main__":
    app = ManosabaTextBox()
    app.run()
