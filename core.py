"""魔裁文本框核心逻辑"""
from config import ConfigLoader, AppConfig
from clipboard_utils import ClipboardManager
from image_processor import ImageProcessor
from sentiment_analyzer import SentimentAnalyzer
from load_utils import clear_cache, preload_all_images_async
from path_utils import get_available_fonts

import os
import time
import random
import psutil
import threading
from pynput.keyboard import Key, Controller
from sys import platform
import keyboard as kb_module
from typing import Dict, Any

if platform.startswith("win"):
    try:
        import win32gui
        import win32process
    except ImportError:
        print("[red]请先安装 Windows 运行库: pip install pywin32[/red]")
        raise

class ManosabaCore:
    """魔裁文本框核心类"""

    def __init__(self):
        # 初始化配置
        self.config = AppConfig(os.path.dirname(os.path.abspath(__file__)))
        self.kbd_controller = Controller()
        self.clipboard_manager = ClipboardManager()

        # 加载配置
        self.config_loader = ConfigLoader()
        self.mahoshojo = {}
        self.text_configs_dict = {}
        self.character_list = []
        self.keymap = {}
        self.process_whitelist = []
        self.load_configs()

        # 初始化图片处理器
        self.image_processor = ImageProcessor(
            self.config.BASE_PATH,
            self.config.BOX_RECT,
            self.text_configs_dict,
            self.mahoshojo,  # 传递角色元数据用于字体获取
        )

        # 状态变量
        self.selected_emotion = None
        self.selected_background = None
        self.last_emotion = -1
        self.current_character_index = 2

        # 状态更新回调
        self.status_callback = None

        # GUI设置
        self.gui_settings = self.config_loader.load_gui_settings()

        # 初始化情感分析器 - 不在这里初始化，等待特定时机
        self.sentiment_analyzer = SentimentAnalyzer()
        self.sentiment_analyzer_status = {
            'initialized': False,
            'initializing': False,
            'current_config': {}
        }
        self.gui_callback = None  # 新增：用于通知GUI状态变化的回调函数
        
        # 程序启动时开始预加载图片
        self.update_status("正在预加载图片到缓存...")
        self._preload_images_async()

        # 程序启动时检查是否需要初始化
        sentiment_settings = self.gui_settings.get("sentiment_matching", {})
        if sentiment_settings.get("enabled", False):
            self.update_status("检测到启用情感匹配，正在初始化...")
            self._initialize_sentiment_analyzer_async()
        else:
            self.update_status("情感匹配功能未启用")
            self._notify_gui_status_change(False, False)

    
    def _preload_images_async(self):
        """异步预加载所有图片到缓存"""
        def preload_callback(success, message):
            if success:
                self.update_status("图片预加载完成，所有资源已缓存")
            else:
                self.update_status(f"图片预加载失败: {message}")
        
        # 开始异步预加载
        preload_all_images_async(
            self.config.BASE_PATH,
            self.mahoshojo,
            callback=preload_callback
        )

    def set_gui_callback(self, callback):
        """设置GUI回调函数，用于通知状态变化"""
        self.gui_callback = callback

    def _notify_gui_status_change(self, initialized: bool, enabled: bool = None, initializing: bool = False):
        """通知GUI状态变化"""
        if self.gui_callback:
            if enabled is None:
                # 如果没有指定enabled，则使用当前设置
                sentiment_settings = self.gui_settings.get("sentiment_matching", {})
                enabled = sentiment_settings.get("enabled", False) and initialized
            self.gui_callback(initialized, enabled, initializing)

    def _initialize_sentiment_analyzer_async(self):
        """异步初始化情感分析器"""
        def init_task():
            try:
                self.sentiment_analyzer_status['initializing'] = True
                self._notify_gui_status_change(False, False, True)
                
                sentiment_settings = self.gui_settings.get("sentiment_matching", {})
                if sentiment_settings.get("enabled", False):
                    client_type = sentiment_settings.get("ai_model", "ollama")
                    model_configs = sentiment_settings.get("model_configs", {})
                    config = model_configs.get(client_type, {})
                    
                    # 记录当前配置
                    self.sentiment_analyzer_status['current_config'] = {
                        'client_type': client_type,
                        'config': config.copy()
                    }
                    
                    success = self.sentiment_analyzer.initialize(client_type, config)
                    
                    if success:
                        self.update_status("情感分析器初始化完成，功能已启用")
                        self.sentiment_analyzer_status['initialized'] = True
                        # 通知GUI初始化成功
                        self._notify_gui_status_change(True, True, False)
                    else:
                        self.update_status("情感分析器初始化失败，功能已禁用")
                        self.sentiment_analyzer_status['initialized'] = False
                        # 通知GUI初始化失败，需要禁用情感匹配
                        self._notify_gui_status_change(False, False, False)
                        # 更新设置，禁用情感匹配
                        self._disable_sentiment_matching()
                else:
                    self.update_status("情感匹配功能未启用，跳过初始化")
                    self.sentiment_analyzer_status['initialized'] = False
                    self._notify_gui_status_change(False, False, False)
                    
            except Exception as e:
                self.update_status(f"情感分析器初始化失败: {e}，功能已禁用")
                self.sentiment_analyzer_status['initialized'] = False
                # 通知GUI初始化失败，需要禁用情感匹配
                self._notify_gui_status_change(False, False, False)
                # 更新设置，禁用情感匹配
                self._disable_sentiment_matching()
            finally:
                self.sentiment_analyzer_status['initializing'] = False
        
        # 在后台线程中初始化
        init_thread = threading.Thread(target=init_task, daemon=True)
        init_thread.start()    
    
    def toggle_sentiment_matching(self):
        """切换情感匹配状态"""
        # 如果正在初始化，不处理点击
        if self.sentiment_analyzer_status['initializing']:
            return
            
        sentiment_settings = self.gui_settings.get("sentiment_matching", {})
        current_enabled = sentiment_settings.get("enabled", False)
        
        if not current_enabled:
            # 如果当前未启用，则启用并初始化
            if not self.sentiment_analyzer_status['initialized']:
                # 如果未初始化，则开始初始化
                self.update_status("正在初始化情感分析器...")
                if "sentiment_matching" not in self.gui_settings:
                    self.gui_settings["sentiment_matching"] = {}
                self.gui_settings["sentiment_matching"]["enabled"] = True
                self.config_loader.save_gui_settings(self.gui_settings)
                self._initialize_sentiment_analyzer_async()
            else:
                # 如果已初始化，直接启用
                self.update_status("已启用情感匹配功能")
                self.gui_settings["sentiment_matching"]["enabled"] = True
                self.config_loader.save_gui_settings(self.gui_settings)
                self._notify_gui_status_change(True, True, False)
        else:
            # 如果当前已启用，则禁用
            self.update_status("已禁用情感匹配功能")
            self.gui_settings["sentiment_matching"]["enabled"] = False
            self.config_loader.save_gui_settings(self.gui_settings)
            self._notify_gui_status_change(self.sentiment_analyzer_status['initialized'], False, False)

    def _disable_sentiment_matching(self):
        """禁用情感匹配设置"""
        if "sentiment_matching" in self.gui_settings:
            self.gui_settings["sentiment_matching"]["enabled"] = False
        # 保存设置
        self.config_loader.save_gui_settings(self.gui_settings)
        self.update_status("情感匹配功能已禁用")

    def _reinitialize_sentiment_analyzer_if_needed(self):
        """检查配置是否有变化，如果有变化则重新初始化"""
        sentiment_settings = self.gui_settings.get("sentiment_matching", {})
        if not sentiment_settings.get("enabled", False):
            # 如果功能被禁用，重置状态
            if self.sentiment_analyzer_status['initialized']:
                self.sentiment_analyzer_status['initialized'] = False
                self.update_status("情感匹配已禁用，重置分析器状态")
                self._notify_gui_status_change(False, False, False)
            return
        
        client_type = sentiment_settings.get("ai_model", "ollama")
        model_configs = sentiment_settings.get("model_configs", {})
        config = model_configs.get(client_type, {})
        
        new_config = {
            'client_type': client_type,
            'config': config.copy()
        }
        
        # 检查配置是否有变化
        if new_config != self.sentiment_analyzer_status['current_config']:
            self.update_status("AI配置已更改，重新初始化情感分析器")
            self.sentiment_analyzer_status['initialized'] = False
            self.sentiment_analyzer_status['current_config'] = new_config
            # 通知GUI开始重新初始化
            self._notify_gui_status_change(False, False, False)
            self._initialize_sentiment_analyzer_async()

    def get_ai_models(self) -> Dict[str, Dict[str, Any]]:
        """获取可用的AI模型配置"""
        return self.sentiment_analyzer.client_manager.get_available_models()

    def test_ai_connection(self, client_type: str, config: Dict[str, Any]) -> bool:
        """测试AI连接 - 这会进行模型初始化"""
        try:
            # 使用临时分析器进行测试，不影响主分析器状态
            temp_analyzer = SentimentAnalyzer()
            success = temp_analyzer.initialize(client_type, config)
            if success:
                self.update_status(f"AI连接测试成功: {client_type}")
                # 如果测试成功，可以更新主分析器
                self.sentiment_analyzer.initialize(client_type, config)
                self.sentiment_analyzer_status['initialized'] = True
                # 通知GUI测试成功
                self._notify_gui_status_change(True, True)
            else:
                self.update_status(f"AI连接测试失败: {client_type}")
                self.sentiment_analyzer_status['initialized'] = False
                # 通知GUI测试失败
                self._notify_gui_status_change(False, False)
            return success
        except Exception as e:
            self.update_status(f"连接测试失败: {e}")
            self.sentiment_analyzer_status['initialized'] = False
            # 通知GUI测试失败
            self._notify_gui_status_change(False, False)
            return False

    def _get_emotion_by_sentiment(self, text: str) -> int:
        """根据文本情感获取对应的表情索引"""
        if not text.strip():
            return None
        
        if not self.sentiment_analyzer_status['initialized']:
            return None
    
        try:
            # 分析情感
            sentiment = self.sentiment_analyzer.analyze_sentiment(text)
            if not sentiment:
                return None
                
            current_character = self.get_character()
            character_meta = self.mahoshojo.get(current_character, {})
            
            # 查找对应情感的表情索引列表
            emotion_indices = character_meta.get(sentiment, [])
            if not emotion_indices:
                # 如果没有对应的情感，使用无感情表情
                emotion_indices = character_meta.get("无感情", [])
                if not emotion_indices:
                    return None
                
            # 随机选择一个表情索引
            if emotion_indices:
                import random
                return random.choice(emotion_indices)
            else:
                return None
                
        except Exception as e:
            self.update_status(f"情感分析失败: {e}")
            return None

    def _update_emotion_by_sentiment(self, text: str) -> bool:
        """根据文本情感更新表情，返回是否成功更新"""
        # 检查情感分析器是否已初始化
        if not self.sentiment_analyzer_status['initialized']:
            self.update_status("情感分析器未初始化，跳过情感分析")
            return False
            
        emotion_index = self._get_emotion_by_sentiment(text)
        if emotion_index:
            self.selected_emotion = emotion_index
            return True
        return False

    def load_configs(self):
        """加载所有配置"""
        self.mahoshojo = self.config_loader.load_chara_meta()
        self.character_list = list(self.mahoshojo.keys())
        self.text_configs_dict = self.config_loader.load_text_configs()
        self.keymap = self.config_loader.load_keymap(platform)
        self.process_whitelist = self.config_loader.load_process_whitelist()
        
    def reload_configs(self):
        """重新加载配置（用于热键更新后）"""
        # 重新加载快捷键映射
        self.keymap = self.config_loader.load_keymap(platform)
        # 重新加载进程白名单
        self.process_whitelist = self.config_loader.load_process_whitelist()
        # 重新加载GUI设置
        self.gui_settings = self.config_loader.load_gui_settings()
        self.update_status("配置已重新加载")

    def get_character(self, index: str | None = None, full_name: bool = False) -> str:
        """获取角色名称"""
        if index is not None:
            return self.mahoshojo[index]["full_name"] if full_name else index
        else:
            chara = self.character_list[self.current_character_index - 1]
            return self.mahoshojo[chara]["full_name"] if full_name else chara

    def switch_character(self, index: int) -> bool:
        """切换到指定索引的角色"""
        clear_cache("character")
        if 0 < index <= len(self.character_list):
            self.current_character_index = index
            character_name = self.get_character()
            # 预加载角色图片到内存
            self.image_processor.preload_character_images(character_name)
            return True
        return False

    def get_current_font(self) -> str:
        """返回当前角色的字体名称"""
        return self.image_processor.get_character_font(self.get_character())

    def get_current_emotion_count(self) -> int:
        """获取当前角色的表情数量"""
        return self.mahoshojo[self.get_character()]["emotion_count"]

    def get_character_list(self):
        """获取角色列表"""
        return self.character_list

    def get_character_name(self, index=None, full_name=False):
        """获取角色名称（兼容性方法）"""
        return self.get_character(index, full_name)

    def get_gui_settings(self):
        """获取GUI设置"""
        return self.gui_settings

    def save_gui_settings(self, settings):
        """保存GUI设置"""
        self.gui_settings = settings
        return self.config_loader.save_gui_settings(settings)

    def _get_random_emotion(self, emotion_count: int) -> int:
        """随机选择表情（避免连续相同）"""
        if self.last_emotion == -1:
            emotion_index = random.randint(1, emotion_count)
        else:
            # 避免连续相同表情
            available_emotions = [
                i for i in range(1, emotion_count + 1) if i != self.last_emotion
            ]
            emotion_index = (
                random.choice(available_emotions)
                if available_emotions
                else self.last_emotion
            )

        self.last_emotion = emotion_index
        return emotion_index

    def _active_process_allowed(self) -> bool:
        """校验当前前台进程是否在白名单"""
        if not self.process_whitelist:
            return True

        wl = {name.lower() for name in self.process_whitelist}

        if platform.startswith("win"):
            try:
                hwnd = win32gui.GetForegroundWindow()
                if not hwnd:
                    return False
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                name = psutil.Process(pid).name().lower()
                return name in wl
            except (psutil.Error, OSError):
                return False

        elif platform == "darwin":
            try:
                import subprocess

                result = subprocess.run(
                    [
                        "osascript",
                        "-e",
                        'tell application "System Events" to get name of first process whose frontmost is true',
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                name = result.stdout.strip().lower()
                return name in wl
            except subprocess.SubprocessError:
                return False

        else:
            # Linux 支持
            return True

    def cut_all_and_get_text(self) -> str:
        """模拟全选和剪切操作，返回剪切得到的文本内容"""
        self.clipboard_manager.copy_text_to_clipboard("")

        if platform == "darwin":
            self.kbd_controller.press(Key.cmd)
            self.kbd_controller.press("a")
            self.kbd_controller.release("a")
            self.kbd_controller.press("x")
            self.kbd_controller.release("x")
            self.kbd_controller.release(Key.cmd)
        elif platform.startswith("win"):
            kb_module.send("CTRL+A")
            kb_module.send("CTRL+X")

        # 增加重试机制来确保剪贴板中有内容
        new_clip = ""
        max_retries = 3
        for attempt in range(max_retries):
            time.sleep(self.config.KEY_DELAY)
            new_clip = self.clipboard_manager.get_text_from_clipboard()
            if new_clip.strip():
                break
            elif attempt < max_retries - 1:
                time.sleep(self.config.KEY_DELAY * (attempt + 1))

        return new_clip.strip()

    def generate_preview(self) -> tuple:
        """生成预览图片和相关信息"""
        character_name = self.get_character()
        emotion_count = self.get_current_emotion_count()

        # 确定表情和背景
        emotion_index = (
            self._get_random_emotion(emotion_count)
            if self.selected_emotion is None
            else self.selected_emotion
        )
        background_index = (
            self.image_processor.get_random_background()
            if self.selected_background is None
            else self.selected_background
        )

        # 保存预览使用的表情和背景
        self.preview_emotion = emotion_index
        self.preview_background = background_index

        # 生成预览图片
        preview_image = self.image_processor.generate_preview_image(
            character_name, background_index, emotion_index
        )

        # 构建预览信息 - 显示实际使用的索引值
        emotion_text = (
            f"{emotion_index}" if self.selected_emotion is None else f"{emotion_index}"
        )
        background_text = (
            f"{background_index}"
            if self.selected_background is None
            else f"{background_index}"
        )

        info = f"角色: {character_name}\n表情: {emotion_text}\n背景: {background_text}"

        return preview_image, info

    def generate_image(self) -> str:
        """生成并发送图片"""
        if not self._active_process_allowed():
            return "前台应用不在白名单内"

        character_name = self.get_character()
        base_msg=""

        # 开始计时
        start_time = time.time()
        print(f"[{int((time.time()-start_time)*1000)}] 开始生成图片")

        # 获取剪切板内容
        text = self.cut_all_and_get_text()
        image = self.clipboard_manager.get_image_from_clipboard()
        print(f"[{int((time.time()-start_time)*1000)}] 剪切板内容获取完成")

        # 情感匹配处理：仅当启用且只有文本内容时
        sentiment_settings = self.gui_settings.get("sentiment_matching", {})
        # selected_emotion_by_ai = None

        if (sentiment_settings.get("enabled", False) and 
            self.sentiment_analyzer_status['initialized'] and
            text.strip() and 
            image is None):
            
            self.update_status("正在分析文本情感...")
            emotion_updated = self._update_emotion_by_sentiment(text)
            
            if emotion_updated:
                self.update_status("情感分析完成，更新表情")
                print(f"[{int((time.time()-start_time)*1000)}] 情感分析完成")
                # 刷新预览以显示新的表情
                base_msg += f"情感: {self.sentiment_analyzer.selected_emotion}  "
                self.generate_preview()
                
            else:
                self.update_status("情感分析失败，使用默认表情")
                self.selected_emotion = None
                print(f"[{int((time.time()-start_time)*1000)}] 情感分析失败")

        if text == "" and image is None:
            return "错误: 没有文本或图像"

        try:
            # 使用GUI中设置的对话框字体，而不是角色专用字体
            font_file = None
            font_name=None
            font_family = self.gui_settings.get("font_family")
            font_size = self.gui_settings.get("font_size", 120)

           # 如果设置了字体家族，检测是否在可用字体列表中
            if font_family:
                # 获取可用字体列表（去掉后缀名的字体名称）
                font_files = get_available_fonts()
                for font_file in font_files:
                    if font_file and font_family == os.path.splitext(os.path.basename(font_file))[0]:
                        # 检查设置的字体家族是否在可用字体列表中
                        font_name = font_file
                        break
            #字体回退
            if font_name is None:
                print(f"字体家族 {font_family} 不在可用字体列表中")
                font_name = self.get_current_font()  # 使用角色专用字体名称

            # 获取文字颜色设置
            text_color_hex = self.gui_settings.get("text_color", "#FFFFFF")
            # 将十六进制颜色转换为RGB元组
            text_color = self.hex_to_rgb(text_color_hex)

            # 获取强调颜色设置
            bracket_color_hex = self.gui_settings.get("bracket_color", "#89B1FB")
            # 将十六进制颜色转换为RGB元组
            bracket_color = self.hex_to_rgb(bracket_color_hex)

            # 生成图片
            bmp_bytes = self.image_processor.generate_image_fast(
                character_name,
                text,
                image,
                font_name,  # 传递字体名称而非路径
                font_size,
                text_color,
                bracket_color,
                self.gui_settings.get("image_compression", {})
            )

            print(f"[{int((time.time()-start_time)*1000)}] 图片合成完成")

        except Exception as e:
            return f"生成图像失败: {e}"

        if bmp_bytes is None:
            return "生成图像失败！"

        # 复制到剪贴板
        if not self.clipboard_manager.copy_image_to_clipboard(bmp_bytes):
            return "复制到剪贴板失败"
        
        print(f"[{int((time.time()-start_time)*1000)}] 图片复制到剪切板完成")

        # 等待剪贴板确认（最多等待2.5秒）
        max_wait_time = 2.5
        wait_interval = 0.05

        while max_wait_time > 0:
            # 检查剪贴板中是否有图片
            if self.clipboard_manager.has_image_in_clipboard():
                break
            time.sleep(wait_interval)
            max_wait_time -= wait_interval

        print(f"[{int((time.time()-start_time)*1000)}] 剪切板确认完成")

        # 自动粘贴和发送
        if self.config.AUTO_PASTE_IMAGE:
            self.kbd_controller.press(Key.ctrl if platform != "darwin" else Key.cmd)
            self.kbd_controller.press("v")
            self.kbd_controller.release("v")
            self.kbd_controller.release(Key.ctrl if platform != "darwin" else Key.cmd)

            time.sleep(0.1)

            if self.config.AUTO_SEND_IMAGE:
                self.kbd_controller.press(Key.enter)
                self.kbd_controller.release(Key.enter)

                print(f"[{int((time.time()-start_time)*1000)}] 自动发送完成")
        
        # 计算总用时
        end_time = time.time()
        total_time_ms = int((end_time - start_time) * 1000)
        
        # 构建状态消息
        base_msg += f"角色: {character_name}, 表情: {self.preview_emotion}, 背景: {self.preview_background}, 用时: {total_time_ms}ms"
        
        return base_msg
    
    def set_status_callback(self, callback):
        """设置状态更新回调函数"""
        self.status_callback = callback

    def update_status(self, message: str):
        """更新状态（供外部调用）"""
        if self.status_callback:
            self.status_callback(message)

    def hex_to_rgb(self, hex_color: str) -> tuple:
        """将十六进制颜色转换为RGB元组"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))