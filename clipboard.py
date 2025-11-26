# -*- coding: utf-8 -*-
#剪贴板相关功能
import time
import keyboard
import pyperclip
import io
from PIL import Image
import win32clipboard
import logging

logger = logging.getLogger(__name__)

#将图片复制进剪贴板
def copy_png_bytes_to_clipboard(png_bytes: bytes):
    # 打开 PNG 字节为 Image
    image = Image.open(io.BytesIO(png_bytes))
    # 转换成 BMP 字节流（去掉 BMP 文件头的前 14 个字节）
    with io.BytesIO() as output:
        image.convert("RGB").save(output, "BMP")
        bmp_data = output.getvalue()[14:]
    # 打开剪贴板并写入 DIB 格式
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
    finally:
        try:
            win32clipboard.CloseClipboard()
        except:
            pass

#从剪贴板中获取图片
def try_get_image() -> Image.Image | None:
    """
    尝试从剪贴板获取图像，如果没有图像则返回 None。
    仅支持 Windows。
    """
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
            if data:
                # 将 DIB 数据转换为字节流，供 Pillow 打开
                bmp_data = data
                # DIB 格式缺少 BMP 文件头，需要手动加上
                # BMP 文件头是 14 字节，包含 "BM" 标识和文件大小信息
                header = b'BM' + (len(bmp_data) + 14).to_bytes(4, 'little') + b'\x00\x00\x00\x00\x36\x00\x00\x00'
                image = Image.open(io.BytesIO(header + bmp_data))
                return image
    except Exception as e:
        logger.exception("无法从剪贴板获取图像：%s", e)
    finally:
        try:
            win32clipboard.CloseClipboard()
        except:
            pass
    return None

#将文本剪切进剪贴板
def cut_all_and_get_text(select_hotkey: str = 'ctrl+a', cut_hotkey: str = 'ctrl+x', delay: float = 0.2) -> tuple:
    # 备份原剪贴板
    try:
        old_clip = pyperclip.paste()
    except Exception:
        old_clip = ''

    # 清空剪贴板，防止读到旧数据
    try:
        pyperclip.copy("")
    except Exception:
        pass

    # 发送 Select All 和 Cut
    keyboard.send(select_hotkey)
    keyboard.send(cut_hotkey)
    time.sleep(delay)

    # 获取剪切后的内容
    try:
        new_clip = pyperclip.paste()
    except Exception:
        new_clip = ''

    return new_clip, old_clip