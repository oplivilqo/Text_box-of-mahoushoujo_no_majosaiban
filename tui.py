""" Textual UI 版本"""
import random
import time
import psutil
from pynput.keyboard import Key, Controller
import threading
from sys import platform
import os

from rich import print
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, RadioSet, RadioButton, Label, Switch
from textual.binding import Binding
from textual.reactive import reactive

from core import ManosabaCore

PLATFORM = platform.lower()

if PLATFORM.startswith('win'):
    try:
        import win32gui
        import win32process
        import keyboard
    except ImportError:
        print("[red]请先安装 Windows 运行库: pip install pywin32 keyboard[/red]")
        raise


class ManosabaTUI(App):
    """魔裁文本框生成器 TUI"""

    CSS = """
    #main_container {
        margin: 1;
        padding: 1;
    }
    
    .panel_title {
        text-style: bold;
        margin-bottom: 1;
    }
    
    #character_panel, #emotion_panel, #background_panel, #switch_panel {
        height: 100%;
        border: solid $accent;
        margin: 1;
        padding: 1;
    }
    
    #character_panel {
        width: 35%;
    }
    
    #emotion_panel {
        width: 25%;
    }
    
    #background_panel {
        width: 25%;
    }
    
    #switch_panel {
        width: 15%;
    }
    
    .switch_label {
        margin: 1 0;
    }
    
    #status_label {
        margin: 1;
        padding: 1;
        background: $panel;
        border: solid $accent;
    }
    
    #control_panel {
        height: 5;
        align: center middle;
    }
    """

    TITLE = "魔裁 文本框生成器"
    SUB_TITLE = "TUI Version"

    current_character = reactive("")
    current_emotion = reactive(None)  # None表示随机
    current_background = reactive(None)  # None表示随机
    status_msg = reactive("就绪")

    BINDINGS = [
        Binding("ctrl+g", "generate", "生成图片", priority=True),
        Binding("ctrl+q", "quit", "退出", priority=True),
    ]

    def __init__(self):
        super().__init__()
        self.core = ManosabaCore()
        self.current_character = self.core.get_character()
        self.hotkey_listener = None
        self.setup_global_hotkeys()
        self._emotion_initialized = False
        self._background_initialized = False

    def setup_global_hotkeys(self) -> None:
        """设置全局热键监听器"""
        if PLATFORM.startswith('win'):
            try:
                hotkey = self.core.keymap.get('start_generate', 'ctrl+alt+g')
                keyboard.add_hotkey(hotkey, self.trigger_generate, suppress=False)
            except Exception as e:
                print(f"热键设置失败: {e}")

    def trigger_generate(self) -> None:
        """全局热键触发生成图片"""
        self.call_from_thread(self.action_generate)

    def compose(self) -> ComposeResult:
        """创建UI布局"""
        yield Header()

        with Container(id="main_container"):
            with Horizontal():
                with Vertical(id="character_panel"):
                    yield Label("选择角色", classes="panel_title")
                    with ScrollableContainer():
                        with RadioSet(id="character_radio"):
                            for char_id in self.core.character_list:
                                char_name = self.core.get_character(char_id, full_name=True)
                                is_current = char_id == self.current_character
                                yield RadioButton(
                                    f"{char_name} ({char_id})",
                                    value=is_current,
                                    id=f"char_{char_id}"
                                )

                with Vertical(id="emotion_panel"):
                    yield Label("选择表情", classes="panel_title")
                    with ScrollableContainer():
                        # 在compose阶段直接创建表情选项
                        with RadioSet(id="emotion_radio"):
                            yield RadioButton("随机", value=True, id="emotion_random")
                            emotion_cnt = self.core.get_current_emotion_count()
                            for i in range(1, emotion_cnt + 1):
                                yield RadioButton(
                                    f"表情 {i}",
                                    value=False,
                                    id=f"emotion_{i}"
                                )
                        self._emotion_initialized = True

                with Vertical(id="background_panel"):
                    yield Label("选择背景", classes="panel_title")
                    with ScrollableContainer():
                        # 在compose阶段直接创建背景选项
                        with RadioSet(id="background_radio"):
                            yield RadioButton("随机", value=True, id="background_random")
                            background_count = self.core.image_processor.background_count
                            for i in range(1, background_count + 1):
                                yield RadioButton(
                                    f"背景 {i}",
                                    value=False,
                                    id=f"background_{i}"
                                )
                        self._background_initialized = True

                with Vertical(id="switch_panel"):
                    yield Label("自动粘贴:", classes="switch_label")
                    yield Switch(value=self.core.config.AUTO_PASTE_IMAGE, id="auto_paste_switch")
                    yield Label("自动发送:", classes="switch_label")
                    yield Switch(value=self.core.config.AUTO_SEND_IMAGE, id="auto_send_switch")

            with Horizontal(id="control_panel"):
                yield Label(self.status_msg, id="status_label")

        yield Footer()

    def on_mount(self) -> None:
        """应用启动时执行"""
        self.update_status(f"当前角色: {self.core.get_character(full_name=True)}")

    def safe_refresh_emotion_panel(self) -> None:
        """安全刷新表情面板 - 使用延迟执行避免挂载问题"""
        if not self._emotion_initialized:
            return
            
        def do_refresh():
            emotion_radio = self.query_one("#emotion_radio")
            
            # 保存当前选中的表情
            current_emotion = self.current_emotion
            
            # 完全移除所有子组件
            for child in list(emotion_radio.children):
                try:
                    child.remove()
                except:
                    pass
            
            # 重新添加选项
            emotion_radio.mount(RadioButton("随机", value=(current_emotion is None), id="emotion_random_new"))
            
            emotion_cnt = self.core.get_current_emotion_count()
            for i in range(1, emotion_cnt + 1):
                emotion_radio.mount(
                    RadioButton(f"表情 {i}", value=(current_emotion == i), id=f"emotion_{i}_new")
                )
        
        # 延迟执行，确保UI已经稳定
        self.set_timer(0.1, do_refresh)

    def safe_refresh_background_panel(self) -> None:
        """安全刷新背景面板 - 使用延迟执行避免挂载问题"""
        if not self._background_initialized:
            return
            
        def do_refresh():
            background_radio = self.query_one("#background_radio")
            
            # 保存当前选中的背景
            current_background = self.current_background
            
            # 完全移除所有子组件
            for child in list(background_radio.children):
                try:
                    child.remove()
                except:
                    pass
            
            # 重新添加选项
            background_radio.mount(RadioButton("随机", value=(current_background is None), id="background_random_new"))
            
            background_count = self.core.image_processor.background_count
            for i in range(1, background_count + 1):
                background_radio.mount(
                    RadioButton(f"背景 {i}", value=(current_background == i), id=f"background_{i}_new")
                )
        
        # 延迟执行，确保UI已经稳定
        self.set_timer(0.1, do_refresh)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """当Switch状态改变时"""
        if event.switch.id == "auto_paste_switch":
            self.core.config.AUTO_PASTE_IMAGE = event.value
            self.update_status("自动粘贴已" + ("启用" if event.value else "禁用"))
            
            # 如果禁用自动粘贴，也禁用自动发送
            auto_send_switch = self.query_one("#auto_send_switch", Switch)
            if not event.value:
                self.core.config.AUTO_SEND_IMAGE = False
                auto_send_switch.value = False
            auto_send_switch.disabled = not event.value
            
        elif event.switch.id == "auto_send_switch":
            self.core.config.AUTO_SEND_IMAGE = event.value
            self.update_status("自动发送已" + ("启用" if event.value else "禁用"))

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """当RadioSet选项改变时"""
        if event.radio_set.id == "character_radio":
            selected_char = event.pressed.id.replace("char_", "")
            self.current_character = selected_char

            # 更新角色索引
            char_idx = self.core.character_list.index(selected_char) + 1
            self.core.switch_character(char_idx)

            # 重置表情选择
            self.current_emotion = None
            self.core.selected_emotion = None
            
            # 安全刷新表情选项
            self.safe_refresh_emotion_panel()
            
            self.update_status(f"已切换到角色: {self.core.get_character(full_name=True)}")

        elif event.radio_set.id == "emotion_radio":
            # 处理表情选择
            emotion_id = event.pressed.id
            if emotion_id == "emotion_random" or emotion_id == "emotion_random_new":
                self.current_emotion = None
                self.core.selected_emotion = None
                self.update_status("已选择随机表情")
            else:
                try:
                    # 处理新旧ID格式
                    emotion_id_clean = emotion_id.replace("_new", "")
                    emotion_num = int(emotion_id_clean.replace("emotion_", ""))
                    self.current_emotion = emotion_num
                    self.core.selected_emotion = emotion_num
                    self.update_status(f"已选择表情 {emotion_num}")
                except (ValueError, AttributeError, IndexError) as e:
                    self.update_status(f"选择表情错误: {e}")

        elif event.radio_set.id == "background_radio":
            # 处理背景选择
            background_id = event.pressed.id
            if background_id == "background_random" or background_id == "background_random_new":
                self.current_background = None
                self.core.selected_background = None
                self.update_status("已选择随机背景")
            else:
                try:
                    # 处理新旧ID格式
                    background_id_clean = background_id.replace("_new", "")
                    background_num = int(background_id_clean.replace("background_", ""))
                    self.current_background = background_num
                    self.core.selected_background = background_num
                    self.update_status(f"已选择背景 {background_num}")
                except (ValueError, AttributeError, IndexError) as e:
                    self.update_status(f"选择背景错误: {e}")

    def update_status(self, msg: str) -> None:
        """更新状态栏"""
        self.status_msg = msg
        status_label = self.query_one("#status_label", Label)
        status_label.update(msg)

    def action_generate(self) -> None:
        """生成图片"""
        def generate_in_thread():
            try:
                result = self.core.generate_image()
                self.call_from_thread(lambda: self.update_status(result))
            except Exception as e:
                self.call_from_thread(lambda: self.update_status(f"生成失败: {str(e)}"))
        
        self.update_status("正在生成图片...")
        thread = threading.Thread(target=generate_in_thread, daemon=True)
        thread.start()

    def action_quit(self) -> None:
        """退出应用"""
        if PLATFORM.startswith('win'):
            try:
                keyboard.clear_all_hotkeys()
            except:
                pass
        self.exit()


if __name__ == "__main__":
    app = ManosabaTUI()
    app.run()