# -*- coding: utf-8 -*-
# GUI 功能
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageTk, Image
import threading
import io
import core
import clipboard
import hotkeys
import keyboard
import queue
import tkinter.font as tkfont

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局状态
state = hotkeys.AppState()
roles = list(core.mahoshojo.keys())
selected_image = None  # 保存剪贴板里的图片

# Tk 主窗口
root = tk.Tk()
root.title("魔裁 GUI")

# 控件占位
role_var = None
text_widget = None
btn_generate = None
preview_label = None
status_label = None
auto_paste_var = None
auto_send_var = None
hotkey_var = None

PREVIEW_MAX_SIZE = (360, 360)

#貌似是用来适配不同版本间的pillow的，aidebug的，我也不知道为啥
try:
    RESAMPLE = Image.Resampling.LANCZOS
except Exception:
    try:
        RESAMPLE = Image.LANCZOS
    except Exception:
        RESAMPLE = 1


#预处理窗口 这是我让ai加的一段预处理窗口，不过貌似没办法显示出来
class PreloadWindow(tk.Toplevel):
    def __init__(self, parent, title='资源预生成'):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.geometry('600x360')
        self.protocol('WM_DELETE_WINDOW', lambda: None)
        self.transient(parent)
        self.grab_set()

        self.text = tk.Text(self, wrap='word', state='disabled')
        self.text.pack(fill='both', expand=True, padx=8, pady=8)

        self.lbl = ttk.Label(self, text='正在预处理资源，请稍候...')
        self.lbl.pack(side='left', padx=8, pady=(0,8))

        # queue用来跨进程通信
        self._q = queue.Queue()
        self._polling = False

    def add_line(self, line: str):
        try:
            self.text.config(state='normal')
            self.text.insert('end', line + '\n')
            self.text.see('end')
            self.text.config(state='disabled')
        except Exception:
            logger.exception('add_line failed')

    def _start_poller(self, interval=100):
        if not self._polling:
            self._polling = True
            self.after(interval, self._poll_queue)

    def _poll_queue(self):
        try:
            while not self._q.empty():
                try:
                    msg = self._q.get_nowait()
                except Exception:
                    break
                if msg == '__PRELOAD_DONE__':
                    try:
                        self._on_done()
                    except Exception:
                        logger.exception('on_done failed')
                else:
                    self.add_line(msg)
        except Exception:
            logger.exception('poll_queue failed')
        finally:
            if self.winfo_exists():
                self.after(100, self._poll_queue)

    def start_prepare(self):
        try:
            self.deiconify()
            self.lift()
            self.attributes('-topmost', True)
            self.after(500, lambda: self.attributes('-topmost', False))
        except Exception:
            pass
        self._start_poller()

        def cb(msg):
            try:
                self._q.put(msg)
            except Exception:
                logger.exception('callback put failed')

        def worker():
            try:
                core.prepare_resources(callback=cb)
                self._q.put('__PRELOAD_DONE__')
            except Exception:
                logger.exception('prepare_resources worker failed')
                self._q.put('预处理出错')
                self._q.put('__PRELOAD_DONE__')

        threading.Thread(target=worker, daemon=True).start()

    def _on_done(self):
        try:
            self.lbl.config(text='预处理完成，窗口即将关闭')
        except Exception:
            pass
        self.after(800, self._close)

    def _close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


def show_preload_dialog():
    dlg = PreloadWindow(root, title='资源预生成')
    dlg.start_prepare()
    return dlg


