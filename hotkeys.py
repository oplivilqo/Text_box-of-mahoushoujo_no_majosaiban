# -*- coding: utf-8 -*-
# 管理全局热键
import threading
import time
import keyboard
import logging
import win32gui
import win32process
import psutil
import os
import core
import clipboard
from config_loader import load_process_whitelist, load_keymap

logger = logging.getLogger(__name__)

_registered_hotkeys = []

class AppState:
    def __init__(self):
        roles = list(core.mahoshojo.keys())
        self.current_role = (roles[0] if roles else '')
        self.current_expression = -1
        self.last_expression = -1
        self.auto_paste = True
        self.auto_send = True
        # 白名单开关（会话内，可在设置里切换）
        self.enable_whitelist = True
        # 从配置文件加载白名单（不使用任何硬编码默认）
        try:
            self.window_whitelist = load_process_whitelist('win32')
        except Exception:
            logger.exception('加载窗口白名单失败')
            self.window_whitelist = []
        self.busy = False
        self.delay = 0.08
        # 从 key map.yml 读取快捷键（若缺失，keyboard 库会按空字符串忽略）
        km = {}
        try:
            km = load_keymap() or {}
        except Exception:
            km = {}
        self.start_hotkey = str(km.get('start_hotkey', 'enter'))
        self.paste_hotkey = str(km.get('paste_hotkey', 'ctrl+v'))
        self.send_hotkey = str(km.get('send_hotkey', 'enter'))
        self.select_all_hotkey = str(km.get('select_all_hotkey', 'ctrl+a'))
        self.cut_hotkey = str(km.get('cut_hotkey', 'ctrl+x'))


# 获取前台 exe 名称
def get_foreground_exe_name():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        exe_path = proc.exe()
        return os.path.basename(exe_path)
    except Exception as e:
        logger.debug("获取前台进程exe名失败: %s", e)
        return None


# 清除魔裁缓存文件夹
def _clear_magic_cut_folder():
    folder = core.get_magic_cut_folder()
    if not os.path.isdir(folder):
        return
    for entry in os.scandir(folder):
        if entry.is_file() and entry.name.lower().endswith('.jpg'):
            try:
                os.remove(entry.path)
            except Exception:
                logger.exception("删除失败： %s", entry.path)
    # 清除缓存文件夹后，也清除内存缓存
    core.clear_image_cache()


# 统一处理剪贴板操作
def _perform_keyboard_actions(png_bytes, state: AppState):
    if png_bytes is None:
        logger.warning("png_bytes里没东西")
        return
    try:
        # 把图片写入剪贴板
        clipboard.copy_png_bytes_to_clipboard(png_bytes)
    except Exception:
        logger.exception("拷贝进剪贴板失败")
        return

    if state.auto_paste:
        keyboard.call_later(lambda: keyboard.send(state.paste_hotkey), delay=0.08)
        if state.auto_send:
            keyboard.call_later(lambda: keyboard.send(state.send_hotkey), delay=0.25)


# 进行图片生成和发送的工作线程
def _worker_generate_and_send(text: str, content_image, state: AppState):
    try:
        # 更新为新的目录结构
        font_path = core.get_resource_path(os.path.join('assets', 'fonts', core.mahoshojo[state.current_role]["font"])) if state.current_role in core.mahoshojo else None
        # 使用 state.last_expression 作为 expression 参数，这样热键生成也会使用 GUI 设置的表情
        png_bytes, expr = core.generate_image(text=text, content_image=content_image, role_name=state.current_role, font_path=font_path, last_value=state.last_expression, expression=state.current_expression)
        # 更新状态
        if expr is not None:
            state.last_expression = expr
    except Exception:
        logger.exception("生成失败")
        png_bytes = None
    finally:
        # 在 keyboard 的线程上下文安全地执行粘贴/发送
        keyboard.call_later(lambda: _perform_keyboard_actions(png_bytes, state), delay=0)
        state.busy = False


