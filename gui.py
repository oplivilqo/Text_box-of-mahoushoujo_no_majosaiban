"""魔裁文本框 GUI 版本"""

import tkinter as tk
from tkinter import ttk
from PIL import ImageTk
import threading
import os
# import yaml
import time

from core import ManosabaCore


class SettingsWindow:
    """设置窗口"""

    def __init__(self, parent, core, gui):
        self.parent = parent
        self.core = core
        self.gui = gui

        # 加载设置
        self.settings = self.core.get_gui_settings()

        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("设置")
        self.window.geometry("500x600")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        # 创建Notebook用于标签页
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 常规设置标签页
        general_frame = ttk.Frame(notebook, padding="10")
        notebook.add(general_frame, text="常规设置")

        # 快捷键设置标签页
        hotkey_frame = ttk.Frame(notebook, padding="10")
        notebook.add(hotkey_frame, text="快捷键设置")

        self.setup_general_tab(general_frame)
        self.setup_hotkey_tab(hotkey_frame)

        # 按钮框架
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="保存", command=self.on_save).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(button_frame, text="取消", command=self.window.destroy).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(button_frame, text="应用", command=self.on_apply).pack(
            side=tk.RIGHT, padx=5
        )

    def setup_general_tab(self, parent):
        """设置常规设置标签页"""
        # 字体设置
        font_frame = ttk.LabelFrame(parent, text="字体设置", padding="10")
        font_frame.pack(fill=tk.X, pady=5)

        ttk.Label(font_frame, text="对话框字体:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # 获取可用字体列表
        available_fonts = self.get_available_fonts()
        
        self.font_family_var = tk.StringVar(
            value=self.settings.get("font_family", "Arial")
        )
        font_combo = ttk.Combobox(
            font_frame,
            textvariable=self.font_family_var,
            values=available_fonts,
            state="readonly",
            width=20,
        )
        font_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        font_combo.bind("<<ComboboxSelected>>", self.on_setting_changed)

        # 字号设置
        ttk.Label(font_frame, text="对话框字号:").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.font_size_var = tk.IntVar(value=self.settings.get("font_size", 12))
        font_size_spin = ttk.Spinbox(
            font_frame, textvariable=self.font_size_var, from_=8, to=72, width=10
        )
        font_size_spin.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        font_size_spin.bind("<KeyRelease>", self.on_setting_changed)
        font_size_spin.bind("<<Increment>>", self.on_setting_changed)
        font_size_spin.bind("<<Decrement>>", self.on_setting_changed)
        
        # 字体说明
        ttk.Label(font_frame, text="注：角色名字字体保持不变，使用角色配置中的专用字体", 
                 font=("", 8), foreground="gray").grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=2
        )

        # 图像压缩设置
        compression_frame = ttk.LabelFrame(parent, text="图像压缩设置", padding="10")
        compression_frame.pack(fill=tk.X, pady=5)

        # 像素减少压缩
        self.pixel_reduction_var = tk.BooleanVar(
            value=self.settings.get("image_compression", {}).get("pixel_reduction_enabled", False)
        )
        pixel_reduction_cb = ttk.Checkbutton(
            compression_frame,
            text="启用像素削减压缩",
            variable=self.pixel_reduction_var,
            command=self.on_setting_changed
        )
        pixel_reduction_cb.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        # 像素减少比例滑条
        ttk.Label(compression_frame, text="像素削减比例:").grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        
        pixel_frame = ttk.Frame(compression_frame)
        pixel_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.pixel_reduction_ratio_var = tk.IntVar(
            value=self.settings.get("image_compression", {}).get("pixel_reduction_ratio", 50)
        )
        pixel_scale = ttk.Scale(
            pixel_frame,
            from_=10,
            to=90,
            variable=self.pixel_reduction_ratio_var,
            orient=tk.HORIZONTAL,
            length=200
        )
        pixel_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        pixel_scale.bind("<ButtonRelease-1>", self.on_setting_changed)
        
        self.pixel_value_label = ttk.Label(pixel_frame, text=f"{self.pixel_reduction_ratio_var.get()}%")
        self.pixel_value_label.pack(side=tk.RIGHT, padx=5)
        
        # 绑定变量变化更新标签
        self.pixel_reduction_ratio_var.trace_add("write", self.update_pixel_label)

        # 压缩说明
        ttk.Label(compression_frame, 
                 text="注：压缩质量影响PNG输出质量，像素减少通过降低BMP图像分辨率来减小文件大小", 
                 font=("", 8), foreground="gray").grid(
            row=4, column=0, columnspan=2, sticky=tk.W, pady=2
        )

    def update_pixel_label(self, *args):
        """更新像素减少比例标签"""
        self.pixel_value_label.config(text=f"{self.pixel_reduction_ratio_var.get()}%")
        self.on_setting_changed()
    def get_available_fonts(self):
        """获取可用字体列表，优先显示项目字体"""
        fonts_dir = os.path.join(self.core.config.BASE_PATH, "assets", "fonts")
        project_fonts = []
        # system_fonts = []
        
        # 获取项目字体
        if os.path.exists(fonts_dir):
            for file in os.listdir(fonts_dir):
                if file.lower().endswith(('.ttf', '.otf', '.ttc')):
                    font_name = os.path.splitext(file)[0]
                    project_fonts.append(font_name)
        return project_fonts

    def setup_hotkey_tab(self, parent):
        """设置快捷键标签页"""
        # 创建滚动框架
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 从core中获取当前平台的热键
        hotkeys = self.core.keymap
        
        # 生成快捷键放在第一个
        generate_frame = ttk.LabelFrame(scrollable_frame, text="生成控制", padding="10")
        generate_frame.pack(fill=tk.X, pady=5)

        self.create_hotkey_display_row(
            generate_frame,
            "生成图片",
            "start_generate",
            hotkeys.get("start_generate", "ctrl+e"),
            0,
        )

        # 角色切换快捷键
        char_frame = ttk.LabelFrame(scrollable_frame, text="角色切换", padding="10")
        char_frame.pack(fill=tk.X, pady=5)

        self.create_hotkey_display_row(
            char_frame,
            "向前切换角色",
            "next_character",
            hotkeys.get("next_character", "ctrl+j"),
            0,
        )
        self.create_hotkey_display_row(
            char_frame,
            "向后切换角色",
            "prev_character",
            hotkeys.get("prev_character", "ctrl+l"),
            1,
        )

        # 表情切换快捷键 - 新增
        emotion_frame = ttk.LabelFrame(scrollable_frame, text="表情切换", padding="10")
        emotion_frame.pack(fill=tk.X, pady=5)

        self.create_hotkey_display_row(
            emotion_frame,
            "向前切换表情",
            "next_emotion",
            hotkeys.get("next_emotion", "ctrl+u"),
            0,
        )
        self.create_hotkey_display_row(
            emotion_frame,
            "向后切换表情",
            "prev_emotion",
            hotkeys.get("prev_emotion", "ctrl+o"),
            1,
        )

        # 背景切换快捷键
        bg_frame = ttk.LabelFrame(scrollable_frame, text="背景切换", padding="10")
        bg_frame.pack(fill=tk.X, pady=5)

        self.create_hotkey_display_row(
            bg_frame,
            "向前切换背景",
            "next_background",
            hotkeys.get("next_background", "ctrl+i"),
            0,
        )
        self.create_hotkey_display_row(
            bg_frame,
            "向后切换背景",
            "prev_background",
            hotkeys.get("prev_background", "ctrl+k"),
            1,
        )

        # 控制快捷键
        control_frame = ttk.LabelFrame(scrollable_frame, text="控制", padding="10")
        control_frame.pack(fill=tk.X, pady=5)

        self.create_hotkey_display_row(
            control_frame,
            "继续/停止监听",
            "toggle_listener",
            hotkeys.get("toggle_listener", "alt+ctrl+p"),
            0,
        )

        # 角色快速选择快捷键
        quick_char_frame = ttk.LabelFrame(
            scrollable_frame, text="角色快速选择", padding="10"
        )
        quick_char_frame.pack(fill=tk.X, pady=5)

        # 获取所有角色选项
        character_options = [""]  # 空选项
        for char_id in self.core.character_list:
            full_name = self.core.get_character(char_id, full_name=True)
            character_options.append(f"{full_name} ({char_id})")

        quick_chars = self.settings.get("quick_characters", {})

        for i in range(1, 7):
            # 获取当前设置的角色
            current_char = quick_chars.get(f"character_{i}", "")
            if current_char and current_char in self.core.character_list:
                current_display = f"{self.core.get_character(current_char, full_name=True)} ({current_char})"
            else:
                current_display = ""

            self.create_character_hotkey_row(
                quick_char_frame,
                f"快捷键 {i}",
                f"character_{i}",
                hotkeys.get(f"character_{i}", f"ctrl+{i}"),
                current_display,
                character_options,
                i - 1,
            )

    def create_hotkey_display_row(self, parent, label, key, hotkey_value, row):
        """创建快捷键显示行（只读）"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)

        # 快捷键显示（只读）
        hotkey_var = tk.StringVar(value=hotkey_value)
        setattr(self, f"{key}_hotkey_var", hotkey_var)

        entry = ttk.Entry(parent, textvariable=hotkey_var, width=20, state="readonly")
        entry.grid(row=row, column=1, padx=5, pady=2, sticky=tk.W)

        # 提示信息
        # ttk.Label(parent, text="在keymap.yml中修改").grid(row=row, column=2, padx=5, pady=2)

    def create_character_hotkey_row(
        self, parent, label, key, hotkey_value, current_char, character_options, row
    ):
        """创建角色快捷键设置行"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)

        # 角色选择下拉框
        char_var = tk.StringVar(value=current_char)
        setattr(self, f"{key}_char_var", char_var)

        char_combo = ttk.Combobox(
            parent,
            textvariable=char_var,
            values=character_options,
            state="readonly",
            width=25,
        )
        char_combo.grid(row=row, column=1, padx=5, pady=2, sticky=tk.W)
        char_combo.bind("<<ComboboxSelected>>", self.on_setting_changed)

        # 快捷键显示（只读）
        hotkey_var = tk.StringVar(value=hotkey_value)
        setattr(self, f"{key}_hotkey_var", hotkey_var)

        entry = ttk.Entry(parent, textvariable=hotkey_var, width=15, state="readonly")
        entry.grid(row=row, column=2, padx=5, pady=2, sticky=tk.W)

        # 提示信息
        ttk.Label(parent, text="在keymap.yml中修改").grid(
            row=row, column=3, padx=5, pady=2
        )

    def on_setting_changed(self, event=None):
        """设置改变时的回调"""
        # 更新设置字典
        self.settings["font_family"] = self.font_family_var.get()
        self.settings["font_size"] = self.font_size_var.get()

        # 更新图像压缩设置
        if "image_compression" not in self.settings:
            self.settings["image_compression"] = {}
        
        # self.settings["image_compression"]["enabled"] = self.compression_enabled_var.get()
        # self.settings["image_compression"]["quality_preset"] = self.quality_preset_var.get()
        self.settings["image_compression"]["pixel_reduction_enabled"] = self.pixel_reduction_var.get()
        self.settings["image_compression"]["pixel_reduction_ratio"] = self.pixel_reduction_ratio_var.get()

        # 更新快速角色设置
        quick_characters = {}
        for i in range(1, 7):
            char_var = getattr(self, f"character_{i}_char_var")
            char_display = char_var.get()
            # 从显示文本中提取角色ID
            if char_display and "(" in char_display and ")" in char_display:
                char_id = char_display.split("(")[-1].rstrip(")")
                quick_characters[f"character_{i}"] = char_id
            else:
                quick_characters[f"character_{i}"] = ""

        self.settings["quick_characters"] = quick_characters

        # 即时保存设置
        self.core.save_gui_settings(self.settings)

    def on_save(self):
        """保存设置并关闭窗口"""
        self.on_setting_changed()
        self.window.destroy()

    def on_apply(self):
        """应用设置但不关闭窗口"""
        self.on_setting_changed()

