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
import os
from config_loader import BACKGROUND_INDEXES, save_process_whitelist, load_keymap, save_keymap, list_fonts, save_chara_font, get_resource_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局状态
state = hotkeys.AppState()
selected_image = None  # 保存剪贴板里的图片

# 背景选择状态
selected_bg_index = -1  # -1 表示随机

# Tk 主窗口
root = tk.Tk()
root.title("魔裁，启动！！")

# 主题与 DPI 缩放
def _apply_theme_and_dpi():
    try:
        style = ttk.Style()
        # 选择更现代的主题（优先 vista/xpnative，其次 clam）
        for theme in ('vista', 'xpnative', 'clam'):  # 顺序尝试
            if theme in style.theme_names():
                style.theme_use(theme)
                logger.info('应用主题: %s', theme)
                break
    except Exception:
        logger.exception('应用主题失败')
    # 自动 DPI 缩放，按屏幕 DPI 计算比例：ppi/72
    try:
        ppi = root.winfo_fpixels('1i')  # 每英寸像素
        scaling = max(1.0, float(ppi) / 72.0)
        root.tk.call('tk', 'scaling', scaling)
        logger.info('应用 DPI 缩放: ppi=%.2f scaling=%.2f', ppi, scaling)
    except Exception:
        # 退回固定缩放
        try:
            root.tk.call('tk', 'scaling', 1.25)
            logger.info('应用默认 DPI 缩放: 1.25')
        except Exception:
            logger.exception('设置 DPI 缩放失败')

_apply_theme_and_dpi()

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

try:
    RESAMPLE = Image.Resampling.LANCZOS
except Exception:
    try:
        RESAMPLE = Image.LANCZOS
    except Exception:
        RESAMPLE = 1


