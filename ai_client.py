"""AI客户端管理"""

from typing import Dict, Any
import openai
import yaml
import os
from path_utils import get_resource_path

class AIClientManager:
    """AI客户端管理器"""
    
    def __init__(self):
        self.clients = {}
        self.current_client = None
        
    def initialize_client(self, client_type: str, config: Dict[str, Any]) -> bool:
        """初始化AI客户端"""
        try:
            if client_type == "ollama":
                openai.api_key = config.get("api_key", "ollama")
                openai.base_url = config.get("base_url", "http://localhost:11434/v1/")
                self.current_client = "ollama"
                
            elif client_type == "deepseek":
                openai.api_key = config.get("api_key", "")
                openai.base_url = config.get("base_url", "https://api.deepseek.com")
                self.current_client = "deepseek"
                
            else:
                return False
                
            # 测试连接
            return self.test_connection(config.get("model", ""))
            
        except Exception as e:
            print(f"初始化AI客户端失败: {e}")
            return False
    
    def test_connection(self, model_name: str) -> bool:
        """测试连接"""
        try:
            # 发送一个简单的测试请求
            response = openai.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return response.choices[0].message.content is not None
        except Exception as e:
            print(f"连接测试失败: {e}")
            return False
    
    def _load_config_from_file(self) -> Dict[str, Any]:
        """从配置文件加载配置"""
        config_path = get_resource_path(os.path.join("config", "settings.yml"))
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config or {}
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
    
    def _save_config_to_file(self, config: Dict[str, Any]) -> bool:
        """保存配置到文件"""
        config_path = get_resource_path(os.path.join("config", "settings.yml"))
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """获取可用模型配置"""
        # 从配置文件读取模型配置
        config = self._load_config_from_file()
        model_configs = config.get("sentiment_matching", {}).get("model_configs", {})
        
        # 构建模型信息字典
        available_models = {}
        model_descriptions = {
            "ollama": "本地运行的Ollama服务",
            "deepseek": "DeepSeek在线API", 
            "chatGPT": "OpenAI ChatGPT服务"
        }
        
        for model_type, model_config in model_configs.items():
            available_models[model_type] = {
                "name": model_type.capitalize(),
                "base_url": model_config.get("base_url", ""),
                "api_key": model_config.get("api_key", ""),
                "model": model_config.get("model", ""),
                "description": model_config.get("description", model_descriptions.get(model_type, f"{model_type} AI服务"))
            }
        
        # 如果没有从配置文件读取到模型，使用默认配置
        if not available_models:
            available_models = {
                "ollama": {
                    "name": "Ollama",
                    "base_url": "http://localhost:11434/v1/",
                    "api_key": "",
                    "model": "qwen2.5",
                    "description": "本地运行的Ollama服务"
                },
                "deepseek": {
                    "name": "DeepSeek",
                    "base_url": "https://api.deepseek.com", 
                    "api_key": "",
                    "model": "deepseek-chat",
                    "description": "DeepSeek在线API"
                }
            }
        
        return available_models