class ManosabaGUI:
    """魔裁文本框 GUI"""

    def __init__(self):
        self.core = ManosabaCore()
        self.root = tk.Tk()
        self.root.title("魔裁文本框生成器")
        self.root.geometry("800x700")

        # 预览相关
        self.preview_size = (700, 525)

        # 热键监听状态
        self.hotkey_listener_active = True
        # 图片生成状态
        self.is_generating = False

        self.setup_gui()
        self.root.bind("<Configure>", self.on_window_resize)

        self.update_status("就绪 - 等待生成预览")
        self.setup_hotkeys()

    def setup_gui(self):
        """设置 GUI 界面"""
        # 创建菜单栏
        self.setup_menu()

        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 角色选择
        ttk.Label(main_frame, text="选择角色:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.character_var = tk.StringVar()
        character_combo = ttk.Combobox(
            main_frame, textvariable=self.character_var, state="readonly", width=30
        )
        character_combo["values"] = [
            f"{self.core.get_character(char_id, full_name=True)} ({char_id})"
            for char_id in self.core.character_list
        ]
        character_combo.set(
            f"{self.core.get_character(full_name=True)} ({self.core.get_character()})"
        )
        character_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        character_combo.bind("<<ComboboxSelected>>", self.on_character_changed)

        # 表情选择框架
        emotion_frame = ttk.LabelFrame(main_frame, text="表情选择", padding="5")
        emotion_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # 表情随机选择
        self.emotion_random_var = tk.BooleanVar(value=True)
        emotion_random_cb = ttk.Checkbutton(
            emotion_frame,
            text="随机表情",
            variable=self.emotion_random_var,
            command=self.on_emotion_random_changed,
        )
        emotion_random_cb.grid(row=0, column=0, sticky=tk.W, padx=5)

        # 表情下拉框
        ttk.Label(emotion_frame, text="指定表情:").grid(
            row=0, column=1, sticky=tk.W, padx=5
        )
        self.emotion_var = tk.StringVar()
        self.emotion_combo = ttk.Combobox(
            emotion_frame, textvariable=self.emotion_var, state="readonly", width=15
        )
        emotion_count = self.core.get_current_emotion_count()
        self.emotion_combo["values"] = [
            f"表情 {i}" for i in range(1, emotion_count + 1)
        ]
        self.emotion_combo.set("表情 1")
        self.emotion_combo.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=5)
        self.emotion_combo.bind("<<ComboboxSelected>>", self.on_emotion_changed)
        self.emotion_combo.config(state="disabled")

        emotion_frame.columnconfigure(2, weight=1)

        # 背景选择框架
        background_frame = ttk.LabelFrame(main_frame, text="背景选择", padding="5")
        background_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )

        # 背景随机选择
        self.background_random_var = tk.BooleanVar(value=True)
        background_random_cb = ttk.Checkbutton(
            background_frame,
            text="随机背景",
            variable=self.background_random_var,
            command=self.on_background_random_changed,
        )
        background_random_cb.grid(row=0, column=0, sticky=tk.W, padx=5)

        # 背景下拉框
        ttk.Label(background_frame, text="指定背景:").grid(
            row=0, column=1, sticky=tk.W, padx=5
        )
        self.background_var = tk.StringVar()
        self.background_combo = ttk.Combobox(
            background_frame,
            textvariable=self.background_var,
            state="readonly",
            width=15,
        )
        background_count = self.core.image_processor.background_count
        self.background_combo["values"] = [
            f"背景 {i}" for i in range(1, background_count + 1)
        ]
        self.background_combo.set("背景 1")
        self.background_combo.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=5)
        self.background_combo.bind("<<ComboboxSelected>>", self.on_background_changed)
        self.background_combo.config(state="disabled")

        background_frame.columnconfigure(2, weight=1)

        # 设置框架
        settings_frame = ttk.LabelFrame(main_frame, text="设置", padding="5")
        settings_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.auto_paste_var = tk.BooleanVar(value=self.core.config.AUTO_PASTE_IMAGE)
        ttk.Checkbutton(
            settings_frame,
            text="自动粘贴",
            variable=self.auto_paste_var,
            command=self.on_auto_paste_changed,
        ).grid(row=0, column=0, sticky=tk.W, padx=5)

        self.auto_send_var = tk.BooleanVar(value=self.core.config.AUTO_SEND_IMAGE)
        ttk.Checkbutton(
            settings_frame,
            text="自动发送",
            variable=self.auto_send_var,
            command=self.on_auto_send_changed,
        ).grid(row=0, column=1, sticky=tk.W, padx=5)

        # 预览框架
        preview_frame = ttk.LabelFrame(main_frame, text="图片预览", padding="5")
        preview_frame.grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5
        )

        # 预览信息区域（放在图片上方，横向排列三个信息项）
        preview_info_frame = ttk.Frame(preview_frame)
        preview_info_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        # 创建三个标签用于显示预览信息，横向排列
        self.preview_info_var1 = tk.StringVar(value="信息1")
        self.preview_info_var2 = tk.StringVar(value="信息2")
        self.preview_info_var3 = tk.StringVar(value="信息3")

        preview_info_label1 = ttk.Label(
            preview_info_frame, textvariable=self.preview_info_var1
        )
        preview_info_label1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # 添加分隔线
        separator1 = ttk.Separator(preview_info_frame, orient=tk.VERTICAL)
        separator1.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)

        preview_info_label2 = ttk.Label(
            preview_info_frame, textvariable=self.preview_info_var2
        )
        preview_info_label2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # 添加分隔线
        separator2 = ttk.Separator(preview_info_frame, orient=tk.VERTICAL)
        separator2.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)

        preview_info_label3 = ttk.Label(
            preview_info_frame, textvariable=self.preview_info_var3
        )
        preview_info_label3.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # 更新预览按钮 - 放在预览信息区域的右侧
        ttk.Button(
            preview_info_frame, text="刷新", command=self.update_preview, width=10
        ).pack(side=tk.RIGHT, padx=5)

        # 图片预览区域
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief=tk.SUNKEN
        )
        status_bar.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)

        self.update_preview()


    def setup_menu(self):
        """设置菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 工具栏菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具栏", menu=tools_menu)
        tools_menu.add_command(label="设置", command=self.open_settings)
        tools_menu.add_separator()
        tools_menu.add_command(label="退出", command=self.root.quit)

    def open_settings(self):
        """打开设置窗口"""
        SettingsWindow(self.root, self.core, self)

    def setup_hotkeys(self):
        """设置热键监听"""
        self.hotkey_listener_active = True
        self.hotkey_thread = threading.Thread(target=self.hotkey_listener, daemon=True)
        self.hotkey_thread.start()

    def hotkey_listener(self):
        """热键监听线程"""
        try:
            import keyboard

            while True:
                # 重新加载设置以获取最新配置
                try:
                    # 获取当前平台的热键
                    hotkeys = self.core.keymap
                    # 获取GUI设置
                    gui_settings = self.core.get_gui_settings()
                    quick_chars = gui_settings.get("quick_characters", {})
                except Exception as e:
                    print(f"加载热键设置失败: {e}")
                    time.sleep(1)
                    continue
                
                # 始终检查停止监听热键
                toggle_hotkey = hotkeys.get("toggle_listener", "alt+ctrl+p")
                if keyboard.is_pressed(toggle_hotkey):
                    self.root.after(0, self.toggle_hotkey_listener)
                    time.sleep(0.5)  # 防止重复触发
                    
                # 如果监听未激活，则跳过其他热键检查
                if not self.hotkey_listener_active:
                    time.sleep(0.05)
                    continue
                
                # 检查每个热键
                for action, hotkey in hotkeys.items():
                    # 只监听GUI相关的热键
                    if action in [
                        "start_generate",
                        "next_character",
                        "prev_character",
                        "next_background",
                        "prev_background",
                        "next_emotion",
                        "prev_emotion",
                        # "toggle_listener",
                    ] or action.startswith("character_"):
                        if keyboard.is_pressed(hotkey):
                            # 对于角色快捷键，传递角色ID
                            if action.startswith("character_"):
                                char_id = quick_chars.get(action, "")
                                self.root.after(
                                    0,
                                    lambda a=action, c=char_id: self.handle_hotkey_action(
                                        a, c
                                    ),
                                )
                            else:
                                self.root.after(
                                    0, lambda a=action: self.handle_hotkey_action(a)
                                )
                            # 防止重复触发
                            time.sleep(0.3)
                            break

                time.sleep(0.05)  # 降低CPU使用率

        except Exception as e:
            print(f"热键监听错误: {e}")
            time.sleep(1)  # 出错时等待1秒再重试

    def handle_hotkey_action(self, action, char_id=None):
        """处理热键动作"""
        try:
            if action == "start_generate":
                self.generate_image()  # 生成图片
            elif action == "next_character":
                self.switch_character(1)  # 向后切换
            elif action == "prev_character":
                self.switch_character(-1)  # 向前切换
            elif action == "next_emotion":  # 新增：向前切换表情
                self.switch_emotion(1)
            elif action == "prev_emotion":  # 新增：向后切换表情
                self.switch_emotion(-1)
            elif action == "next_background":
                self.switch_background(1)  # 向后切换背景
            elif action == "prev_background":
                self.switch_background(-1)  # 向前切换背景
            elif action == "toggle_listener":
                self.toggle_hotkey_listener()
            elif action.startswith("character_") and char_id:
                self.switch_to_character_by_id(char_id)

        except Exception as e:
            print(f"处理热键动作失败: {e}")

    def switch_emotion(self, direction):
        """切换表情"""
        if self.emotion_random_var.get():
            # 如果当前是随机模式，切换到指定模式
            self.emotion_random_var.set(False)
            self.on_emotion_random_changed()

        emotion_count = self.core.get_current_emotion_count()
        current_emotion = self.core.selected_emotion or 1

        new_emotion = current_emotion + direction
        if new_emotion > emotion_count:
            new_emotion = 1
        elif new_emotion < 1:
            new_emotion = emotion_count

        self.core.selected_emotion = new_emotion
        self.emotion_combo.set(f"表情 {new_emotion}")
        self.update_preview()
        self.update_status(f"已切换到表情: {new_emotion}")

    def switch_character(self, direction):
        """切换角色"""
        current_index = self.core.current_character_index
        total_chars = len(self.core.character_list)

        new_index = current_index + direction
        if new_index > total_chars:
            new_index = 1
        elif new_index < 1:
            new_index = total_chars

        if self.core.switch_character(new_index):
            # 切换角色后清理缓存
            self.core.image_processor.clear_cache()
            # 更新GUI显示
            self.character_var.set(
                f"{self.core.get_character(full_name=True)} ({self.core.get_character()})"
            )
            self.update_emotion_options()
            self.update_preview()
            self.update_status(
                f"已切换到角色: {self.core.get_character(full_name=True)}"
            )

    def switch_background(self, direction):
        """切换背景"""
        if self.background_random_var.get():
            # 如果当前是随机模式，切换到指定模式
            self.background_random_var.set(False)
            self.on_background_random_changed()

        current_bg = self.core.selected_background or 1
        total_bgs = self.core.image_processor.background_count

        new_bg = current_bg + direction
        if new_bg > total_bgs:
            new_bg = 1
        elif new_bg < 1:
            new_bg = total_bgs

        self.core.selected_background = new_bg
        self.background_combo.set(f"背景 {new_bg}")
        self.update_preview()
        self.update_status(f"已切换到背景: {new_bg}")

    def switch_to_character_by_id(self, char_id):
        """通过角色ID切换到指定角色"""
        if char_id and char_id in self.core.character_list:
            char_index = self.core.character_list.index(char_id) + 1
            if self.core.switch_character(char_index):
                self.character_var.set(
                    f"{self.core.get_character(full_name=True)} ({self.core.get_character()})"
                )
                self.update_emotion_options()
                self.update_preview()
                self.update_status(
                    f"已快速切换到角色: {self.core.get_character(full_name=True)}"
                )

    def toggle_hotkey_listener(self):
        """切换热键监听状态"""
        self.hotkey_listener_active = not self.hotkey_listener_active
        status = "启用" if self.hotkey_listener_active else "禁用"
        self.update_status(f"热键监听已{status}")

    def update_hotkeys(self):
        """更新热键设置（供SettingsWindow调用）"""
        # 热键会在监听线程中自动重新加载，这里只需要确保监听在运行
        if not self.hotkey_listener_active:
            self.hotkey_listener_active = True

    # 其余现有方法保持不变...
    def on_window_resize(self, event):
        """处理窗口大小变化事件 - 调整大小并刷新内容"""
        if event.widget == self.root:
            window_width = self.root.winfo_width()
            new_width = max(200, window_width - 40)
            new_height = int(new_width * 0.75)

            if (
                abs(new_width - self.preview_size[0]) > 30
                or abs(new_height - self.preview_size[1]) > 20
            ):
                self.preview_size = (new_width, new_height)
                # 更新预览内容
                self.update_preview()

    def update_preview(self):
        """更新预览"""
        try:
            preview_image, info = self.core.generate_preview(self.preview_size)

            # 保存原始图片用于大小调整
            # self.preview_image = preview_image

            # 转换为 PhotoImage
            self.preview_photo = ImageTk.PhotoImage(preview_image)
            self.preview_label.configure(image=self.preview_photo)

            # 更新预览信息 - 将信息拆分成三个部分横向显示
            info_parts = info.split("\n")
            if len(info_parts) >= 3:
                self.preview_info_var1.set(info_parts[0])
                self.preview_info_var2.set(info_parts[1])
                self.preview_info_var3.set(info_parts[2])

        except Exception as e:
            # 错误信息也分配到三个标签中
            error_msg = f"预览生成失败: {str(e)}"
            self.preview_info_var1.set(error_msg)
            self.preview_info_var2.set("")
            self.preview_info_var3.set("")

    def on_character_changed(self, event=None):
        """角色改变事件"""
        selected_text = self.character_var.get()
        char_id = selected_text.split("(")[-1].rstrip(")")

        # 更新核心角色
        char_idx = self.core.character_list.index(char_id) + 1
        self.core.switch_character(char_idx)

        # 更新表情选项
        self.update_emotion_options()

        # 重置表情选择为第一个表情
        self.emotion_combo.set("表情 1")
        self.core.selected_emotion = 1

        # 标记需要更新预览内容
        self.update_preview()
        self.update_status(f"已切换到角色: {self.core.get_character(full_name=True)}")

    def update_emotion_options(self):
        """更新表情选项"""
        emotion_count = self.core.get_current_emotion_count()
        self.emotion_combo["values"] = [
            f"表情 {i}" for i in range(1, emotion_count + 1)
        ]
        self.emotion_combo.set("表情 1")

    def on_emotion_random_changed(self):
        """表情随机选择改变"""
        if self.emotion_random_var.get():
            self.emotion_combo.config(state="disabled")
            self.core.selected_emotion = None
        else:
            self.emotion_combo.config(state="readonly")
            emotion_value = self.emotion_combo.get()
            if emotion_value:
                emotion_index = int(emotion_value.split()[-1])
                self.core.selected_emotion = emotion_index

        self.update_preview()

    def on_emotion_changed(self, event=None):
        """表情改变事件"""
        if not self.emotion_random_var.get():
            emotion_value = self.emotion_var.get()
            if emotion_value:
                emotion_index = int(emotion_value.split()[-1])
                self.core.selected_emotion = emotion_index
                self.update_preview()

    def on_background_random_changed(self):
        """背景随机选择改变"""
        if self.background_random_var.get():
            self.background_combo.config(state="disabled")
            self.core.selected_background = None
        else:
            self.background_combo.config(state="readonly")
            background_value = self.background_combo.get()
            if background_value:
                background_index = int(background_value.split()[-1])
                self.core.selected_background = background_index

        self.update_preview()

    def on_background_changed(self, event=None):
        """背景改变事件"""
        if not self.background_random_var.get():
            background_value = self.background_var.get()
            if background_value:
                background_index = int(background_value.split()[-1])
                self.core.selected_background = background_index
                self.update_preview()

    def on_auto_paste_changed(self):
        """自动粘贴设置改变"""
        self.core.config.AUTO_PASTE_IMAGE = self.auto_paste_var.get()

    def on_auto_send_changed(self):
        """自动发送设置改变"""
        self.core.config.AUTO_SEND_IMAGE = self.auto_send_var.get()

    def generate_image(self):
        """生成图片"""
        if self.is_generating:
            return
        
        # 设置生成状态
        self.is_generating = True
        self.status_var.set("正在生成图片...")

        def generate_in_thread():
            try:
                result = self.core.generate_image()
                self.root.after(0, lambda: self.on_generation_complete(result))
            except Exception as e:
                error_msg = f"生成失败: {str(e)}"
                print(error_msg)
                self.root.after(0, lambda: self.on_generation_complete(error_msg))
            finally:
                self.is_generating = False
        thread = threading.Thread(target=generate_in_thread, daemon=True)
        thread.start()

    def on_generation_complete(self, result):
        """生成完成后的回调函数"""
        self.status_var.set(result)
        self.update_preview()

    def update_status(self, message: str):
        """更新状态栏"""
        self.status_var.set(message)
        self.root.update_idletasks()

    def run(self):
        """运行 GUI"""
        self.root.mainloop()
