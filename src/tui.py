""" Textual UI 版本"""
from pynput.keyboard import Key, Controller, GlobalHotKeys
from sys import platform
import os
import yaml
import threading

from rich import print
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, RadioSet, RadioButton, Label, ProgressBar, Switch
from textual.binding import Binding
from textual.reactive import reactive

from main import ManosabaTextBox

PLATFORM = platform.lower()

if PLATFORM.startswith('win'):
    try:
        import win32clipboard
        import keyboard
        import win32gui
        import win32process
    except ImportError:
        print("[red]请先安装 Windows 运行库: pip install pywin32 keyboard[/red]")
        raise

class ManosabaTUI(App):
    """魔裁文本框生成器 TUI"""

    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "textual.tcss"),
              'r', encoding="utf-8") as f:
        CSS = f.read()

    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "keymap.yml"),
              'r', encoding="utf-8") as f:
        keymap = yaml.safe_load(f).get(PLATFORM, {})

    TITLE = "魔裁 文本框生成器"
    theme = "tokyo-night"

    status_msg = reactive("就绪")

    BINDINGS = [
        Binding(keymap['start_generate'], "generate", "生成图片", priority=True),
        Binding(keymap['delete_cache'], "delete_cache", "清除缓存", priority=True),
        Binding(keymap['quit'], "quit", "退出", priority=True),
        Binding(keymap['pause'], "pause", "暂停", priority=True),
    ]

    def __init__(self):
        super().__init__()
        self.textbox = ManosabaTextBox()
        self.textbox.active = True
        self.current_character = self.textbox.get_character()
        self.hotkey_listener = None
        self.setup_global_hotkeys()

    def setup_global_hotkeys(self) -> None:
        """设置全局热键监听器"""
        keymap = self.keymap
        if PLATFORM == "darwin":
            hotkeys = {
                keymap['start_generate']: self.trigger_generate
            }

            self.hotkey_listener = GlobalHotKeys(hotkeys)
            self.hotkey_listener.start()
        elif PLATFORM.startswith('win'):
            keyboard.add_hotkey(keymap['start_generate'], self.trigger_generate)

    def trigger_generate(self) -> None:
        """全局热键触发生成图片（在后台线程中调用）"""
        # 使用 call_from_thread 在主线程中安全地调用 action_generate
        if self.textbox.active:
            self.call_from_thread(self.action_generate)

    def compose(self) -> ComposeResult:
        """创建UI布局"""
        yield Header()

        with Container(id="main_container"):
            with Horizontal():
                with Vertical(id="character_panel"):
                    yield Label("选择角色 (Character)", classes="panel_title")
                    with ScrollableContainer():
                        with RadioSet(id="character_radio"):
                            for char_id in self.textbox.character_list:
                                char_name = self.textbox.get_character(char_id, full_name=True)
                                yield RadioButton(
                                    f"{char_name} ({char_id})",
                                    value=char_id == self.current_character,
                                    id=f"char_{char_id}"
                                )

                with Vertical(id="emotion_panel"):
                    yield Label("选择表情 (Emotion)", classes="panel_title")
                    with ScrollableContainer():
                        with RadioSet(id="emotion_radio"):
                            emotion_cnt = self.textbox.get_current_emotion_count()
                            for i in range(0, emotion_cnt + 1):
                                yield RadioButton(
                                    f"表情 {i}" if i > 0 else "随机表情",
                                    value = (i == 0),
                                    id=f"emotion_{i}"
                                )
                with Vertical(id="switch_panel"):
                    yield Label("自动粘贴: ", classes="switch_label")
                    yield Switch(value=self.textbox.AUTO_PASTE_IMAGE, id="auto_paste_switch")
                    yield Label("自动发送: ", classes="switch_label")
                    yield Switch(value=self.textbox.AUTO_SEND_IMAGE, id="auto_send_switch")

            with Horizontal(id="control_panel"):
                yield Label(self.status_msg, id="status_label")
                yield ProgressBar(id="progress_bar")

        yield Footer()

    def on_mount(self) -> None:
        """应用启动时执行"""
        self.update_status(f"当前角色: {self.textbox.get_character(self.current_character, full_name=True)} ")

        # 预加载当前角色（在后台线程中执行）
        char_name = self.textbox.get_character(self.current_character)
        self.load_character_images(char_name)

    def load_character_images(self, char_name: str) -> None:
        """在后台线程中加载角色图片（内存模式：仅预加载，不生成磁盘缓存）"""

        def load_in_thread():
            # 禁用选择框
            self.call_from_thread(self._disable_radio_sets)

            self.call_from_thread(self.update_status,
                                  f"正在加载角色 {self.textbox.get_character(self.current_character, full_name=True)} ...")

            # 内存模式：只需确保角色表情加载到内存
            emotion_cnt = self.textbox.mahoshojo[char_name]["emotion_count"]
            self.textbox.img_generator._ensure_character_loaded(char_name, emotion_cnt)

            self.call_from_thread(self.update_status,
                                  f"角色 {self.textbox.get_character(self.current_character, full_name=True)} 加载完成 ✓")

            # 恢复选择框
            self.call_from_thread(self._enable_radio_sets)

        thread = threading.Thread(target=load_in_thread, daemon=True)
        thread.start()

    def _show_progress_bar(self) -> None:
        """显示进度条"""
        progress_bar = self.query_one("#progress_bar", ProgressBar)
        progress_bar.add_class("visible")
        progress_bar.update(total=100, progress=0)

    def _hide_progress_bar(self) -> None:
        """隐藏进度条"""
        progress_bar = self.query_one("#progress_bar", ProgressBar)
        progress_bar.remove_class("visible")

    def _update_progress(self, current: int, total: int) -> None:
        """更新进度条"""
        progress_bar = self.query_one("#progress_bar", ProgressBar)
        progress_bar.update(total=total, progress=current)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """当Switch状态改变时"""
        if event.switch.id == "auto_paste_switch":
            self.textbox.AUTO_PASTE_IMAGE = event.value
            self.update_status("自动粘贴已" + ("启用" if event.value else "禁用"))
            auto_send_switch = self.query_one("#auto_send_switch", Switch)
            if event.value == False:
                self.textbox.AUTO_SEND_IMAGE = False
                auto_send_switch.value = False
                auto_send_switch.disabled = True
            else:
                self.textbox.AUTO_SEND_IMAGE = True
                auto_send_switch.disabled = False
        elif event.switch.id == "auto_send_switch":
            self.textbox.AUTO_SEND_IMAGE = event.value
            self.update_status("自动发送已" + ("启用" if event.value else "禁用"))

    def _disable_radio_sets(self) -> None:
        """禁用所有RadioSet"""
        try:
            char_radio = self.query_one("#character_radio", RadioSet)
            char_radio.disabled = True

            emotion_radio = self.query_one("#emotion_radio", RadioSet)
            emotion_radio.disabled = True
        except Exception as e:
            self.notify(str(e), title="禁用选择框失败", severity="warning")

    def _enable_radio_sets(self) -> None:
        """启用所有RadioSet"""
        try:
            char_radio = self.query_one("#character_radio", RadioSet)
            char_radio.disabled = False

            emotion_radio = self.query_one("#emotion_radio", RadioSet)
            emotion_radio.disabled = False
        except Exception as e:
            self.notify(str(e), title="启用选择框失败", severity="warning")

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """当RadioSet选项改变时"""
        if event.radio_set.id == "character_radio":
            selected_char = event.pressed.id.replace("char_", "")
            self.current_character = selected_char

            # 更新角色索引
            char_idx = self.textbox.character_list.index(selected_char) + 1
            self.textbox.switch_character(char_idx)

            # 预加载新角色（使用带进度条的加载方法）
            self.load_character_images(selected_char)

            # 重新生成表情选项（延迟执行以确保状态更新完成）
            self.call_after_refresh(self.refresh_emotion_panel)

        elif event.radio_set.id == "emotion_radio":
            # 从按钮 id 中提取表情编号
            try:
                label = event.pressed.id
                emotion_num = int(label.split('_')[-1])
                self.current_emotion = emotion_num
                self.textbox.emote = emotion_num
                self.update_status(f"已选择表情 {emotion_num} 喵" if emotion_num > 0 else "已选择随机表情喵")
            except (ValueError, AttributeError, IndexError) as e:
                self.update_status(e)
                pass

    def refresh_emotion_panel(self) -> None:
        """刷新表情面板"""
        emotion_radio = self.query_one("#emotion_radio", RadioSet)

        # 获取所有子组件并逐个移除
        children = list(emotion_radio.children)
        for child in children:
            try:
                child.remove()
            except Exception:
                pass

        # 重置表情为 0
        self.current_emotion = 0
        self.textbox.emote = 0

        # 添加新的按钮
        emotion_cnt = self.textbox.get_current_emotion_count()
        for i in range(0, emotion_cnt + 1):
            unique_id = f"emotion_{self.current_character}_{i}"
            btn = RadioButton(
                f"表情 {i}" if i > 0 else "随机表情",
                value=(self.textbox.emote == i),
                id=unique_id
            )
            emotion_radio.mount(btn)

    def update_status(self, msg: str) -> None:
        """更新状态栏"""
        self.status_msg = msg
        status_label = self.query_one("#status_label", Label)
        status_label.update(msg)

    def action_pause(self):
        """切换暂停状态"""
        self.textbox.toggle_active()
        status = "激活" if self.textbox.active else "暂停"
        self.update_status(f"应用已{status}。")
        main_container = self.query_one("#main_container")
        main_container.disabled = not self.textbox.active

    def action_generate(self) -> None:
        """生成图片"""
        self.update_status("正在生成图片...")
        result = self.textbox.start()
        self.update_status(result)

    def action_delete_cache(self) -> None:
        """清除缓存（包括内存和磁盘）"""
        self.update_status("正在清除缓存...")

        # 清除内存缓存
        self.textbox.img_generator.clear_memory_cache()

        # 清除磁盘缓存
        self.textbox.delete()

        cache_info = self.textbox.img_generator.get_cache_info()
        self.update_status(f"缓存已清除 (内存: {cache_info['chars_cnt']}角色, 背景: {cache_info['bg_cached']}张)")

        # 重新加载当前角色
        char_name = self.textbox.get_character(self.current_character)
        self.load_character_images(char_name)

    def action_quit(self) -> None:
        """退出应用"""
        # 停止全局热键监听器
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.exit()


if __name__ == "__main__":
    app = ManosabaTUI()
    app.run()
