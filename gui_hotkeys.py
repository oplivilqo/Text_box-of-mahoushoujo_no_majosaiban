"""热键管理模块"""

import threading
import time
import keyboard
from load_utils import clear_cache


class HotkeyManager:
    """热键管理器"""

    def __init__(self, gui):
        self.gui = gui
        self.core = gui.core
        self.hotkey_listener_active = True
        self.hotkey_thread = None
        self.last_hotkey_time = {}  # 记录每个热键的最后触发时间
        self.debounce_delay = 0.5   # 防抖延迟时间（秒）
        self._thread_lock = threading.Lock()  # 线程锁，防止重复创建线程

    def setup_hotkeys(self):
        """设置热键监听（仅在初始化时调用）"""
        with self._thread_lock:
            if self.hotkey_thread and self.hotkey_thread.is_alive():
                return  # 如果线程已经在运行，则不重复启动
            
            self.hotkey_listener_active = True
            self.hotkey_thread = threading.Thread(target=self.hotkey_listener, daemon=True)
            self.hotkey_thread.start()
            print("热键监听线程已启动")

    def restart_hotkey_listener(self):
        """重启热键监听线程（用于修改快捷键设置后）"""
        with self._thread_lock:
            # 先停止现有线程
            self._stop_hotkey_listener()
            
            # 等待一小段时间确保线程完全停止
            time.sleep(0.1)
            
            # 重新启动线程
            self.hotkey_listener_active = True
            self.hotkey_thread = threading.Thread(target=self.hotkey_listener, daemon=True)
            self.hotkey_thread.start()
            print("热键监听线程已重启")

    def _stop_hotkey_listener(self):
        """内部方法：停止热键监听线程"""
        self.hotkey_listener_active = False
        if self.hotkey_thread and self.hotkey_thread.is_alive():
            # 等待线程自然结束（最多等待1秒）
            self.hotkey_thread.join(timeout=1.0)
            if self.hotkey_thread.is_alive():
                print("警告：热键监听线程未能正常停止，强制结束")

    def hotkey_listener(self):
        """热键监听线程"""
        try:
            while True:  # 保持无限循环，通过hotkey_listener_active控制是否处理热键
                
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
                
                # 优先检查停止监听热键
                toggle_hotkey = hotkeys.get("toggle_listener", "alt+ctrl+p")
                if self._is_hotkey_pressed(toggle_hotkey, "toggle_listener"):
                    self.gui.root.after(0, self.toggle_hotkey_listener)
                    time.sleep(1.0)  # 增加防抖时间，防止冲突
                    continue  # 处理完toggle后直接继续，避免其他热键干扰
                
                # 如果监听未激活，则等待
                if not self.hotkey_listener_active:
                    time.sleep(0.1)
                    continue

                # 检查每个热键
                for action, hotkey in hotkeys.items():
                    # 跳过toggle_listener，因为已经单独处理了
                    if action == "toggle_listener":
                        continue
                        
                    # 只监听GUI相关的热键
                    if action in [
                        "start_generate",
                        "next_character",
                        "prev_character",
                        "next_background",
                        "prev_background",
                        "next_emotion",
                        "prev_emotion",
                    ] or action.startswith("character_"):
                        if self._is_hotkey_pressed(hotkey, action):
                            # 对于角色快捷键，传递角色ID
                            if action.startswith("character_"):
                                char_id = quick_chars.get(action, "")
                                self.gui.root.after(
                                    0,
                                    lambda a=action, c=char_id: self.handle_hotkey_action(
                                        a, c
                                    ),
                                )
                            else:
                                self.gui.root.after(
                                    0, lambda a=action: self.handle_hotkey_action(a)
                                )
                            # 防止重复触发
                            time.sleep(0.3)
                            break

                time.sleep(0.05)  # 降低CPU使用率

        except Exception as e:
            print(f"热键监听错误: {e}")
            # 出错时重新启动监听（但避免无限重启）
            if self.hotkey_listener_active:
                time.sleep(1)
                if self.hotkey_listener_active:
                    self.restart_hotkey_listener()

    def toggle_hotkey_listener(self):
        """切换热键监听状态"""
        self.hotkey_listener_active = not self.hotkey_listener_active
        status = "启用" if self.hotkey_listener_active else "禁用"
        self.gui.update_status(f"热键监听已{status}")
        print(f"热键监听状态已切换为: {status}")

    def update_hotkeys(self):
        """更新热键设置（供SettingsWindow调用）"""
        # 修改快捷键设置后需要重启监听线程
        self.restart_hotkey_listener()

    def _is_hotkey_pressed(self, hotkey, action_name):
        """热键检测"""
        current_time = time.time()
        
        # 检查防抖时间
        if action_name in self.last_hotkey_time:
            if current_time - self.last_hotkey_time[action_name] < self.debounce_delay:
                return False
        
        # 直接使用keyboard库的热键检测
        try:
            if keyboard.is_pressed(hotkey):
                self.last_hotkey_time[action_name] = current_time
                return True
        except Exception as e:
            print(f"热键检测错误 {hotkey}: {e}")
        
        return False

    def handle_hotkey_action(self, action, char_id=None):
        """处理热键动作"""
        try:
            if action == "start_generate":
                # 确保所有按键释放后再执行生成操作
                self._wait_for_keys_release()
                self.gui.generate_image()  # 生成图片
            elif action == "next_character":
                self.switch_character(1)  # 向后切换
            elif action == "prev_character":
                self.switch_character(-1)  # 向前切换
            elif action == "next_emotion":  # 向前切换表情
                self.switch_emotion(1)
            elif action == "prev_emotion":  # 向后切换表情
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

    def _wait_for_keys_release(self, timeout=2.0):
        """等待所有按键释放"""
        import time
        import keyboard
        
        start_time = time.time()
        keys_checked = set()
        
        # 检查常见修饰键和字母数字键是否释放
        common_keys = [
            'ctrl', 'alt', 'shift', 'win', 
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
        ]
        
        while time.time() - start_time < timeout:
            all_released = True
            
            # 检查常见按键是否都已释放
            for key in common_keys:
                if keyboard.is_pressed(key):
                    all_released = False
                    if key not in keys_checked:
                        # print(f"检测到按键 {key} 未释放，等待中...")
                        keys_checked.add(key)
                    break
            
            if all_released:
                # print("所有按键已释放，继续执行生成操作")
                return
            
            time.sleep(0.05)  # 短暂等待后再次检查
        
        print(f"警告：等待按键释放超时（{timeout}秒），继续执行操作")

    def toggle_hotkey_listener(self):
        """切换热键监听状态"""
        self.hotkey_listener_active = not self.hotkey_listener_active
        status = "启用" if self.hotkey_listener_active else "禁用"
        self.gui.update_status(f"热键监听已{status}")
        print(f"热键监听状态已切换为: {status}")  # 添加调试信息

    def update_hotkeys(self):
        """更新热键设置（供SettingsWindow调用）"""
        # 热键会在监听线程中自动重新加载，这里只需要确保监听在运行
        if not self.hotkey_listener_active:
            self.hotkey_listener_active = True

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
            self._handle_character_switch_success()
    
    def switch_to_character_by_id(self, char_id):
        """通过角色ID切换到指定角色"""
        if char_id and char_id in self.core.character_list:
            char_index = self.core.character_list.index(char_id) + 1
            if self.core.switch_character(char_index):
                self._handle_character_switch_success()
    
    def switch_emotion(self, direction):
        """切换表情"""
        # 取消情感匹配勾选
        self._cancel_sentiment_matching()
        
        if self.gui.emotion_random_var.get():
            # 如果当前是随机模式，切换到指定模式
            self.gui.emotion_random_var.set(False)
            self.gui.on_emotion_random_changed()
    
        emotion_count = self.core.get_current_emotion_count()
        current_emotion = self.core.selected_emotion or 1
    
        new_emotion = current_emotion + direction
        if new_emotion > emotion_count:
            new_emotion = 1
        elif new_emotion < 1:
            new_emotion = emotion_count
    
        self.core.selected_emotion = new_emotion
        self.gui.emotion_combo.set(f"表情 {new_emotion}")
        self.gui.update_preview()
        self.gui.update_status(f"已切换到表情: {new_emotion}")

    def _handle_character_switch_success(self):
        """处理角色切换成功后的通用操作"""
        # 切换角色后清理缓存
        clear_cache("character")
        # 更新GUI显示
        self.gui.character_var.set(
            f"{self.core.get_character(full_name=True)} ({self.core.get_character()})"
        )
        self.gui.update_emotion_options()
        
        # 重置表情索引为1，与手动切换保持一致
        self.gui.emotion_combo.set("表情 1")
        if self.gui.emotion_random_var.get():
            self.core.selected_emotion = None
        else:
            self.core.selected_emotion = 1
        
        self.gui.update_preview()
        self.gui.update_status(
            f"已切换到角色: {self.core.get_character(full_name=True)}"
        )
    
    def _cancel_sentiment_matching(self):
        """取消情感匹配并更新状态"""
        if self.gui.sentiment_matching_var.get():
            self.gui.sentiment_matching_var.set(False)
            self.gui.on_sentiment_matching_changed()
            self.gui.update_status("已取消情感匹配（手动切换表情）")

    def switch_background(self, direction):
        """切换背景"""
        if self.gui.background_random_var.get():
            # 如果当前是随机模式，切换到指定模式
            self.gui.background_random_var.set(False)
            self.gui.on_background_random_changed()

        current_bg = self.core.selected_background or 1
        total_bgs = self.core.image_processor.background_count

        new_bg = current_bg + direction
        if new_bg > total_bgs:
            new_bg = 1
        elif new_bg < 1:
            new_bg = total_bgs

        self.core.selected_background = new_bg
        self.gui.background_combo.set(f"背景 {new_bg}")
        self.gui.update_preview()
        self.gui.update_status(f"已切换到背景: {new_bg}")

    def switch_to_character_by_id(self, char_id):
        """通过角色ID切换到指定角色"""
        if char_id and char_id in self.core.character_list:
            char_index = self.core.character_list.index(char_id) + 1
            if self.core.switch_character(char_index):
                self.gui.character_var.set(
                    f"{self.core.get_character(full_name=True)} ({self.core.get_character()})"
                )
                self.gui.update_emotion_options()
                
                # 重置表情索引为1
                self.gui.emotion_combo.set("表情 1")
                if self.gui.emotion_random_var.get():
                    self.core.selected_emotion = None
                else:
                    self.core.selected_emotion = 1
                
                self.gui.update_preview()
                self.gui.update_status(
                    f"已快速切换到角色: {self.core.get_character(full_name=True)}"
                )