def build_ui():
    global role_var, text_widget, btn_generate, preview_label, status_label, auto_paste_var, auto_send_var, hotkey_var

    frm_top = ttk.Frame(root)
    frm_top.pack(fill='x', padx=8, pady=6)

    # 角色标签
    ttk.Label(frm_top, text='角色:').pack(side='left')
    # 角色下拉框
    role_var = tk.StringVar(value=state.current_role)
    cmb_role = ttk.Combobox(frm_top, values=roles, textvariable=role_var, state='readonly')
    cmb_role.pack(side='left', padx=(4, 8))

    # 热键启用复选框
    hotkey_var = tk.BooleanVar(value=False)
    chk_hotkeys = ttk.Checkbutton(frm_top, text='启用热键', variable=hotkey_var, command=lambda: toggle_hotkeys(hotkey_var.get()))
    chk_hotkeys.pack(side='left', padx=4)

    # 自动粘贴复选框
    auto_paste_var = tk.BooleanVar(value=state.auto_paste)
    chk_paste = ttk.Checkbutton(frm_top, text='自动粘贴', variable=auto_paste_var, command=lambda: set_auto_paste(auto_paste_var.get()))
    chk_paste.pack(side='left', padx=4)

    # 自动发送复选框
    auto_send_var = tk.BooleanVar(value=state.auto_send)
    chk_send = ttk.Checkbutton(frm_top, text='自动发送', variable=auto_send_var, command=lambda: set_auto_send(auto_send_var.get()))
    chk_send.pack(side='left', padx=4)

    # 中间主区，左侧文本右侧预览
    frm_main = ttk.Frame(root)
    frm_main.pack(fill='both', expand=True, padx=8, pady=6)

    # 文本输入区域容器
    frm_left = ttk.Frame(frm_main)
    frm_left.pack(side='left', fill='both', expand=True)

    # 输入文本标签
    ttk.Label(frm_left, text='输入文本:').pack(anchor='w')
    # 文本输入控件
    try:
        families = tkfont.families()
        if 'Segoe UI Emoji' in families:
            text_font = ('Segoe UI Emoji', 12)
        elif 'Segoe UI Symbol' in families:
            text_font = ('Segoe UI Symbol', 12)
        else:
            text_font = ('Arial', 12)
    except Exception:
        text_font = ('Arial', 12)

    text_widget = tk.Text(frm_left, height=8, width=48, font=text_font)
    text_widget.pack(fill='both', expand=True)

    # 按钮行容器
    frm_buttons = ttk.Frame(frm_left)
    frm_buttons.pack(fill='x', pady=(6,0))

    # 生成按钮
    btn_generate = ttk.Button(frm_buttons, text='生成', command=on_generate_click)
    btn_generate.pack(side='left')

    # 从剪贴板读取图片按钮
    btn_paste_image = ttk.Button(frm_buttons, text='从剪贴板读取图片', command=on_paste_image_from_clipboard)
    btn_paste_image.pack(side='left', padx=6)

    # 右侧预览容器
    frm_right = ttk.Frame(frm_main, width=PREVIEW_MAX_SIZE[0])
    frm_right.pack(side='left', fill='y', padx=(8,0))

    # 预览标签
    ttk.Label(frm_right, text='预览:').pack(anchor='w')
    # 预览显示控件
    preview_label = ttk.Label(frm_right)
    preview_label.pack()

    # 状态栏
    status_label = ttk.Label(root, text='状态：就绪')
    status_label.pack(fill='x', padx=8, pady=(0,8))

    # 启动时异步预加载资源
    threading.Thread(target=_async_prepare_resources, daemon=True).start()

    def on_role_selected(event):
        try:
            selected = role_var.get()
            state.current_role = selected
            try:
                idx = roles.index(selected) + 1
                hotkeys.switch_role_by_index(idx, state)
            except Exception:
                logger.exception('切换失败')
        except Exception:
            logger.exception('切换失败')
            
    # 用来同步快捷键设置的角色和下拉框的角色
    cmb_role.bind('<<ComboboxSelected>>', on_role_selected)


def _async_prepare_resources():
    try:
        logger.info('开始预处理资源')
        root.after(0, lambda: status_label.config(text='状态：预生成资源中...'))
        core.prepare_resources()
        logger.info('预处理资源完成')
        root.after(0, lambda: status_label.config(text='状态：就绪'))
    except Exception:
        logger.exception('prepare_resources failed')
        root.after(0, lambda: status_label.config(text='状态：预生成失败'))


def on_generate_click():
    role = role_var.get()
    text = text_widget.get('1.0', 'end').strip()
    content_image = selected_image

    btn_generate.config(state='disabled')
    status_label.config(text='状态：生成中...')

    # 后台执行耗时生成
    threading.Thread(target=_worker_generate, args=(text or None, content_image, role), daemon=True).start()