class PreloadWindow(tk.Toplevel):
    def __init__(self, parent, title='资源预生成'):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.geometry('640x420')
        self.protocol('WM_DELETE_WINDOW', lambda: None)
        self.transient(parent)
        self.grab_set()

        self.text = tk.Text(self, wrap='word', state='disabled')
        self.text.pack(fill='both', expand=True, padx=8, pady=8)

        self.lbl = ttk.Label(self, text='正在预处理资源，请稍候...')
        self.lbl.pack(side='left', padx=8, pady=(0,8))

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
                logger.exception('预处理出错')
                self._q.put('预处理出错')
                self._q.put('__PRELOAD_DONE__')

        threading.Thread(target=worker, daemon=True).start()

    def _on_done(self):
        try:
            self.lbl.config(text='预处理完成，窗口即将关闭')
        except Exception:
            pass
        self.after(150, self._close)

    def _close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title('设置')
        self.geometry('560x460')
        self.transient(parent)
        self.grab_set()

        self._km = load_keymap() or {}

        nb = ttk.Notebook(self)
        self.tab_whitelist = ttk.Frame(nb)
        self.tab_hotkeys = ttk.Frame(nb)
        self.tab_font = ttk.Frame(nb)
        nb.add(self.tab_whitelist, text='窗口白名单')
        nb.add(self.tab_hotkeys, text='快捷键')
        nb.add(self.tab_font, text='角色字体')
        nb.pack(fill='both', expand=True, padx=8, pady=6)

        self._build_whitelist_tab()
        self._build_hotkeys_tab()
        self._build_font_tab()

        frm_btns = ttk.Frame(self)
        frm_btns.pack(fill='x', padx=8, pady=6)
        ttk.Button(frm_btns, text='保存', command=self._on_save).pack(side='right', padx=4)
        ttk.Button(frm_btns, text='取消', command=self.destroy).pack(side='right')

    # 白名单页
    def _build_whitelist_tab(self):
        self.var_enable_whitelist = tk.BooleanVar(value=state.enable_whitelist)
        chk = ttk.Checkbutton(self.tab_whitelist, text='启用窗口白名单', variable=self.var_enable_whitelist)
        chk.pack(anchor='w', padx=6, pady=6)

        frm = ttk.Frame(self.tab_whitelist)
        frm.pack(fill='both', expand=True, padx=6, pady=4)
        self.lst_whitelist = tk.Listbox(frm, height=10)
        self.lst_whitelist.pack(side='left', fill='both', expand=True)
        scrl = ttk.Scrollbar(frm, orient='vertical', command=self.lst_whitelist.yview)
        scrl.pack(side='left', fill='y')
        self.lst_whitelist.config(yscrollcommand=scrl.set)

        for name in (state.window_whitelist or []):
            self.lst_whitelist.insert('end', name)

        frm2 = ttk.Frame(self.tab_whitelist)
        frm2.pack(fill='x', padx=6, pady=4)
        self.entry_process = ttk.Entry(frm2)
        self.entry_process.pack(side='left', fill='x', expand=True)
        ttk.Button(frm2, text='添加', command=self._add_process).pack(side='left', padx=4)
        ttk.Button(frm2, text='删除选中', command=self._remove_selected).pack(side='left')

    def _add_process(self):
        val = self.entry_process.get().strip()
        if not val:
            return
        self.lst_whitelist.insert('end', val)
        self.entry_process.delete(0, 'end')

    def _remove_selected(self):
        for i in reversed(self.lst_whitelist.curselection()):
            self.lst_whitelist.delete(i)

    # 快捷键页
    def _build_hotkeys_tab(self):
        grid = ttk.Frame(self.tab_hotkeys)
        grid.pack(fill='both', expand=True, padx=8, pady=6)
        labels = [
            ('启动生成', 'start_hotkey', state.start_hotkey),
            ('粘贴', 'paste_hotkey', state.paste_hotkey),
            ('发送', 'send_hotkey', state.send_hotkey),
            ('全选', 'select_all_hotkey', state.select_all_hotkey),
            ('剪切', 'cut_hotkey', state.cut_hotkey),
        ]
        self.hotkey_vars = {}
        for r, (label, key, default) in enumerate(labels):
            ttk.Label(grid, text=label + '：').grid(row=r, column=0, sticky='e', padx=4, pady=4)
            var = tk.StringVar(value=str(self._km.get(key, default)))
            ent = ttk.Entry(grid, textvariable=var, width=24)
            ent.grid(row=r, column=1, sticky='w', padx=4, pady=4)
            self.hotkey_vars[key] = var
        for i in range(2):
            grid.columnconfigure(i, weight=1)

    # 角色字体页
    def _build_font_tab(self):
        frm = ttk.Frame(self.tab_font)
        frm.pack(fill='both', expand=True, padx=8, pady=6)

        ttk.Label(frm, text='角色：').grid(row=0, column=0, sticky='e', padx=4, pady=4)
        self.var_role = tk.StringVar(value=state.current_role)
        cmb_role = ttk.Combobox(frm, values=list(core.mahoshojo.keys()), textvariable=self.var_role, state='readonly', width=18)
        cmb_role.grid(row=0, column=1, sticky='w', padx=4, pady=4)

        ttk.Label(frm, text='字体文件：').grid(row=1, column=0, sticky='e', padx=4, pady=4)
        # 初始值设置为当前角色字体
        current_font = core.mahoshojo.get(state.current_role, {}).get('font', '')
        self.var_font_file = tk.StringVar(value=current_font)
        fonts = list_fonts()
        self.cmb_font = ttk.Combobox(frm, values=fonts, textvariable=self.var_font_file, state='readonly', width=24)
        self.cmb_font.grid(row=1, column=1, sticky='w', padx=4, pady=4)

        ttk.Button(frm, text='应用到该角色', command=self._apply_role_font).grid(row=2, column=1, sticky='w', padx=4, pady=6)

        frm.columnconfigure(1, weight=1)

        # 当角色选择变化时，同步更新字体选择的当前值为该角色已有字体
        def on_role_change(_evt=None):
            role = self.var_role.get()
            font_val = core.mahoshojo.get(role, {}).get('font', '')
            try:
                self.var_font_file.set(font_val)
            except Exception:
                logger.exception('更新角色字体初始值失败')
        cmb_role.bind('<<ComboboxSelected>>', on_role_change)
        # 进入界面时也确保一次同步
        on_role_change()

    def _apply_role_font(self):
        role = self.var_role.get().strip()
        font_file = self.var_font_file.get().strip()
        if not role or not font_file:
            logger.info('字体未变更或参数缺失 role=%s font=%s', role, font_file)
            return
        cfg_path = get_resource_path('config/chara_meta.yml')
        logger.info('准备保存角色字体: role=%s font=%s -> %s', role, font_file, cfg_path)
        ok = save_chara_font(role, font_file)
        logger.info('保存角色字体结果: ok=%s', ok)
        if ok:
            try:
                core.mahoshojo[role]['font'] = font_file
            except Exception:
                pass
            messagebox.showinfo('字体', f'已应用字体 {font_file} 到角色 {role}')
        else:
            messagebox.showerror('字体', '保存失败，请检查配置文件权限')

    def _on_save(self):
        # 白名单
        items = [self.lst_whitelist.get(i) for i in range(self.lst_whitelist.size())]
        state.window_whitelist = items
        state.enable_whitelist = bool(self.var_enable_whitelist.get())
        wl_path = get_resource_path('config/process_whitelist.yml')
        logger.info('准备保存白名单(%d)：%s -> %s', len(items), items, wl_path)
        ok_wl = save_process_whitelist('win32', items)
        logger.info('保存白名单结果: ok=%s', ok_wl)

        # 快捷键 -> keymap.yml
        mapping = {}
        for k, var in self.hotkey_vars.items():
            val = var.get().strip()
            if not val:
                continue
            setattr(state, k, val)
            mapping[k] = val
        km_path = get_resource_path('config/keymap.yml')
        logger.info('准备保存快捷键：%s -> %s', mapping, km_path)
        ok_km = save_keymap(mapping)
        logger.info('保存快捷键结果: ok=%s', ok_km)
        if not ok_km:
            messagebox.showwarning('提示', '保存快捷键失败，已应用到当前会话')

        # 使新启动热键生效
        try:
            if hotkey_var and hotkey_var.get():
                hotkeys.unregister_hotkeys()
                hotkeys.register_hotkeys(state)
                logger.info('热键已重新注册: start=%s paste=%s send=%s', state.start_hotkey, state.paste_hotkey, state.send_hotkey)
        except Exception:
            logger.exception('重新注册热键失败')

        self.destroy()


