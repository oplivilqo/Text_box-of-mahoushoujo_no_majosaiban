"""设置窗口模块"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import yaml
import sys
from path_utils import get_available_fonts, get_resource_path


class SettingsWindow:
    """设置窗口"""

    def __init__(self, parent, core, gui):
        self.parent = parent
        self.core = core
        self.gui = gui

        # 加载设置
        self.settings = self.core.get_gui_settings()

        # 获取可用的AI模型配置
        self.ai_models = self.core.get_ai_models()
        
        # 确定当前平台
        self.platform = sys.platform
        if self.platform.startswith('win'):
            self.platform_key = 'win32'
        elif self.platform == 'darwin':
            self.platform_key = 'darwin'
        else:
            self.platform_key = 'win32'  # 默认

        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("设置")
        self.window.geometry("500x750")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        self.setup_ui()

        # 确保界面状态正确
        self.setup_model_parameters()

    def setup_ui(self):
        """设置UI界面"""
        # 创建Notebook用于标签页
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 常规设置标签页
        general_frame = ttk.Frame(notebook, padding="10")
        notebook.add(general_frame, text="常规设置")

        # 进程白名单标签页
        whitelist_frame = ttk.Frame(notebook, padding="10")
        notebook.add(whitelist_frame, text="进程白名单")

        # 快捷键设置标签页
        hotkey_frame = ttk.Frame(notebook, padding="10")
        notebook.add(hotkey_frame, text="快捷键设置")

        self.setup_general_tab(general_frame)
        self.setup_whitelist_tab(whitelist_frame)
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
        # 获取情感匹配设置
        sentiment_settings = self.settings.get("sentiment_matching", {})
        
        # 字体设置
        font_frame = ttk.LabelFrame(parent, text="字体设置", padding="10")
        font_frame.pack(fill=tk.X, pady=5)

        ttk.Label(font_frame, text="对话框字体:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # 获取可用字体列表
        available_fonts = self._get_available_fonts()
        
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

        # 文字颜色设置
        ttk.Label(font_frame, text="文字颜色:").grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        
        color_frame = ttk.Frame(font_frame)
        color_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.text_color_var = tk.StringVar(
            value=self.settings.get("text_color", "#FFFFFF")
        )
        color_entry = ttk.Entry(
            color_frame,
            textvariable=self.text_color_var,
            width=10
        )
        color_entry.pack(side=tk.LEFT, padx=(0, 5))
        color_entry.bind("<KeyRelease>", self.on_setting_changed)
        
        # 颜色预览标签
        self.color_preview_label = ttk.Label(
            color_frame,
            text="   ",
            background=self.text_color_var.get(),
            relief="solid",
            width=3
        )
        self.color_preview_label.pack(side=tk.LEFT)
        
        # # 绑定变量变化更新预览
        # self.text_color_var.trace_add("write", self.update_color_preview)
        
        # 绑定变量变化更新预览
        def on_color_change(*args):
                self.update_color_preview()
                self.on_setting_changed()
            
        self.text_color_var.trace_add("write", on_color_change)

                # 强调颜色设置
        ttk.Label(font_frame, text="强调颜色:").grid(
            row=4, column=0, sticky=tk.W, pady=5
        )
        
        bracket_color_frame = ttk.Frame(font_frame)
        bracket_color_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.bracket_color_var = tk.StringVar(
            value=self.settings.get("bracket_color", "#89B1FB")
        )
        bracket_color_entry = ttk.Entry(
            bracket_color_frame,
            textvariable=self.bracket_color_var,
            width=10
        )
        bracket_color_entry.pack(side=tk.LEFT, padx=(0, 5))
        bracket_color_entry.bind("<KeyRelease>", self.on_setting_changed)
        
        # 强调颜色预览标签
        self.bracket_color_preview_label = ttk.Label(
            bracket_color_frame,
            text="   ",
            background=self.bracket_color_var.get(),
            relief="solid",
            width=3
        )
        self.bracket_color_preview_label.pack(side=tk.LEFT)
        
        # 绑定变量变化更新预览
        def on_bracket_color_change(*args):
                self.update_bracket_color_preview()
                self.on_setting_changed()
            
        self.bracket_color_var.trace_add("write", on_bracket_color_change)
        
        # 强调颜色说明
        ttk.Label(font_frame, 
                text="注：该颜色控制括号内容的颜色", 
                font=("", 8), foreground="gray").grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=2
        )


        # 情感匹配设置
        sentiment_frame = ttk.LabelFrame(parent, text="情感匹配设置", padding="10")
        sentiment_frame.pack(fill=tk.X, pady=5)

        # 启用情感匹配
        self.sentiment_enabled_var = tk.BooleanVar(
            value=sentiment_settings.get("enabled", False)
        )

        # AI模型选择
        ttk.Label(sentiment_frame, text="AI模型:").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        
        # 动态获取模型列表
        model_names = list(self.ai_models.keys())
        self.ai_model_var = tk.StringVar(
            value=sentiment_settings.get("ai_model", model_names[0] if model_names else "ollama")
        )
        ai_model_combo = ttk.Combobox(
            sentiment_frame,
            textvariable=self.ai_model_var,
            values=model_names,
            state="readonly",
            width=15
        )
        ai_model_combo.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        ai_model_combo.bind("<<ComboboxSelected>>", self.setup_model_parameters)

        # 连接测试按钮
        self.test_btn = ttk.Button(
            sentiment_frame,
            text="测试连接",
            command=self.test_ai_connection,
            width=10
        )
        self.test_btn.grid(row=1, column=2, sticky=tk.W, pady=5, padx=5)

        # 模型参数框架 - 显示所有参数
        self.params_frame = ttk.Frame(sentiment_frame)
        self.params_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # 初始化参数显示
        self.setup_model_parameters()

        # 情感匹配说明
        ttk.Label(sentiment_frame, 
                text="注：在主界面点击情感匹配以进行连接，点击测试连接按钮也行", 
                font=("", 8), foreground="gray").grid(
            row=0, column=0, columnspan=3, sticky=tk.W, pady=2
        )

        sentiment_frame.columnconfigure(1, weight=1)

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
        
        # 从配置文件重新加载快捷键
        self.original_hotkeys = self.core.config_loader.load_keymap(self.platform_key)
        hotkeys = self.original_hotkeys
        
        # 生成快捷键放在第一个
        generate_frame = ttk.LabelFrame(scrollable_frame, text="生成控制", padding="10")
        generate_frame.pack(fill=tk.X, pady=5)

        self.create_hotkey_editable_row(
            generate_frame,
            "生成图片",
            "start_generate",
            hotkeys.get("start_generate", "ctrl+e"),
            0,
        )

        # 角色切换快捷键
        char_frame = ttk.LabelFrame(scrollable_frame, text="角色切换", padding="10")
        char_frame.pack(fill=tk.X, pady=5)

        self.create_hotkey_editable_row(
            char_frame,
            "向前切换角色",
            "next_character",
            hotkeys.get("next_character", "ctrl+j"),
            0,
        )
        self.create_hotkey_editable_row(
            char_frame,
            "向后切换角色",
            "prev_character",
            hotkeys.get("prev_character", "ctrl+l"),
            1,
        )

        # 表情切换快捷键 - 新增
        emotion_frame = ttk.LabelFrame(scrollable_frame, text="表情切换", padding="10")
        emotion_frame.pack(fill=tk.X, pady=5)

        self.create_hotkey_editable_row(
            emotion_frame,
            "向前切换表情",
            "next_emotion",
            hotkeys.get("next_emotion", "ctrl+u"),
            0,
        )
        self.create_hotkey_editable_row(
            emotion_frame,
            "向后切换表情",
            "prev_emotion",
            hotkeys.get("prev_emotion", "ctrl+o"),
            1,
        )

        # 背景切换快捷键
        bg_frame = ttk.LabelFrame(scrollable_frame, text="背景切换", padding="10")
        bg_frame.pack(fill=tk.X, pady=5)

        self.create_hotkey_editable_row(
            bg_frame,
            "向前切换背景",
            "next_background",
            hotkeys.get("next_background", "ctrl+i"),
            0,
        )
        self.create_hotkey_editable_row(
            bg_frame,
            "向后切换背景",
            "prev_background",
            hotkeys.get("prev_background", "ctrl+k"),
            1,
        )

        # 控制快捷键
        control_frame = ttk.LabelFrame(scrollable_frame, text="控制", padding="10")
        control_frame.pack(fill=tk.X, pady=5)

        self.create_hotkey_editable_row(
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

    def create_hotkey_editable_row(self, parent, label, key, hotkey_value, row):
        """创建可编辑的快捷键显示行"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)

        # 快捷键显示（可编辑）
        hotkey_var = tk.StringVar(value=hotkey_value)
        setattr(self, f"{key}_hotkey_var", hotkey_var)

        entry = ttk.Entry(parent, textvariable=hotkey_var, width=20)
        entry.grid(row=row, column=1, padx=5, pady=2, sticky=tk.W)

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

    def setup_whitelist_tab(self, parent):
        """设置进程白名单标签页"""
        # 创建滚动文本框
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)

        # 添加说明
        ttk.Label(frame, text="每行一个进程名，不包含.exe后缀").pack(anchor=tk.W, pady=5)

        # 文本框
        self.whitelist_text = tk.Text(frame, wrap=tk.WORD, width=50, height=20)
        self.whitelist_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # 从配置文件重新加载白名单内容
        current_whitelist = self.core.config_loader.load_process_whitelist()
        self.whitelist_text.insert('1.0', '\n'.join(current_whitelist))

    def setup_model_parameters(self, event=None):
        """设置模型参数显示"""
        # 清除现有参数控件
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        
        selected_model = self.ai_model_var.get()
        if selected_model not in self.ai_models:
            return
            
        model_config = self.ai_models[selected_model]
        sentiment_settings = self.settings.get("sentiment_matching", {})
        model_settings = sentiment_settings.get("model_configs", {}).get(selected_model, {})
        
        # 创建参数输入控件
        row = 0
        
        # API URL
        ttk.Label(self.params_frame, text="API地址:").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        self.api_url_var = tk.StringVar(
            value=model_settings.get("base_url", model_config.get("base_url", ""))
        )
        api_url_entry = ttk.Entry(
            self.params_frame,
            textvariable=self.api_url_var,
            width=40
        )
        api_url_entry.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2, padx=5)
        api_url_entry.bind("<KeyRelease>", self.on_setting_changed)
        row += 1
        
        # API Key
        ttk.Label(self.params_frame, text="API密钥:").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        self.api_key_var = tk.StringVar(
            value=model_settings.get("api_key", model_config.get("api_key", ""))
        )
        api_key_entry = ttk.Entry(
            self.params_frame,
            textvariable=self.api_key_var,
            width=40,
            show="*"
        )
        api_key_entry.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2, padx=5)
        api_key_entry.bind("<KeyRelease>", self.on_setting_changed)
        row += 1
        
        # 模型名称
        ttk.Label(self.params_frame, text="模型名称:").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        self.model_name_var = tk.StringVar(
            value=model_settings.get("model", model_config.get("model", ""))
        )
        model_name_entry = ttk.Entry(
            self.params_frame,
            textvariable=self.model_name_var,
            width=40
        )
        model_name_entry.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2, padx=5)
        model_name_entry.bind("<KeyRelease>", self.on_setting_changed)
        row += 1
        
        # 模型描述
        description = model_config.get("description", "")
        if description:
            ttk.Label(self.params_frame, text="描述:", font=("", 8)).grid(
                row=row, column=0, sticky=tk.W, pady=2
            )
            ttk.Label(self.params_frame, text=description, font=("", 8), foreground="gray").grid(
                row=row, column=1, columnspan=2, sticky=tk.W, pady=2, padx=5
            )
        
        self.params_frame.columnconfigure(1, weight=1)

    def test_ai_connection(self):
        """测试AI连接 - 这会触发模型初始化"""
        selected_model = self.ai_model_var.get()
        if selected_model not in self.ai_models:
            return
            
        # 获取当前配置
        config = {
            "base_url": self.api_url_var.get(),
            "api_key": self.api_key_var.get(),
            "model": self.model_name_var.get()
        }
        
        # 禁用按钮
        self.test_btn.config(state="disabled")
        self.test_btn.config(text="测试中...")
        
        def test_in_thread():
            success = self.core.test_ai_connection(selected_model, config)
            self.window.after(0, lambda: self.on_connection_test_complete(success))
        
        threading.Thread(target=test_in_thread, daemon=True).start()

    def on_connection_test_complete(self, success: bool):
        """连接测试完成回调"""
        self.test_btn.config(state="normal")
        if success:
            self.test_btn.config(text="连接成功")
            # 测试成功时，更新当前配置
            selected_model = self.ai_model_var.get()
            if "model_configs" not in self.settings["sentiment_matching"]:
                self.settings["sentiment_matching"]["model_configs"] = {}
            self.settings["sentiment_matching"]["model_configs"][selected_model] = {
                "base_url": self.api_url_var.get(),
                "api_key": self.api_key_var.get(),
                "model": self.model_name_var.get()
            }
            # 2秒后恢复文本
            self.window.after(2000, lambda: self.test_btn.config(text="测试连接"))
        else:
            self.test_btn.config(text="连接失败")
            # 连接失败时，禁用情感匹配
            self.sentiment_enabled_var.set(False)
            self.on_setting_changed()
            # 2秒后恢复文本
            self.window.after(2000, lambda: self.test_btn.config(text="测试连接"))

    def update_pixel_label(self, *args):
        """更新像素减少比例标签"""
        self.pixel_value_label.config(text=f"{self.pixel_reduction_ratio_var.get()}%")
        self.on_setting_changed()

    def _get_available_fonts(self):
        """获取可用字体列表，优先显示项目字体"""
        font_files = get_available_fonts()
        project_fonts = []

        # 直接从路径中提取字体文件名（不含扩展名）
        for font_path in font_files:
            if font_path:
                # 获取文件名（不含路径和扩展名）
                font_name = os.path.splitext(os.path.basename(font_path))[0]
                project_fonts.append(font_name)
        return project_fonts

    def on_setting_changed(self, event=None):
        """设置改变时的回调"""
        # 更新设置字典
        self.settings["font_family"] = self.font_family_var.get()
        self.settings["font_size"] = self.font_size_var.get()

        # 只在颜色有效时更新设置中的颜色值
        color_value = self.text_color_var.get()
        if self.validate_color_format(color_value):
            # 更新颜色预览
            self.color_preview_label.configure(background=color_value)
            # 更新设置字典中的颜色值
            self.settings["text_color"] = color_value
        else:
            # 颜色无效时，不更新设置字典，保持之前的有效值
            pass
        
        # 更新强调颜色设置
        bracket_color_value = self.bracket_color_var.get()
        if self.validate_color_format(bracket_color_value):
            # 更新强调颜色预览
            self.bracket_color_preview_label.configure(background=bracket_color_value)
            # 更新设置字典中的强调颜色值
            self.settings["bracket_color"] = bracket_color_value
        else:
            # 颜色无效时，不更新设置字典，保持之前的有效值
            pass

        # 更新情感匹配设置
        if "sentiment_matching" not in self.settings:
            self.settings["sentiment_matching"] = {}
        
        self.settings["sentiment_matching"]["enabled"] = self.sentiment_enabled_var.get()
        self.settings["sentiment_matching"]["ai_model"] = self.ai_model_var.get()
        
        # 保存模型配置
        if "model_configs" not in self.settings["sentiment_matching"]:
            self.settings["sentiment_matching"]["model_configs"] = {}
            
        selected_model = self.ai_model_var.get()
        self.settings["sentiment_matching"]["model_configs"][selected_model] = {
            "base_url": self.api_url_var.get(),
            "api_key": self.api_key_var.get(),
            "model": self.model_name_var.get()
        }
            
        # 更新图像压缩设置
        if "image_compression" not in self.settings:
            self.settings["image_compression"] = {}
        
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

    def on_save(self):
        """保存设置并关闭窗口"""
        if self.on_apply():
            self.window.destroy()

    def on_apply(self):
        """应用设置但不关闭窗口"""
        # 验证颜色值
        if not self.validate_color_format(self.text_color_var.get()):
            messagebox.showerror("颜色错误", "颜色格式无效，请输入有效的十六进制颜色值（例如：#FFFFFF）")
            return False
        
        self.on_setting_changed()

        # 检查快捷键是否有更改并保存
        if self._check_hotkeys_changed():
            if not self.save_hotkey_settings():
                return False
            # 只在快捷键有更改时重新初始化热键管理器
            self.core.reload_configs()
            self.gui.reinitialize_hotkeys()
            self.hotkeys_changed = False

        # 保存设置到文件
        self.core.save_gui_settings(self.settings)
        # 保存进程白名单
        self.save_whitelist_settings()

        # 应用设置时检查是否需要重新初始化AI模型
        self.core._reinitialize_sentiment_analyzer_if_needed()
        return True

    def save_hotkey_settings(self):
        """保存快捷键设置"""
        # 检查快捷键有效性
        if not self._validate_hotkeys():
            return False  # 如果快捷键无效，返回False

        # 加载现有的keymap配置
        keymap_file = get_resource_path(os.path.join("config", "keymap.yml"))
        if os.path.exists(keymap_file):
            with open(keymap_file, 'r', encoding='utf-8') as f:
                keymap_data = yaml.safe_load(f) or {}
        else:
            keymap_data = {}

        # 确保当前平台配置存在
        if self.platform_key not in keymap_data:
            keymap_data[self.platform_key] = {}

        # 更新当前平台的快捷键
        for key in ['start_generate', 'next_character', 'prev_character', 'next_emotion', 'prev_emotion', 
                   'next_background', 'prev_background', 'toggle_listener']:
            var_name = f"{key}_hotkey_var"
            if hasattr(self, var_name):
                hotkey_var = getattr(self, var_name)
                keymap_data[self.platform_key][key] = hotkey_var.get()

        # 保存回文件
        try:
            os.makedirs(os.path.dirname(keymap_file), exist_ok=True)
            with open(keymap_file, 'w', encoding='utf-8') as f:
                yaml.dump(keymap_data, f, allow_unicode=True, default_flow_style=False)
            
            # 更新原始快捷键以反映保存状态
            self.original_hotkeys = keymap_data[self.platform_key]
            return True
        except Exception as e:
            print(f"保存快捷键设置失败: {e}")
            return False
    
    def _validate_hotkeys(self):
        """验证快捷键输入的有效性"""
        valid_modifiers = ['ctrl', 'alt', 'shift', 'win']
        valid_keys = [
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
            'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
            'space', 'tab', 'enter', 'esc', 'backspace', 'delete', 'insert', 'home', 'end',
            'pageup', 'pagedown', 'up', 'down', 'left', 'right'
        ]
        
        # 获取所有快捷键变量
        hotkey_vars = []
        for key in ['start_generate', 'next_character', 'prev_character', 'next_emotion', 'prev_emotion', 
                'next_background', 'prev_background', 'toggle_listener']:
            var_name = f"{key}_hotkey_var"
            if hasattr(self, var_name):
                hotkey_vars.append((key, getattr(self, var_name)))
        
        # 检查每个快捷键
        for key_name, hotkey_var in hotkey_vars:
            hotkey = hotkey_var.get().strip().lower()
            if not hotkey:
                continue  # 空快捷键跳过检查
                
            # 检查格式：modifier+key 或 modifier+modifier+key
            parts = hotkey.split('+')
            if len(parts) < 2 or len(parts) > 3:
                self._show_hotkey_error(f"快捷键 '{hotkey}' 格式无效，应为：修饰键+按键")
                return False
            
            # 检查修饰键
            for modifier in parts[:-1]:
                if modifier not in valid_modifiers:
                    self._show_hotkey_error(f"快捷键 '{hotkey}' 包含无效修饰键 '{modifier}'")
                    return False
            
            # 检查主按键
            main_key = parts[-1]
            if main_key not in valid_keys:
                self._show_hotkey_error(f"快捷键 '{hotkey}' 包含无效按键 '{main_key}'")
                return False
        
        return True

    def _show_hotkey_error(self, message):
        """显示快捷键错误消息"""
        messagebox.showerror("快捷键错误", message)
        
    def save_whitelist_settings(self):
        """保存进程白名单设置"""
        # 从文本框获取内容
        text_content = self.whitelist_text.get('1.0', tk.END).strip()
        processes = [p.strip() for p in text_content.split('\n') if p.strip()]

        # 使用config_loader保存白名单
        success = self.core.config_loader.save_process_whitelist(processes)

        if success:
            # 更新core中的白名单
            self.core.process_whitelist = processes
            return True
        else:
            return False

    def _check_hotkeys_changed(self):
        """检查快捷键是否有更改"""
        # 获取当前快捷键设置

        for key in ['start_generate', 'next_character', 'prev_character', 'next_emotion', 'prev_emotion', 
                   'next_background', 'prev_background', 'toggle_listener']:
            var_name = f"{key}_hotkey_var"
            if hasattr(self, var_name):
                if  getattr(self, var_name).get() != self.original_hotkeys[key]:
                    return True

        return False

    def update_color_preview(self, *args):
        """更新颜色预览标签"""
        color_value = self.text_color_var.get()
        # 验证颜色格式
        if self.validate_color_format(color_value):
            # 更新预览标签背景色
            self.color_preview_label.configure(background=color_value)
        else:
            # 如果颜色格式无效，显示默认颜色（保持原样，不更新）
            pass  # 不更新预览，保持之前的状态
    
    def update_bracket_color_preview(self, *args):
        """更新强调颜色预览标签"""
        color_value = self.bracket_color_var.get()
        # 验证颜色格式
        if self.validate_color_format(color_value):
            # 更新预览标签背景色
            self.bracket_color_preview_label.configure(background=color_value)
        else:
            # 如果颜色格式无效，显示默认颜色（保持原样，不更新）
            pass  # 不更新预览，保持之前的状态

    def validate_color_format(self, color_value):
        """验证颜色格式是否为有效的十六进制颜色"""
        import re
        # 匹配 #FFFFFF 格式
        pattern = r'^#([A-Fa-f0-9]{6})$'
        return re.match(pattern, color_value) is not None