def _worker_generate(text, content_image, role):
    try:
        font_path = core.get_resource_path(core.mahoshojo[role]['font']) if role in core.mahoshojo else None
        png_bytes, expr = core.generate_image(text=text, content_image=content_image, role_name=role, font_path=font_path, last_value=state.last_expression, expression=-1)
        # 更新 last_expression（在主线程也可更新）
        if expr is not None:
            state.last_expression = expr
        root.after(0, lambda: on_result(png_bytes, expr))
    except Exception as e:
        logger.exception('生成失败')
        root.after(0, lambda: on_error(str(e)))


def on_result(png_bytes, expr):
    btn_generate.config(state='normal')
    if png_bytes is None:
        status_label.config(text='状态：生成失败')
        return

    # 显示预览
    try:
        img = Image.open(io.BytesIO(png_bytes))
        # 缩放以适配预览区
        img.thumbnail(PREVIEW_MAX_SIZE, RESAMPLE)
        tkimg = ImageTk.PhotoImage(img)
        preview_label.config(image=tkimg)
        preview_label.image = tkimg
    except Exception:
        logger.exception('预览生成失败')

    status_label.config(text=f'状态：生成完成 表情:{expr}')

    # 自动粘贴/发送
    if auto_paste_var.get():
        try:
            clipboard.copy_png_bytes_to_clipboard(png_bytes)
        except Exception:
            logger.exception('复制失败')
            status_label.config(text='状态：复制到剪贴板失败')
            return
        # 使用 keyboard.call_later 在 keyboard 的线程安全发送按键
        keyboard.call_later(lambda: keyboard.send(state.paste_hotkey), delay=0.12)
        if auto_send_var.get():
            keyboard.call_later(lambda: keyboard.send(state.send_hotkey), delay=0.35)


def on_error(msg: str):
    btn_generate.config(state='normal')
    status_label.config(text=f'状态：错误: {msg}')
    messagebox.showerror('生成错误', msg)


def on_paste_image_from_clipboard():
    global selected_image
    try:
        img = clipboard.try_get_image()
        if img is None:
            status_label.config(text='状态：剪贴板没有图片')
            return
        selected_image = img
        # 显示缩略预览
        img2 = img.copy()
        img2.thumbnail(PREVIEW_MAX_SIZE, RESAMPLE)
        tkimg = ImageTk.PhotoImage(img2)
        preview_label.config(image=tkimg)
        preview_label.image = tkimg
        status_label.config(text='状态：已获取剪贴板图片')
    except Exception:
        logger.exception('获取剪贴板图片失败')
        status_label.config(text='状态：获取剪贴板图片失败')


def toggle_hotkeys(enable: bool):
    if enable:
        hotkeys.register_hotkeys(state)
        status_label.config(text='状态：热键已启用')
    else:
        hotkeys.unregister_hotkeys()
        status_label.config(text='状态：热键已禁用')


def set_auto_paste(value: bool):
    state.auto_paste = value


def set_auto_send(value: bool):
    state.auto_send = value


def on_close():
    try:
        hotkeys.unregister_hotkeys()
    except Exception:
        pass
    root.destroy()


#在预处理完成前不显示主窗口
if __name__ == '__main__':
    root.withdraw()
    preload = PreloadWindow(root)
    preload.start_prepare()
    #阻塞
    root.wait_window(preload)
    #重新显示
    root.deiconify()
    build_ui()

    #复选框打勾
    try:
        hotkey_var.set(True)
    except Exception:
        pass

    try:
        #注册当前状态的热键
        hotkeys.register_hotkeys(state)
    except Exception:
        logger.exception('热键注册失败')

    #注册下拉栏回调函数
    try:
        def _on_role_change(new_role):
            try:
                root.after(0, lambda: role_var.set(new_role))
            except Exception:
                logger.exception('下拉栏更新失败')
        hotkeys.role_change_callback = _on_role_change
    except Exception:
        logger.exception('注册回调函数失败')

    root.protocol('WM_DELETE_WINDOW', on_close)
    root.mainloop()