def build_ui():
    global role_var, text_widget, btn_generate, preview_label, status_label, auto_paste_var, auto_send_var, hotkey_var
    global selected_bg_index

    frm_top = ttk.Frame(root)
    frm_top.pack(fill='x', padx=8, pady=6)

    ttk.Label(frm_top, text='角色:').pack(side='left')
    role_var = tk.StringVar(value=state.current_role)
    cmb_role = ttk.Combobox(frm_top, values=list(core.mahoshojo.keys()), textvariable=role_var, state='readonly')
    cmb_role.pack(side='left', padx=(4, 8))

    ttk.Label(frm_top, text='表情:').pack(side='left')
    global expression_var, cmb_expression
    expression_var = tk.StringVar(value='随机')
    cmb_expression = ttk.Combobox(frm_top, textvariable=expression_var, state='readonly', width=8)
    cmb_expression.pack(side='left', padx=(4, 8))

    ttk.Label(frm_top, text='背景:').pack(side='left')
    global bg_var, cmb_bg
    bg_var = tk.StringVar(value='随机')
    count_bg = len(BACKGROUND_INDEXES) or 16
    options_bg = ['随机'] + [str(i) for i in range(1, count_bg + 1)]
    cmb_bg = ttk.Combobox(frm_top, textvariable=bg_var, values=options_bg, state='readonly', width=8)
    cmb_bg.pack(side='left', padx=(4, 8))

    def on_bg_selected(event):
        global selected_bg_index
        try:
            val = bg_var.get()
            selected_bg_index = -1 if val == '随机' else int(val)
            logger.info('背景设置为: %s', val)
        except Exception:
            logger.exception('设置背景失败')
            selected_bg_index = -1

    cmb_bg.bind('<<ComboboxSelected>>', on_bg_selected)

    ttk.Button(frm_top, text='设置', command=lambda: SettingsDialog(root)).pack(side='left', padx=8)

    hotkey_var = tk.BooleanVar(value=False)
    chk_hotkeys = ttk.Checkbutton(frm_top, text='启用热键', variable=hotkey_var, command=lambda: toggle_hotkeys(hotkey_var.get()))
    chk_hotkeys.pack(side='left', padx=4)

    auto_paste_var = tk.BooleanVar(value=state.auto_paste)
    chk_paste = ttk.Checkbutton(frm_top, text='自动粘贴', variable=auto_paste_var, command=lambda: set_auto_paste(auto_paste_var.get()))
    chk_paste.pack(side='left', padx=4)

    auto_send_var = tk.BooleanVar(value=state.auto_send)
    chk_send = ttk.Checkbutton(frm_top, text='自动发送', variable=auto_send_var, command=lambda: set_auto_send(auto_send_var.get()))
    chk_send.pack(side='left', padx=4)

    frm_main = ttk.Frame(root)
    frm_main.pack(fill='both', expand=True, padx=8, pady=6)

    frm_left = ttk.Frame(frm_main)
    frm_left.pack(side='left', fill='both', expand=True)

    ttk.Label(frm_left, text='输入文本:').pack(anchor='w')

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

    global text_widget
    text_widget = tk.Text(frm_left, height=8, width=48, font=text_font)
    text_widget.pack(fill='both', expand=True)

    frm_buttons = ttk.Frame(frm_left)
    frm_buttons.pack(fill='x', pady=(6,0))

    global btn_generate
    btn_generate = ttk.Button(frm_buttons, text='生成', command=on_generate_click)
    btn_generate.pack(side='left')

    btn_paste_image = ttk.Button(frm_buttons, text='从剪贴板读取图片', command=on_paste_image_from_clipboard)
    btn_paste_image.pack(side='left', padx=6)

    frm_right = ttk.Frame(frm_main, width=PREVIEW_MAX_SIZE[0])
    frm_right.pack(side='left', fill='y', padx=(8,0))

    ttk.Label(frm_right, text='预览:').pack(anchor='w')
    global preview_label
    preview_label = ttk.Label(frm_right)
    preview_label.pack()

    global status_label
    status_label = ttk.Label(root, text='状态：就绪')
    status_label.pack(fill='x', padx=8, pady=(0,8))

    def update_expression_options(role_name):
        try:
            emotion_count = core.mahoshojo[role_name]['emotion_count']
            options = ['随机'] + [str(i) for i in range(1, emotion_count + 1)]
            cmb_expression['values'] = options
            expression_var.set('随机')
        except Exception:
            logger.exception('更新表情选项失败')

    update_expression_options(state.current_role)

    def on_role_selected(event):
        try:
            selected = role_var.get()
            state.current_role = selected
            update_expression_options(selected)
            try:
                idx = list(core.mahoshojo.keys()).index(selected) + 1
                hotkeys.switch_role_by_index(idx, state)
            except Exception:
                logger.exception('切换失败')
        except Exception:
            logger.exception('切换失败')
    
    def on_expression_selected(event):
        try:
            selected = expression_var.get()
            state.current_expression = -1 if selected == '随机' else int(selected)
            logger.info('表情设置为: %s', selected)
        except Exception:
            logger.exception('设置表情失败')

    cmb_role.bind('<<ComboboxSelected>>', on_role_selected)
    cmb_expression.bind('<<ComboboxSelected>>', on_expression_selected)


