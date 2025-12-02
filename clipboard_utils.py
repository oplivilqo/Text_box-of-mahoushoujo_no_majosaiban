"""剪贴板工具模块"""

import io
import os
import tempfile
import subprocess
from sys import platform

from PIL import Image
import pyperclip
import pyclip


PLATFORM = platform.lower()

if PLATFORM.startswith("win"):
    try:
        import win32clipboard
    except ImportError:
        print("[red]请先安装 Windows 运行库: pip install pywin32[/red]")
        raise


class ClipboardManager:
    """剪贴板管理器"""

    def __init__(self):
        self.platform = PLATFORM

    def copy_image_to_clipboard(self, bmp_bytes: bytes) -> bool:
        """将BMP字节数据复制到剪贴板"""
        try:
            if self.platform == "darwin":
                return self._copy_image_macos(bmp_bytes)
            if self.platform.startswith("win"):
                return self._copy_image_windows(bmp_bytes)
            return self._copy_image_linux(bmp_bytes)
        except Exception as e:
            print(f"复制图片到剪贴板失败: {e}")
            return False

    def _copy_image_macos(self, png_bytes: bytes) -> bool:
        """macOS 复制图片到剪贴板"""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(png_bytes)
            tmp_path = tmp.name

        cmd = f"""osascript -e 'set the clipboard to (read (POSIX file "{tmp_path}") as «class PNGf»)'"""
        result = subprocess.run(cmd, shell=True, capture_output=True, check=False)

        try:
            os.unlink(tmp_path)
        except OSError:
            pass

        return result.returncode == 0

    def _copy_image_windows(self, bmp_bytes: bytes) -> bool:
        """Windows 复制图片到剪贴板"""
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_bytes)
            win32clipboard.CloseClipboard()
            return True
        except Exception as e:
            print(f"Windows 复制图片失败: {e}")
            return False
        finally:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass

    def _copy_image_linux(self, png_bytes: bytes) -> bool:
        """Linux 复制图片到剪贴板"""
        print("Linux 剪贴板支持尚未实现")
        return False

    def get_text_from_clipboard(self) -> str:
        """从剪贴板获取文本"""
        return pyperclip.paste()

    def copy_text_to_clipboard(self, text: str):
        """复制文本到剪贴板"""
        pyperclip.copy(text)

    def get_image_from_clipboard(self) -> Image.Image | None:
        """从剪贴板获取图片"""
        if self.platform == "darwin":
            return self._get_image_macos()
        if self.platform.startswith("win"):
            return self._get_image_windows()
        return self._get_image_linux()

    def _get_image_macos(self) -> Image.Image | None:
        """macOS 从剪贴板获取图片"""
        try:
            data = pyclip.paste()

            if isinstance(data, bytes) and len(data) > 0:
                try:
                    text = data.decode("utf-8")
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
            return None
        except Exception as e:
            print(f"无法从剪贴板获取图像: {e}")
            return None

    def _get_image_windows(self) -> Image.Image | None:
        """Windows 从剪贴板获取图片"""
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
                if data:
                    bmp_data = data
                    header = (
                        b"BM"
                        + (len(bmp_data) + 14).to_bytes(4, "little")
                        + b"\x00\x00\x00\x00\x36\x00\x00\x00"
                    )
                    image = Image.open(io.BytesIO(header + bmp_data))
                    return image
        except Exception as e:
            print("无法从剪贴板获取图像：", e)
        finally:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass
        return None

    def _get_image_linux(self) -> Image.Image | None:
        """Linux 从剪贴板获取图片"""
        return None

    def has_image_in_clipboard(self) -> bool:
        """检查剪贴板中是否有图片"""
        try:
            if platform.startswith("win"):
                win32clipboard.OpenClipboard()
                try:
                    # 尝试获取剪贴板中的图片数据
                    if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                        return True
                    return False
                finally:
                    win32clipboard.CloseClipboard()
            if platform == "darwin":
                # macOS 的实现
                from AppKit import NSPasteboard, NSPasteboardTypePNG

                pasteboard = NSPasteboard.generalPasteboard()
                return (
                    pasteboard.availableTypeFromArray_([NSPasteboardTypePNG])
                    is not None
                )
            # Linux 的实现
            return False  # 需要根据具体实现补充
        except Exception:
            return False