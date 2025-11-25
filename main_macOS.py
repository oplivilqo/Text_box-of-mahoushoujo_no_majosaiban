"""适用于 macOS 的版本"""

import random
import time
from pynput import keyboard
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
from text_fit_draw import draw_text_auto
from image_fit_paste import paste_image_auto

print("""角色说明:
1为樱羽艾玛，2为二阶堂希罗，3为橘雪莉，4为远野汉娜
5为夏目安安，6为月代雪，7为冰上梅露露，8为城崎诺亚，9为莲见蕾雅，10为佐伯米莉亚
11为黑部奈叶香，12为宝生玛格，13为紫藤亚里沙，14为泽渡可可

快捷键说明:
Ctrl+1 到 Ctrl+9: 切换角色1-9
Ctrl+q: 切换角色10
Ctrl+w: 切换角色11
Ctrl+e: 切换角色12
Ctrl+r: 切换角色13
Ctrl+t: 切换角色14
Ctrl+0: 显示当前角色
Alt+1-9: 切换表情1-9(部分角色表情较少 望大家谅解)
Enter: 生成图片
Esc: 退出程序
Ctrl+Tab: 清除图片

程序说明：
这个版本的程序占用体积较小，但是需要预加载，初次更换角色后需要等待数秒才能正常使用，望周知（
按Tab可清除生成图片，降低占用空间，但清除图片后需重启才能正常使用
感谢各位的支持
""")