def on_generate_click():
    role = role_var.get()
    text = text_widget.get('1.0', 'end').strip()
    content_image = selected_image

    try:
        selected_expr = expression_var.get()
        expressionindex = -1 if selected_expr == '随机' else int(selected_expr)
    except Exception:
        logger.exception('读取表情选择器失败')
        expressionindex = -1

    btn_generate.config(state='disabled')
    status_label.config(text='状态：生成中...')

    threading.Thread(target=_worker_generate, args=(text or None, content_image, role, expressionindex, selected_bg_index), daemon=True).start()


def _worker_generate(text, content_image, role, expressionindex, bg_index):
    try:
        font_path = core.get_resource_path(os.path.join("assets", "fonts", core.mahoshojo[role]['font'])) if role in core.mahoshojo else None
        png_bytes, expr = core.generate_image(text=text, content_image=content_image, role_name=role, font_path=font_path, last_value=state.last_expression, expression=expressionindex, bg_index=bg_index)
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

    try:
        img = Image.open(io.BytesIO(png_bytes))
        img.thumbnail(PREVIEW_MAX_SIZE, RESAMPLE)
        tkimg = ImageTk.PhotoImage(img)
        preview_label.config(image=tkimg)
        preview_label.image = tkimg
    except Exception:
        logger.exception('预览生成失败')

    status_label.config(text=f'状态：生成完成 表情:{expr}')

    if auto_paste_var.get():
        try:
            clipboard.copy_png_bytes_to_clipboard(png_bytes)
        except Exception:
            logger.exception('复制失败')
            status_label.config(text='状态：复制到剪贴板失败')
            return
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


if __name__ == '__main__':
    preload = PreloadWindow(root)
    preload.start_prepare()
    try:
        import time as _time
        while True:
            if not preload.winfo_exists():
                break
            root.update()
            _time.sleep(0.05)
    except Exception:
        try:
            root.wait_window(preload)
        except Exception:
            pass
    root.deiconify()
    build_ui()

    try:
        hotkey_var.set(True)
        toggle_hotkeys(True)
    except Exception:
        logger.exception('热键注册失败')

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