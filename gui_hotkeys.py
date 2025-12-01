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

    def setup_hotkeys(self):
        """设置热键监听"""
        self.hotkey_listener_active = True
        self.hotkey_thread = threading.Thread(target=self.hotkey_listener, daemon=True)
        self.hotkey_thread.start()

    def hotkey_listener(self):
        """热键监听线程"""
        try:
            while self.hotkey_listener_active:
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
                    self.gui.root.after(0, self.toggle_hotkey_listener)
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
                    ] or action.startswith("character_"):
                        if keyboard.is_pressed(hotkey):
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
            time.sleep(1)  # 出错时等待1秒再重试

    def handle_hotkey_action(self, action, char_id=None):
        """处理热键动作"""
        try:
            if action == "start_generate":
                self.gui.generate_image()  # 生成图片
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
        # 取消情感匹配勾选
        if self.gui.sentiment_matching_var.get():
            self.gui.sentiment_matching_var.set(False)
            self.gui.on_sentiment_matching_changed()
            self.gui.update_status("已取消情感匹配（手动切换表情）")
            
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
            clear_cache("character")
            # 更新GUI显示
            self.gui.character_var.set(
                f"{self.core.get_character(full_name=True)} ({self.core.get_character()})"
            )
            self.gui.update_emotion_options()
            self.gui.update_preview()
            self.gui.update_status(
                f"已切换到角色: {self.core.get_character(full_name=True)}"
            )

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
                self.gui.update_preview()
                self.gui.update_status(
                    f"已快速切换到角色: {self.core.get_character(full_name=True)}"
                )

    def toggle_hotkey_listener(self):
        """切换热键监听状态"""
        self.hotkey_listener_active = not self.hotkey_listener_active
        status = "启用" if self.hotkey_listener_active else "禁用"
        self.gui.update_status(f"热键监听已{status}")

    def update_hotkeys(self):
        """更新热键设置（供SettingsWindow调用）"""
        # 热键会在监听线程中自动重新加载，这里只需要确保监听在运行
        if not self.hotkey_listener_active:
            self.hotkey_listener_active = True