# 启动触发处理
def _on_start_trigger(state: AppState):
    if state.busy:
        logger.debug("系统繁忙，忽略触发")
        return
    exe = get_foreground_exe_name()
    if state.enable_whitelist and state.window_whitelist and exe not in state.window_whitelist:
        logger.debug("前台exe %s 不在白名单内", exe)
        # 若热键为 Enter，保持原有 Enter 行为；否则忽略
        if state.start_hotkey.lower() == 'enter':
            keyboard.send('enter')
        return
    try:
        select_k = getattr(state, 'select_all_hotkey', 'ctrl+a')
        cut_k = getattr(state, 'cut_hotkey', 'ctrl+x')
        delay = getattr(state, 'delay', 0.08)
        text, _ = clipboard.cut_all_and_get_text(select_k, cut_k, delay)
        content_image = clipboard.try_get_image()
    except Exception:
        logger.exception("剪切失败")
        # 若热键为 Enter，保持原有 Enter 行为；否则忽略
        if state.start_hotkey.lower() == 'enter':
            keyboard.send('enter')
        return
    # 启动后台生成
    state.busy = True
    t = threading.Thread(target=_worker_generate_and_send, args=(text, content_image, state), daemon=True)
    t.start()


# 用于同步切换角色快捷键和下拉栏的函数
role_change_callback = None


# 切换角色
def switch_role_by_index(idx: int, state: AppState):
    roles = list(core.mahoshojo.keys())
    if 1 <= idx <= len(roles):
        state.current_role = roles[idx-1]
        logger.info("角色切换： %s", state.current_role)
        try:
            if role_change_callback:
                try:
                    role_change_callback(state.current_role)
                except Exception:
                    logger.exception('角色切换回传失败')
        except Exception:
            logger.exception('未定义回传函数')
        return True
    return False


# 切换自动粘贴
def toggle_auto_paste(state: AppState):
    state.auto_paste = not state.auto_paste
    if not state.auto_paste:
        state.auto_send = False
    logger.info("auto_paste=%s auto_send=%s", state.auto_paste, state.auto_send)


# 切换自动发送
def toggle_auto_send(state: AppState):
    if not state.auto_paste:
        logger.info("自动发送需要自动粘贴开启")
        return
    state.auto_send = not state.auto_send
    logger.info("auto_send=%s", state.auto_send)


# 注册热键
def register_hotkeys(state: AppState = None):
    if state is None:
        state = AppState()
    # 保留角色切换与缓存清理热键（如需完全配置化，可后续迁移至 keymap.yml）
    for i in range(1, 10):
        hk = keyboard.add_hotkey(f'ctrl+{i}', lambda idx=i: switch_role_by_index(idx, state))
        _registered_hotkeys.append(hk)
    _registered_hotkeys.append(keyboard.add_hotkey('ctrl+q', lambda: switch_role_by_index(10, state)))
    _registered_hotkeys.append(keyboard.add_hotkey('ctrl+e', lambda: switch_role_by_index(11, state)))
    _registered_hotkeys.append(keyboard.add_hotkey('ctrl+r', lambda: switch_role_by_index(12, state)))
    _registered_hotkeys.append(keyboard.add_hotkey('ctrl+t', lambda: switch_role_by_index(13, state)))
    _registered_hotkeys.append(keyboard.add_hotkey('ctrl+y', lambda: switch_role_by_index(14, state)))

    _registered_hotkeys.append(keyboard.add_hotkey('ctrl+tab', lambda: _clear_magic_cut_folder()))
    if state.start_hotkey:
        _registered_hotkeys.append(keyboard.add_hotkey(state.start_hotkey, lambda: _on_start_trigger(state), suppress=True))

    return _registered_hotkeys


# 注销热键
def unregister_hotkeys():
    for hk in list(_registered_hotkeys):
        try:
            keyboard.remove_hotkey(hk)
        except Exception:
            logger.exception("注销热键失败： %s", hk)
    _registered_hotkeys.clear()


# 设置一个defaultstate
_default_state = AppState()

def start_default():
    register_hotkeys(_default_state)


def stop_default():
    unregister_hotkeys()
