import random
import time
import psutil
from pynput.keyboard import Key, Controller, GlobalHotKeys
import pyperclip
import io
from PIL import Image
import pyclip
from sys import platform
import os
import yaml
import tempfile
import subprocess

from rich import print

from text_fit_draw import draw_text_auto
from image_fit_paste import paste_image_auto

PLATFORM = platform.lower()

if PLATFORM.startswith('win'):
    try:
        import win32clipboard
        import keyboard
        import win32gui
        import win32process
    except ImportError:
        print("[red]请先安装 Windows 运行库: pip install pywin32 keyboard[/red]")
        raise


class ManosabaTextBox:
    """主逻辑类"""

    def __init__(self):
        # 常量定义
        self.BOX_RECT = ((728, 355), (2339, 800))  # 文本框区域坐标
        self.KEY_DELAY = 0.1  # 按键延迟
        self.AUTO_PASTE_IMAGE = True  # 自动粘贴图片
        self.AUTO_SEND_IMAGE = True  # 自动发送图片

        self.kbd_controller = Controller()  # 键盘控制器
        self.hotkey_listener = None # 全局热键监听器

        # 初始化路径
        self.BASE_PATH = ""  # 基础路径
        self.CONFIG_PATH = ""  # 配置路径
        self.ASSETS_PATH = ""  # 资源路径
        self.CACHE_PATH = ""  # 缓存路径
        self.setup_paths()

        # 加载配置
        self.mahoshojo = {}  # 角色元数据
        self.text_configs_dict = {}  # 文本配置字典
        self.character_list = []  # 角色列表
        self.keymap = {}  # 快捷键映射
        self.process_whitelist = []  # 进程白名单
        self.load_configs()

        # 状态变量
        self.active = True # 程序激活状态
        self.emote = None  # 表情索引
        self.value_1 = -1  # 我也不知道这是啥我也不敢动
        self.current_character_index = 3  # 当前角色索引，默认第三个角色（sherri）

    def setup_paths(self):
        """设置文件路径"""
        self.BASE_PATH = os.path.dirname(os.path.abspath(__file__))
        self.CONFIG_PATH = os.path.join(self.BASE_PATH, "config")
        self.ASSETS_PATH = os.path.join(self.BASE_PATH, "assets")
        self.CACHE_PATH = os.path.join(self.ASSETS_PATH, "cache")
        os.makedirs(self.CACHE_PATH, exist_ok=True)

    def load_configs(self):
        """从yaml加载配置文件"""
        with open(os.path.join(self.CONFIG_PATH, "chara_meta.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
            self.mahoshojo = config["mahoshojo"]
            self.character_list = list(self.mahoshojo.keys())

        with open(os.path.join(self.CONFIG_PATH, "text_configs.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
            self.text_configs_dict = config["text_configs"]

        with open(os.path.join(self.CONFIG_PATH, "keymap.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
            self.keymap = config.get(PLATFORM, {})

        with open(os.path.join(self.CONFIG_PATH, "process_whitelist.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
            self.process_whitelist = config.get(PLATFORM, [])

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

    def switch_character(self, index: int) -> bool:
        """切换到指定索引的角色"""
        if 0 < index <= len(self.character_list):
            self.current_character_index = index
            return True
        return False

    def get_current_font(self) -> str:
        """返回当前角色的字体文件绝对路径"""
        return os.path.join(self.BASE_PATH, 'assets', 'fonts',
                            self.mahoshojo[self.get_character()]["font"])

    def get_current_emotion_count(self) -> int:
        """获取当前角色的表情数量"""
        return self.mahoshojo[self.get_character()]["emotion_count"]

    def delete(self, folder_path: str) -> None:
        """删除指定文件夹中的所有jpg文件"""
        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.jpg'):
                os.remove(os.path.join(folder_path, filename))

    def generate_and_save_images(self, character_name: str, progress_callback=None) -> None:
        """生成并保存指定角色的所有表情图片"""
        emotion_cnt = self.mahoshojo[character_name]["emotion_count"]

        # 检查是否已经生成过
        for filename in os.listdir(self.CACHE_PATH):
            if filename.startswith(character_name):
                return

        total_images = 16 * emotion_cnt

        for j in range(emotion_cnt):
            for i in range(16):
                background_path = os.path.join(
                    self.BASE_PATH, 'assets', "background", f"c{i + 1}.png"
                )
                overlay_path = os.path.join(
                    self.BASE_PATH, 'assets', 'chara', character_name,
                    f"{character_name} ({j + 1}).png"
                )

                background = Image.open(background_path).convert("RGBA")
                overlay = Image.open(overlay_path).convert("RGBA")

                img_num = j * 16 + i + 1
                result = background.copy()
                result.paste(overlay, (0, 134), overlay)

                save_path = os.path.join(
                    self.CACHE_PATH, f"{character_name} ({img_num}).jpg"
                )
                result.convert("RGB").save(save_path)

                if progress_callback:
                    progress_callback(j * 16 + i + 1, total_images)

    def get_random_value(self) -> str:
        """随机获取表情图片名称"""
        character_name = self.get_character()
        emotion_cnt = self.get_current_emotion_count()
        total_images = 16 * emotion_cnt

        if self.emote:
            i = random.randint((self.emote - 1) * 16 + 1, self.emote * 16)
            self.value_1 = i
            self.emote = None
            return f"{character_name} ({i})"

        max_attempts = 100
        attempts = 0
        i = random.randint(1, total_images)

        while attempts < max_attempts:
            i = random.randint(1, total_images)
            current_emotion = (i - 1) // 16

            if self.value_1 == -1:
                self.value_1 = i
                return f"{character_name} ({i})"

            if current_emotion != (self.value_1 - 1) // 16:
                self.value_1 = i
                return f"{character_name} ({i})"

            attempts += 1

        self.value_1 = i
        return f"{character_name} ({i})"

    def copy_png_bytes_to_clipboard(self, png_bytes: bytes) -> None:
        """将PNG字节数据复制到剪贴板"""
        try:
            if PLATFORM == 'darwin':
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp.write(png_bytes)
                    tmp_path = tmp.name

                cmd = f"""osascript -e 'set the clipboard to (read (POSIX file "{tmp_path}") as «class PNGf»)'"""
                result = subprocess.run(cmd, shell=True, capture_output=True)

                os.unlink(tmp_path)

                if result.returncode != 0:
                    print(f"复制图片到剪贴板失败: {result.stderr.decode()}")
            elif PLATFORM.startswith('win'):
                # 打开 PNG 字节为 Image
                image = Image.open(io.BytesIO(png_bytes))
                # 转换成 BMP 字节流（去掉 BMP 文件头的前 14 个字节）
                with io.BytesIO() as output:
                    image.convert("RGB").save(output, "BMP")
                    bmp_data = output.getvalue()[14:]
                # 打开剪贴板并写入 DIB 格式
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
                win32clipboard.CloseClipboard()
            else:
                # todo: Linux 支持
                pass
        except Exception as e:
            print(f"复制图片到剪贴板失败: {e}")

    def cut_all_and_get_text(self) -> str:
        """模拟全选和剪切操作，返回剪切得到的文本内容"""
        pyperclip.copy("")
        if PLATFORM == 'darwin':
            self.kbd_controller.press(Key.cmd)
            self.kbd_controller.press('a')
            self.kbd_controller.release('a')
            self.kbd_controller.press('x')
            self.kbd_controller.release('x')
            self.kbd_controller.release(Key.cmd)

        elif PLATFORM.startswith('win'):
            keyboard.send("CTRL+A")
            keyboard.send("CTRL+X")

        time.sleep(self.KEY_DELAY)
        new_clip = pyperclip.paste()
        return new_clip.strip()

    def try_get_image(self) -> Image.Image | None:
        """尝试从剪贴板获取图像"""
        if PLATFORM == 'darwin':
            try:
                data = pyclip.paste()

                if isinstance(data, bytes) and len(data) > 0:
                    try:
                        text = data.decode('utf-8')
                        if len(text) < 10000:
                            return None
                    except (UnicodeDecodeError, AttributeError):
                        pass

                    try:
                        image = Image.open(io.BytesIO(data))
                        image.load()
                        return image
                    except Exception:
                        return None

            except Exception as e:
                print(f"无法从剪贴板获取图像: {e}")
        elif PLATFORM.startswith('win'):
            try:
                win32clipboard.OpenClipboard()
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                    data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
                    if data:
                        # 将 DIB 数据转换为字节流，供 Pillow 打开
                        bmp_data = data
                        # DIB 格式缺少 BMP 文件头，需要手动加上
                        # BMP 文件头是 14 字节，包含 "BM" 标识和文件大小信息
                        header = b'BM' + (len(bmp_data) + 14).to_bytes(4,
                                                                       'little') + b'\x00\x00\x00\x00\x36\x00\x00\x00'
                        image = Image.open(io.BytesIO(header + bmp_data))
                        return image
            except Exception as e:
                print("无法从剪贴板获取图像：", e)
            finally:
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass
            return None
        else:
            # todo: Linux 支持
            return None

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
                result = subprocess.run(
                    ["osascript", "-e",
                     'tell application "System Events" to get name of first process whose frontmost is true'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                name = result.stdout.strip().lower()
                print (f"Active process: {name}")
                return name in wl
            except subprocess.SubprocessError:
                return False

        else:
            # todo: Linux 支持
            return True

    def start(self) -> str:
        """生成并发送图片，返回状态消息"""
        if not self._active_process_allowed():
            return "前台应用不在白名单内"
        character_name = self.get_character()
        address = os.path.join(self.CACHE_PATH, self.get_random_value() + ".jpg")
        baseimage_file = address

        text_box_topleft = (self.BOX_RECT[0][0], self.BOX_RECT[0][1])
        image_box_bottomright = (self.BOX_RECT[1][0], self.BOX_RECT[1][1])
        text = self.cut_all_and_get_text()
        image = self.try_get_image()

        if text == "" and image is None:
            return "错误: 没有文本或图像"

        png_bytes = None

        if image is not None:
            try:
                png_bytes = paste_image_auto(
                    image_source=baseimage_file,
                    image_overlay=None,
                    top_left=text_box_topleft,
                    bottom_right=image_box_bottomright,
                    content_image=image,
                    align="center",
                    valign="middle",
                    padding=12,
                    allow_upscale=True,
                    keep_alpha=True,
                    role_name=character_name,
                    text_configs_dict=self.text_configs_dict,
                )
            except Exception as e:
                return f"生成图像失败: {e}"

        elif text is not None and text != "":
            try:
                png_bytes = draw_text_auto(
                    image_source=baseimage_file,
                    image_overlay=None,
                    top_left=text_box_topleft,
                    bottom_right=image_box_bottomright,
                    text=text,
                    align="left",
                    valign='top',
                    color=(255, 255, 255),
                    max_font_height=145,
                    font_path=self.get_current_font(),
                    role_name=character_name,
                    text_configs_dict=self.text_configs_dict,
                )

            except Exception as e:
                return f"生成图像失败: {e}"

        if png_bytes is None:
            return "生成图像失败！"

        self.copy_png_bytes_to_clipboard(png_bytes)

        if self.AUTO_PASTE_IMAGE:
            self.kbd_controller.press(Key.ctrl if PLATFORM != 'darwin' else Key.cmd)
            self.kbd_controller.press('v')
            self.kbd_controller.release('v')
            self.kbd_controller.release(Key.ctrl if PLATFORM != 'darwin' else Key.cmd)

            time.sleep(0.3)

            if self.AUTO_SEND_IMAGE:
                self.kbd_controller.press(Key.enter)
                self.kbd_controller.release(Key.enter)

        return f"成功生成图片！角色: {character_name}, 表情: {1 + (self.value_1 // 16)}"

    def toggle_active(self):
        """切换程序激活状态"""
        self.active = not self.active
        status = "激活" if self.active else "暂停"
        print(f"[green]程序已{status}[/green]")

    def setup_global_hotkeys(self):
        """设置全局热键监听器"""
        keymap = self.keymap
        if PLATFORM == "darwin":
            self.hotkey_listener = GlobalHotKeys({
                keymap['start_generate']: lambda: print(self.start()),
                keymap['pause']: self.toggle_active,
                keymap['delete_cache']: self.delete,
                keymap['quit']: lambda: self.hotkey_listener.stop()
            })
            self.hotkey_listener.start()
            self.hotkey_listener.join() # 保持程序运行，直到热键监听器停止
        elif PLATFORM.startswith('win'):
            keyboard.add_hotkey(keymap['start_generate'], lambda: print(self.start()))
            keyboard.add_hotkey(keymap['pause'], self.toggle_active)
            keyboard.add_hotkey(keymap['delete_cache'], self.delete)
            keyboard.add_hotkey(keymap['quit'], lambda: os._exit(0))
            keyboard.wait('esc')  # 保持程序运行，直到按下 'esc' 键退出

    def run(self):
        """运行主程序"""
        self.setup_global_hotkeys()

if __name__ == "__main__":
    app = ManosabaTextBox()
    app.run()