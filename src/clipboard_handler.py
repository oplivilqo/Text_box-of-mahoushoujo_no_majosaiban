"""剪贴板操作模块"""
import io
import os
import tempfile
import subprocess
import time
from sys import platform
from PIL import Image
import pyperclip
import pyclip
from pynput.keyboard import Key, Controller, KeyCode

PLATFORM = platform.lower()

if PLATFORM.startswith('win'):
    try:
        import win32clipboard
        import keyboard
    except ImportError:
        print("[red]请先安装 Windows 运行库: pip install pywin32 keyboard[/red]")
        raise


class ClipboardHandler:
    """剪贴板处理器"""

    def __init__(self, key_delay: float = 0.1):
        self.key_delay = key_delay
        self.kbd_controller = Controller()

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
                image = Image.open(io.BytesIO(png_bytes))
                with io.BytesIO() as output:
                    image.convert("RGB").save(output, "BMP")
                    bmp_data = output.getvalue()[14:]
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

        time.sleep(self.key_delay)
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
                        bmp_data = data
                        header = b'BM' + (len(bmp_data) + 14).to_bytes(4, 'little') + b'\x00\x00\x00\x00\x36\x00\x00\x00'
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

    def paste_and_send(self, auto_paste: bool, auto_send: bool, send_key: str = "enter") -> None:
        """
        粘贴并发送图片
        Args:
            auto_paste: 是否自动粘贴
            auto_send: 是否自动发送
            send_key: 发送时使用的按键，支持pynput格式（如"enter", "<ctrl>+enter"）
        """
        if auto_paste:
            self.kbd_controller.press(Key.ctrl if PLATFORM != 'darwin' else Key.cmd)
            self.kbd_controller.press('v')
            self.kbd_controller.release('v')
            self.kbd_controller.release(Key.ctrl if PLATFORM != 'darwin' else Key.cmd)

            time.sleep(0.3)

            if auto_send:
                self._press_key_combination(send_key)

    def _press_key_combination(self, key_str: str) -> None:
        """
        解析并按下按键组合
        Args:
            key_str: 按键字符串，支持pynput格式（如"enter", "<ctrl>+enter", "<cmd>+<shift>+a"）
        """
        parts = key_str.split('+')
        modifiers = []
        main_key = None

        for part in parts:
            part = part.strip()
            if part.startswith('<') and part.endswith('>'):
                key_name = part[1:-1].lower()
                if key_name == 'ctrl':
                    modifiers.append(Key.ctrl)
                elif key_name == 'cmd':
                    modifiers.append(Key.cmd)
                elif key_name == 'alt':
                    modifiers.append(Key.alt)
                elif key_name == 'shift':
                    modifiers.append(Key.shift)
                elif key_name == 'enter':
                    main_key = Key.enter
                elif key_name == 'esc':
                    main_key = Key.esc
                elif key_name == 'tab':
                    main_key = Key.tab
                elif key_name == 'space':
                    main_key = Key.space
                else:
                    main_key = part
            else:
                if part.lower() == 'enter':
                    main_key = Key.enter
                elif part.lower() == 'esc':
                    main_key = Key.esc
                elif part.lower() == 'tab':
                    main_key = Key.tab
                elif part.lower() == 'space':
                    main_key = Key.space
                else:
                    main_key = part

        for mod in modifiers:
            self.kbd_controller.press(mod)

        if main_key:
            self.kbd_controller.press(main_key)
            self.kbd_controller.release(main_key)

        for mod in reversed(modifiers):
            self.kbd_controller.release(mod)