class ManosabaTextBox:
    def __init__(self):
        # 常量定义
        self.BOX_RECT = ((728, 355), (2339, 800))
        self.KEY_DELAY = 0.1                    # 组合键延迟
        self.AUTO_PASTE_IMAGE = True            # 自动粘贴
        self.AUTO_SEND_IMAGE = True             # 自动发送

        self.PLATFORM = platform.lower()
        self.kbd_controller = Controller()

        self.BASE_PATH = ""     # 基础路径
        self.CONFIG_PATH = ""   # 配置路径
        self.ASSETS_PATH = ""   # 资源路径
        self.CACHE_PATH = ""    # 缓存路径
        self.setup_paths()

        self.mahoshojo = {}             # 角色元数据
        self.text_configs_dict = {}     # 文字配置数据
        self.character_list = []        # 角色列表
        self.hotkey_bindings = []       # 热键配置
        self.load_configs()


        self.emote = None
        self.value_1 = -1
        self.i = -1
        self.current_character_index = 3
        
    def setup_paths(self):
        """设置文件路径"""
        self.BASE_PATH = os.path.dirname(os.path.abspath(__file__))
        self.CONFIG_PATH = os.path.join(self.BASE_PATH, "config")
        self.ASSETS_PATH = os.path.join(self.BASE_PATH, "assets")
        self.CACHE_PATH = os.path.join(self.ASSETS_PATH, "cache")
        os.makedirs(self.CACHE_PATH, exist_ok=True)

    def load_configs(self):
        """加载配置文件"""
        # 读取角色元数据
        with open(os.path.join(self.CONFIG_PATH, "chara_meta.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
            self.mahoshojo = config["mahoshojo"]

        # 读取文字配置
        with open(os.path.join(self.CONFIG_PATH, "text_configs.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
            self.text_configs_dict = config["text_configs"]
        self.character_list = list(self.mahoshojo.keys())

        # 读取热键配置
        with open(os.path.join(self.CONFIG_PATH, "hotkeys_macos.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
        ACTION_MAP = {
            "switch_character": self.switch_character,
            "show_current_character": self.show_current_character,
            "get_expression": self.get_expression,
            "start_generate": self.start,
            "delete_images": lambda: self.delete(self.CACHE_PATH)
        }

        bindings = {}
        for category, hotkeys in config["hotkeys"].items():
            if not isinstance(hotkeys, list):
                continue

            for hotkey_config in hotkeys:
                key = hotkey_config["key"]
                action_name = hotkey_config["action"]
                param = hotkey_config.get("param")

                if param is not None:
                    bindings[key] = lambda p=param, a=action_name: ACTION_MAP[a](p)
                else:
                    bindings[key] = lambda a=action_name: ACTION_MAP[a]()

        self.hotkey_bindings = bindings

    def get_current_character(self) -> str:
        """获取当前角色名称"""
        return self.character_list[self.current_character_index - 1]

    def switch_character(self, new_index: int) -> bool:
        """切换到指定索引的角色"""
        if 0 <= new_index < len(self.character_list):
            self.current_character_index = new_index
            character_name = self.get_current_character()
            print(f"已切换到角色: {character_name}")
            self.generate_and_save_images(character_name)
            return True
        return False

    def get_current_font(self) -> str:
        """返回当前角色的字体文件绝对路径"""
        return os.path.join(self.BASE_PATH, 'assets', 'fonts',
                            self.mahoshojo[self.get_current_character()]["font"])

    def get_current_emotion_count(self) -> int:
        """获取当前角色的表情数量"""
        return self.mahoshojo[self.get_current_character()]["emotion_count"]

    def delete(self, folder_path: str) -> None:
        """删除指定文件夹中的所有jpg文件"""
        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.jpg'):
                os.remove(os.path.join(folder_path, filename))

    def generate_and_save_images(self, character_name: str) -> None:
        """生成并保存指定角色的所有表情图片"""
        emotion_cnt = self.mahoshojo[character_name]["emotion_count"]

        for filename in os.listdir(self.CACHE_PATH):
            if filename.startswith(character_name):
                return

        print("正在加载")
        for i in range(16):
            for j in range(emotion_cnt):
                background_path = os.path.join(self.BASE_PATH, 'assets', "background", f"c{i + 1}.png")
                overlay_path = os.path.join(self.BASE_PATH, 'assets', 'chara', character_name,
                                            f"{character_name} ({j + 1}).png")

                background = Image.open(background_path).convert("RGBA")
                overlay = Image.open(overlay_path).convert("RGBA")

                img_num = j * 16 + i + 1
                result = background.copy()
                result.paste(overlay, (0, 134), overlay)

                save_path = os.path.join(self.CACHE_PATH, f"{character_name} ({img_num}).jpg")
                result.convert("RGB").save(save_path)
        print("加载完成")

    def show_current_character(self) -> None:
        """显示当前角色信息"""
        character_name = self.get_current_character()
        print(f"当前角色: {character_name}")

    def get_expression(self, i: int) -> None:
        """设置表情索引"""
        character_name = self.get_current_character()
        if i <= self.mahoshojo[character_name]["emotion_count"]:
            print(f"已切换至第{i}个表情")
            self.emote = i

    def get_random_value(self) -> str:
        """随机获取表情图片名称"""
        character_name = self.get_current_character()
        emotion_cnt = self.get_current_emotion_count()
        total_images = 16 * emotion_cnt

        if self.emote:
            i = random.randint((self.emote - 1) * 16 + 1, self.emote * 16)
            self.value_1 = i
            self.emote = None
            return f"{character_name} ({i})"

        max_attempts = 100
        attempts = 0

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
        """将PNG字节数据复制到剪贴板（跨平台）"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp.write(png_bytes)
                tmp_path = tmp.name

            cmd = f"""osascript -e 'set the clipboard to (read (POSIX file "{tmp_path}") as «class PNGf»)'"""
            result = subprocess.run(cmd, shell=True, capture_output=True)

            os.unlink(tmp_path)

            if result.returncode != 0:
                print(f"复制图片到剪贴板失败: {result.stderr.decode()}")
        except Exception as e:
            print(f"复制图片到剪贴板失败: {e}")

    def cut_all_and_get_text(self) -> str:
        """模拟全选和剪切操作，返回剪切得到的文本内容"""
        pyperclip.copy("")

        self.kbd_controller.press(Key.ctrl if self.PLATFORM != 'darwin' else Key.cmd)
        self.kbd_controller.press('a')
        self.kbd_controller.release('a')
        self.kbd_controller.press('x')
        self.kbd_controller.release('x')
        self.kbd_controller.release(Key.ctrl if self.PLATFORM != 'darwin' else Key.cmd)
        time.sleep(self.KEY_DELAY)

        new_clip = pyperclip.paste()
        return new_clip

    def try_get_image(self) -> Image.Image | None:
        """尝试从剪贴板获取图像，如果没有图像则返回None"""
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
        return None

    def start(self) -> None:
        """生成并发送图片"""
        print("Start generate...")

        character_name = self.get_current_character()
        address = os.path.join(self.CACHE_PATH, self.get_random_value() + ".jpg")
        baseimage_file = address
        print(character_name, str(1 + (self.value_1 // 16)), "背景", str(self.value_1 % 16))

        text_box_topleft = (self.BOX_RECT[0][0], self.BOX_RECT[0][1])
        image_box_bottomright = (self.BOX_RECT[1][0], self.BOX_RECT[1][1])
        text = self.cut_all_and_get_text()
        image = self.try_get_image()

        if text == "" and image is None:
            print("no text or image")
            return

        png_bytes = None

        if image is not None:
            try:
                print("Get image")
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
                print("Generate image failed:", e)
                return

        elif text is not None and text != "":
            print(f"Get text: {text}")

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
                print("Generate image failed:", e)
                return

        if png_bytes is None:
            print("Generate image failed!")
            return

        self.copy_png_bytes_to_clipboard(png_bytes)

        if self.AUTO_PASTE_IMAGE:
            self.kbd_controller.press(Key.ctrl if self.PLATFORM != 'darwin' else Key.cmd)
            self.kbd_controller.press('v')
            self.kbd_controller.release('v')
            self.kbd_controller.release(Key.ctrl if self.PLATFORM != 'darwin' else Key.cmd)

            time.sleep(0.3)

            if self.AUTO_SEND_IMAGE:
                self.kbd_controller.press(Key.enter)
                self.kbd_controller.release(Key.enter)
                
    def run(self):
        print("提示: 在 macOS 上首次运行时，请在'系统设置 > 隐私与安全性 > 辅助功能'中授权此程序")

        self.show_current_character()
        self.generate_and_save_images(self.get_current_character())

        listener = GlobalHotKeys(self.hotkey_bindings)
        listener.start()

        print("快捷键监听已启动，按 Esc 退出程序")

        try:
            with keyboard.Listener(on_press=lambda key: key != Key.esc) as esc_listener:
                esc_listener.join()
        except KeyboardInterrupt:
            pass
        finally:
            listener.stop()
            print("\n程序已退出")
        

if __name__ == "__main__":
    app = ManosabaTextBox()
    app.run()
