"""魔裁文本框 GUI 版本"""
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
from sys import platform

from manosaba_core import ManosabaCore


class ManosabaGUI:
    """魔裁文本框 GUI"""
    
    def __init__(self):
        self.core = ManosabaCore()
        self.root = tk.Tk()
        self.root.title("魔裁文本框生成器")
        self.root.geometry("800x700")
        
        # 预览相关
        self.preview_image = None
        self.preview_photo = None
        self.preview_size = (700, 525)  # 默认预览大小，接近窗口宽度
        
        # 热键监听
        self.hotkey_listener = None
        
        self.setup_gui()
        self.setup_hotkeys()
        self.root.bind('<Configure>', self.on_window_resize)
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
        self.emotion_combo.config(state="disabled")  # 初始状态为禁用
        
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
        self.background_combo.config(state="disabled")  # 初始状态为禁用
        
        background_frame.columnconfigure(2, weight=1)
        
        # 设置框架
        settings_frame = ttk.LabelFrame(main_frame, text="设置", padding="5")
        settings_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.auto_paste_var = tk.BooleanVar(value=self.core.AUTO_PASTE_IMAGE)
        ttk.Checkbutton(settings_frame, text="自动粘贴", variable=self.auto_paste_var,
                       command=self.on_auto_paste_changed).grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.auto_send_var = tk.BooleanVar(value=self.core.AUTO_SEND_IMAGE)
        ttk.Checkbutton(settings_frame, text="自动发送", variable=self.auto_send_var,
                       command=self.on_auto_send_changed).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        self.pre_compose_var = tk.BooleanVar(value=self.core.PRE_COMPOSE_IMAGES)
        ttk.Checkbutton(settings_frame, text="预合成图片", variable=self.pre_compose_var,
                       command=self.on_pre_compose_changed).grid(row=0, column=2, sticky=tk.W, padx=5)
        
        # 预览框架 - 改为上下布局
        preview_frame = ttk.LabelFrame(main_frame, text="预览", padding="5")
        preview_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 预览图片在上 - 使用可调整大小的Frame来容纳预览图
        preview_image_frame = ttk.Frame(preview_frame)
        preview_image_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.preview_label = ttk.Label(preview_image_frame)
        self.preview_label.pack(expand=True, fill=tk.BOTH)
        
        # 预览信息在下 - 使用Label而不是Text，节省空间
        self.preview_info_var = tk.StringVar(value="预览信息将显示在这里")
        preview_info_label = ttk.Label(preview_frame, textvariable=self.preview_info_var, 
                                      wraplength=400, justify=tk.LEFT)
        preview_info_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="生成图片", command=self.generate_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除缓存", command=self.delete_cache).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="更新预览", command=self.update_preview).pack(side=tk.LEFT, padx=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
    
    # 修改：窗口大小变化处理函数，让预览图宽度基本与窗口宽度一致
    def on_window_resize(self, event):
        """处理窗口大小变化事件"""
        # 只响应主窗口的大小变化，避免子组件触发事件
        if event.widget == self.root:
            # 获取窗口当前宽度
            window_width = self.root.winfo_width()
            
            # 计算新的预览图尺寸，让宽度基本与窗口宽度一致
            # 减去一些边距（左右各20像素）
            new_width = max(200, window_width - 40)
            # 保持3:4的比例（宽:高），这是常见的图片比例
            new_height = int(new_width * 0.75)
            
            # 只有当尺寸发生显著变化时才更新预览，避免频繁更新
            if abs(new_width - self.preview_size[0]) > 30 or abs(new_height - self.preview_size[1]) > 20:
                self.preview_size = (new_width, new_height)
                self.update_preview()
    
    def setup_hotkeys(self):
        """设置全局热键"""
        if platform.startswith('win'):
            try:
                import keyboard
                hotkey = self.core.keymap.get('start_generate', 'ctrl+alt+g')
                keyboard.add_hotkey(hotkey, self.generate_image)
            except ImportError:
                print("键盘模块不可用，热键功能禁用")
    
    def on_character_changed(self, event=None):
        """角色改变事件"""
        selected_text = self.character_var.get()
        char_id = selected_text.split('(')[-1].rstrip(')')
        
        # 更新核心角色
        char_idx = self.core.character_list.index(char_id) + 1
        self.core.switch_character(char_idx)
        
        # 更新表情选项
        self.update_emotion_options()
        
        # 如果启用了预合成，开始预合成
        if self.core.PRE_COMPOSE_IMAGES:
            self.start_pre_compose()
        
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
            # 启用随机，禁用下拉框
            self.emotion_combo.config(state="disabled")
            self.core.selected_emotion = None
        else:
            # 禁用随机，启用下拉框
            self.emotion_combo.config(state="readonly")
            # 设置默认表情
            emotion_value = self.emotion_combo.get()
            if emotion_value:
                emotion_index = int(emotion_value.split()[-1])
                self.core.selected_emotion = emotion_index
        
        self.update_preview()
    
    def on_emotion_changed(self, event=None):
        """表情改变事件"""
        if not self.emotion_random_var.get():  # 只有在非随机模式下才处理
            emotion_value = self.emotion_var.get()
            if emotion_value:
                emotion_index = int(emotion_value.split()[-1])
                self.core.selected_emotion = emotion_index
                self.update_preview()
    
    def on_background_random_changed(self):
        """背景随机选择改变"""
        if self.background_random_var.get():
            # 启用随机，禁用下拉框
            self.background_combo.config(state="disabled")
            self.core.selected_background = None
        else:
            # 禁用随机，启用下拉框
            self.background_combo.config(state="readonly")
            # 设置默认背景
            background_value = self.background_combo.get()
            if background_value:
                background_index = int(background_value.split()[-1])
                self.core.selected_background = background_index
        
        self.update_preview()
    
    def on_background_changed(self, event=None):
        """背景改变事件"""
        if not self.background_random_var.get():  # 只有在非随机模式下才处理
            background_value = self.background_var.get()
            if background_value:
                background_index = int(background_value.split()[-1])
                self.core.selected_background = background_index
                self.update_preview()
    
    def on_auto_paste_changed(self):
        """自动粘贴设置改变"""
        self.core.AUTO_PASTE_IMAGE = self.auto_paste_var.get()
    
    def on_auto_send_changed(self):
        """自动发送设置改变"""
        self.core.AUTO_SEND_IMAGE = self.auto_send_var.get()
    
    def on_pre_compose_changed(self):
        """预合成设置改变"""
        self.core.PRE_COMPOSE_IMAGES = self.pre_compose_var.get()
        if self.core.PRE_COMPOSE_IMAGES:
            self.start_pre_compose()
    
    def start_pre_compose(self):
        """开始预合成图片"""
        character_name = self.core.get_character()
        
        def pre_compose_with_progress():
            def progress_callback(current, total):
                progress = int((current / total) * 100)
                self.root.after(0, self.update_status, f"预合成中... {progress}%")
            
            self.core.pre_compose_images(character_name, progress_callback)
            self.root.after(0, self.update_status, "预合成完成")
        
        thread = threading.Thread(target=pre_compose_with_progress, daemon=True)
        thread.start()
    
    def update_preview(self):
        """更新预览"""
        try:
            preview_image, info = self.core.generate_preview(self.preview_size)
            
            # 转换为 PhotoImage
            self.preview_photo = ImageTk.PhotoImage(preview_image)
            self.preview_label.configure(image=self.preview_photo)
            
            # 更新预览信息
            self.preview_info_var.set(info)
            
        except Exception as e:
            print(f"更新预览失败: {e}")
            self.preview_info_var.set(f"预览生成失败: {str(e)}")
    
    def generate_image(self):
        """生成图片"""
        def generate_in_thread():
            result = self.core.generate_image()
            self.root.after(0, self.update_status, result)
            # 生成后更新预览，以便显示下一次可能的预览
            self.root.after(0, self.update_preview)
        
        self.update_status("正在生成图片...")
        thread = threading.Thread(target=generate_in_thread, daemon=True)
        thread.start()
    
    def delete_cache(self):
        """清除缓存"""
        self.core.delete_cache()
        self.update_status("缓存已清除")
    
    def update_status(self, message: str):
        """更新状态栏"""
        self.status_var.set(message)
    
    def run(self):
        """运行 GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    app = ManosabaGUI()
    app.run()