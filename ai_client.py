"""AI客户端管理"""

import openai
from typing import Dict, Any, Optional

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
    
    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """获取可用模型配置"""
        # 这里可以从配置文件动态加载模型
        # 暂时返回默认配置
        return {
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