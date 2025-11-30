"""GUI组件模块"""

import tkinter as tk
from tkinter import ttk
from PIL import ImageTk


class PreviewManager:
    """预览管理器"""

    def __init__(self, gui):
        self.gui = gui
        self.core = gui.core
        self.preview_size = (700, 525)
        
        # 预览相关变量
        self.preview_label = None
        self.preview_info_var1 = None
        self.preview_info_var2 = None
        self.preview_info_var3 = None

    def setup_preview_frame(self, parent):
        """设置预览框架"""
        # 预览信息区域（放在图片上方，横向排列三个信息项）
        preview_info_frame = ttk.Frame(parent)
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
            preview_info_frame, text="刷新", command=self.gui.update_preview, width=10
        ).pack(side=tk.RIGHT, padx=5)

        # 图片预览区域
        self.preview_label = ttk.Label(parent)
        self.preview_label.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

    def handle_window_resize(self, event):
        """处理窗口大小变化事件 - 调整大小并刷新内容"""
        if event.widget == self.gui.root:
            window_width = self.gui.root.winfo_width()
            new_width = max(200, window_width - 40)
            new_height = int(new_width * 0.75)

            if (
                abs(new_width - self.preview_size[0]) > 30
                or abs(new_height - self.preview_size[1]) > 20
            ):
                self.preview_size = (new_width, new_height)
                # 更新预览内容
                self.gui.update_preview()

    def update_preview(self):
        """更新预览"""
        try:
            preview_image, info = self.core.generate_preview(self.preview_size)

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


class StatusManager:
    """状态管理器"""

    def __init__(self, gui):
        self.gui = gui
        self.status_var = None
        self.status_bar = None

    def setup_status_bar(self, parent, row):
        """设置状态栏"""
        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = ttk.Label(
            parent, textvariable=self.status_var, relief=tk.SUNKEN
        )
        self.status_bar.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

    def update_status(self, message: str):
        """更新状态栏"""
        self.status_var.set(message)
        self.gui.root.update_idletasks()

    # def set_status(self, message: str):
    #     """设置状态（别名方法）"""
    #     self.update_status(message)