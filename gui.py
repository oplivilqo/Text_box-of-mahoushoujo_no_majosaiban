"""魔裁文本框 GUI 版本"""
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading

from core import ManosabaCore


class ManosabaGUI:
    """魔裁文本框 GUI"""
    
    def __init__(self):
        self.core = ManosabaCore()
        self.root = tk.Tk()
        self.root.title("魔裁文本框生成器")
        self.root.geometry("800x700")
        
        # 预览相关
        # self.preview_image = None
        # self.preview_photo = None
        self.preview_size = (700, 525)
        # self.preview_needs_update = True  # 标记预览是否需要更新内容
        
        self.setup_gui()
        self.root.bind('<Configure>', self.on_window_resize)
        
        # 延迟初始预览，确保窗口已经显示
        # self.root.after(100, self.initial_preview)
        # 确保初始状态正确
        self.update_status("就绪 - 等待生成预览")

        self.setup_hotkeys()
    
    def setup_hotkeys(self):
        """设置热键"""
        def start_hotkey_listener():
            try:
                import keyboard
                hotkey = self.core.keymap.get('start_generate', 'ctrl+alt+g')
                keyboard.add_hotkey(hotkey, self.on_hotkey_triggered)
                print(f"热键已设置: {hotkey}")
            except Exception as e:
                print(f"热键设置失败: {e}")
        
        hotkey_thread = threading.Thread(target=start_hotkey_listener, daemon=True)
        hotkey_thread.start()
    
    def on_hotkey_triggered(self):
        """热键触发时的回调"""
        # 使用 after 确保在主线程中执行
        self.root.after(0, self.generate_image)

    def initial_preview(self):
        """初始预览生成"""
        # self.preview_needs_update = True
        self.update_preview()
    
    def setup_gui(self):
        """设置 GUI 界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 角色选择
        ttk.Label(main_frame, text="选择角色:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.character_var = tk.StringVar()
        character_combo = ttk.Combobox(main_frame, textvariable=self.character_var, state="readonly", width=30)
        character_combo['values'] = [f"{self.core.get_character(char_id, full_name=True)} ({char_id})" 
                                   for char_id in self.core.character_list]
        character_combo.set(f"{self.core.get_character(full_name=True)} ({self.core.get_character()})")
        character_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        character_combo.bind('<<ComboboxSelected>>', self.on_character_changed)
        
        # 表情选择框架
        emotion_frame = ttk.LabelFrame(main_frame, text="表情选择", padding="5")
        emotion_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 表情随机选择
        self.emotion_random_var = tk.BooleanVar(value=True)
        emotion_random_cb = ttk.Checkbutton(emotion_frame, text="随机表情", 
                                           variable=self.emotion_random_var,
                                           command=self.on_emotion_random_changed)
        emotion_random_cb.grid(row=0, column=0, sticky=tk.W, padx=5)
        
        # 表情下拉框
        ttk.Label(emotion_frame, text="指定表情:").grid(row=0, column=1, sticky=tk.W, padx=5)
        self.emotion_var = tk.StringVar()
        self.emotion_combo = ttk.Combobox(emotion_frame, textvariable=self.emotion_var, 
                                         state="readonly", width=15)
        emotion_count = self.core.get_current_emotion_count()
        self.emotion_combo['values'] = [f"表情 {i}" for i in range(1, emotion_count + 1)]
        self.emotion_combo.set("表情 1")
        self.emotion_combo.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=5)
        self.emotion_combo.bind('<<ComboboxSelected>>', self.on_emotion_changed)
        self.emotion_combo.config(state="disabled")
        
        emotion_frame.columnconfigure(2, weight=1)
        
        # 背景选择框架
        background_frame = ttk.LabelFrame(main_frame, text="背景选择", padding="5")
        background_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 背景随机选择
        self.background_random_var = tk.BooleanVar(value=True)
        background_random_cb = ttk.Checkbutton(background_frame, text="随机背景", 
                                              variable=self.background_random_var,
                                              command=self.on_background_random_changed)
        background_random_cb.grid(row=0, column=0, sticky=tk.W, padx=5)
        
        # 背景下拉框
        ttk.Label(background_frame, text="指定背景:").grid(row=0, column=1, sticky=tk.W, padx=5)
        self.background_var = tk.StringVar()
        self.background_combo = ttk.Combobox(background_frame, textvariable=self.background_var, 
                                            state="readonly", width=15)
        background_count = self.core.image_processor.background_count
        self.background_combo['values'] = [f"背景 {i}" for i in range(1, background_count + 1)]
        self.background_combo.set("背景 1")
        self.background_combo.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=5)
        self.background_combo.bind('<<ComboboxSelected>>', self.on_background_changed)
        self.background_combo.config(state="disabled")
        
        background_frame.columnconfigure(2, weight=1)
        
        # 设置框架
        settings_frame = ttk.LabelFrame(main_frame, text="设置", padding="5")
        settings_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.auto_paste_var = tk.BooleanVar(value=self.core.config.AUTO_PASTE_IMAGE)
        ttk.Checkbutton(settings_frame, text="自动粘贴", variable=self.auto_paste_var,
                       command=self.on_auto_paste_changed).grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.auto_send_var = tk.BooleanVar(value=self.core.config.AUTO_SEND_IMAGE)
        ttk.Checkbutton(settings_frame, text="自动发送", variable=self.auto_send_var,
                       command=self.on_auto_send_changed).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 预览框架
        preview_frame = ttk.LabelFrame(main_frame, text="图片预览", padding="5")
        preview_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # 预览信息区域（放在图片上方，横向排列三个信息项）
        preview_info_frame = ttk.Frame(preview_frame)
        preview_info_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        # 创建三个标签用于显示预览信息，横向排列
        self.preview_info_var1 = tk.StringVar(value="信息1")
        self.preview_info_var2 = tk.StringVar(value="信息2")
        self.preview_info_var3 = tk.StringVar(value="信息3")

        preview_info_label1 = ttk.Label(preview_info_frame, textvariable=self.preview_info_var1)
        preview_info_label1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # 添加分隔线
        separator1 = ttk.Separator(preview_info_frame, orient=tk.VERTICAL)
        separator1.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)

        preview_info_label2 = ttk.Label(preview_info_frame, textvariable=self.preview_info_var2)
        preview_info_label2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # 添加分隔线
        separator2 = ttk.Separator(preview_info_frame, orient=tk.VERTICAL)
        separator2.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)

        preview_info_label3 = ttk.Label(preview_info_frame, textvariable=self.preview_info_var3)
        preview_info_label3.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

         # 更新预览按钮 - 放在预览信息区域的右侧
        ttk.Button(preview_info_frame, text="刷新", command=self.update_preview, width=10).pack(side=tk.RIGHT, padx=5)

        # 图片预览区域
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        # ttk.Button(button_frame, text="生成图片", command=self.generate_image).pack(side=tk.LEFT, padx=5)
        # ttk.Button(button_frame, text="清除缓存", command=self.delete_cache).pack(side=tk.LEFT, padx=5)
        # ttk.Button(button_frame, text="更新预览", command=self.update_preview).pack(side=tk.LEFT, padx=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)

        self.update_preview()
    
    def on_window_resize(self, event):
        """处理窗口大小变化事件 - 调整大小并刷新内容"""
        if event.widget == self.root:
            window_width = self.root.winfo_width()
            new_width = max(200, window_width - 40)
            new_height = int(new_width * 0.75)
            
            if abs(new_width - self.preview_size[0]) > 30 or abs(new_height - self.preview_size[1]) > 20:
                self.preview_size = (new_width, new_height)
                # 标记需要更新预览内容，并立即更新
                # self.preview_needs_update = True
                self.update_preview()
    
    def adjust_preview_size(self):
        """只调整预览图大小，不重新生成内容"""
        if self.preview_photo and self.preview_image:
            # 调整现有图片大小
            resized_image = self.preview_image.resize(self.preview_size, Image.Resampling.LANCZOS)
            self.preview_photo = ImageTk.PhotoImage(resized_image)
            self.preview_label.configure(image=self.preview_photo)
    
    # def force_update_preview(self):
    #     """强制更新预览内容"""
    #     self.preview_needs_update = True
    #     self.update_preview()
    
    def update_preview(self):
        """更新预览"""
        try:
            preview_image, info = self.core.generate_preview(self.preview_size)
            
            # 保存原始图片用于大小调整
            self.preview_image = preview_image
            
            # 转换为 PhotoImage
            self.preview_photo = ImageTk.PhotoImage(preview_image)
            self.preview_label.configure(image=self.preview_photo)
            
            # 更新预览信息 - 将信息拆分成三个部分横向显示
            info_parts = info.split('\n')
            if len(info_parts) >= 3:
                self.preview_info_var1.set(info_parts[0])
                self.preview_info_var2.set(info_parts[1])
                self.preview_info_var3.set(info_parts[2])
            else:
                # 如果信息不是三部分，则按需分配
                for i, part in enumerate(info_parts):
                    if i == 0:
                        self.preview_info_var1.set(part)
                    elif i == 1:
                        self.preview_info_var2.set(part)
                    elif i == 2:
                        self.preview_info_var3.set(part)
                # 设置剩余的部分为空
                for i in range(len(info_parts), 3):
                    if i == 0:
                        self.preview_info_var1.set("")
                    elif i == 1:
                        self.preview_info_var2.set("")
                    elif i == 2:
                        self.preview_info_var3.set("")
            
        except Exception as e:
            # 错误信息也分配到三个标签中
            error_msg = f"预览生成失败: {str(e)}"
            self.preview_info_var1.set(error_msg)
            self.preview_info_var2.set("")
            self.preview_info_var3.set("")
    
    def on_character_changed(self, event=None):
        """角色改变事件"""
        selected_text = self.character_var.get()
        char_id = selected_text.split('(')[-1].rstrip(')')
        
        # 更新核心角色
        char_idx = self.core.character_list.index(char_id) + 1
        self.core.switch_character(char_idx)
        
        # 更新表情选项
        self.update_emotion_options()
        
        # 标记需要更新预览内容
        # self.preview_needs_update = True
        self.update_preview()
        self.update_status(f"已切换到角色: {self.core.get_character(full_name=True)}")
    
    def update_emotion_options(self):
        """更新表情选项"""
        emotion_count = self.core.get_current_emotion_count()
        self.emotion_combo['values'] = [f"表情 {i}" for i in range(1, emotion_count + 1)]
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
        
        # self.preview_needs_update = True
        self.update_preview()
    
    def on_emotion_changed(self, event=None):
        """表情改变事件"""
        if not self.emotion_random_var.get():
            emotion_value = self.emotion_var.get()
            if emotion_value:
                emotion_index = int(emotion_value.split()[-1])
                self.core.selected_emotion = emotion_index
                # self.preview_needs_update = True
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
        
        # self.preview_needs_update = True
        self.update_preview()
    
    def on_background_changed(self, event=None):
        """背景改变事件"""
        if not self.background_random_var.get():
            background_value = self.background_var.get()
            if background_value:
                background_index = int(background_value.split()[-1])
                self.core.selected_background = background_index
                # self.preview_needs_update = True
                self.update_preview()
    
    def on_auto_paste_changed(self):
        """自动粘贴设置改变"""
        self.core.config.AUTO_PASTE_IMAGE = self.auto_paste_var.get()
    
    def on_auto_send_changed(self):
        """自动发送设置改变"""
        self.core.config.AUTO_SEND_IMAGE = self.auto_send_var.get()
    
    def generate_image(self):
        """生成图片 - 线程安全版本"""
        # 立即更新状态，让用户知道操作已开始
        self.status_var.set("正在生成图片...")
        self.root.update_idletasks()  # 强制立即更新界面
        
        def generate_in_thread():
            try:
                result = self.core.generate_image()
                # 使用 after 方法在主线程中更新 UI
                self.root.after(0, lambda: self.on_generation_complete(result))
            except Exception as e:
                error_msg = f"生成失败: {str(e)}"
                print(error_msg)  # 调试信息
                self.root.after(0, lambda: self.on_generation_complete(error_msg))
        
        # 启动生成线程
        thread = threading.Thread(target=generate_in_thread, daemon=True)
        thread.start()

    def on_generation_complete(self, result):
        """生成完成后的回调函数"""
        self.status_var.set(result)
        
        # 强制刷新界面
        self.root.update_idletasks()
        
        # 标记需要更新预览
        # self.preview_needs_update = True
        self.update_preview()
        
        # 再次强制刷新，确保预览也更新
        self.root.update_idletasks()
    
    def delete_cache(self):
        """清除缓存"""
        self.core.delete_cache()
        self.update_status("缓存已清除")
    
    def update_status(self, message: str):
        """更新状态栏"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def run(self):
        """运行 GUI"""
        self.root.mainloop()