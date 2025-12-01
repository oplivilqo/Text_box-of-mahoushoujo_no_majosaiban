import openai
import time
import re
from typing import Optional, Dict, Any
from ai_client import AIClientManager  # 新增导入

class SentimentAnalyzer:
    def __init__(self):
        self.client_manager = AIClientManager()  # 使用客户端管理器
        self.is_initialized = False
        self.emotion_list = ["无感情", "愤怒", "嫌弃", "疑惑", "惊讶", "伤心", "害羞", "开心", "恐惧", "无语", "大笑"]
        
        self.selected_emotion = None #用来在generate_image里显示选择的表情

        # 更严格的规则提示词
        self.rule_prompt = """你是一个专门分析日常聊天文本的情感分析助手。你的任务是：分析用户输入文本的情感，并从以下11个选项中选择最匹配的一个：["无感情", "愤怒", "嫌弃", "疑惑", "惊讶", "伤心", "害羞", "开心", "恐惧", "无语", "大笑"]。

规则：
1. 只返回情感词汇，不要添加其他内容
2. 文本可能不构成完整句子，需要推测前后文
3. 如果确实无法判断，返回"无感情"

请严格按照这个格式回复，现在请回复"好的"以确认你理解了规则。"""
        
    def initialize(self, client_type: str, config: Dict[str, Any]) -> bool:
        """
        初始化函数 - 使用新的配置结构
        """
        try:
            # 使用客户端管理器初始化
            success = self.client_manager.initialize_client(client_type, config)
            
            if success:
                # 发送规则提示词
                response = self._send_request(self.rule_prompt)
                self.is_initialized = self._check_initialization_response(response)
                
                if self.is_initialized:
                    print(f"{client_type} 情感分析器初始化成功")
                else:
                    print(f"AI未正确确认规则，回复: {response}")
                
                return self.is_initialized
            else:
                print(f"{client_type} 客户端初始化失败")
                return False
                
        except Exception as e:
            print(f"初始化失败: {e}")
            self.is_initialized = False
            return False
    

    def _send_request(self, message: str) -> str:
        """发送请求到对应的API"""
        try:
            messages = [
                {"role": "system", "content": self.rule_prompt},
                {"role": "user", "content": message}
            ]

            # 获取模型配置
            models = self.client_manager.get_available_models()
            current_client = self.client_manager.current_client
            model_name = models[current_client]["model"] if current_client in models else "deepseek-chat"

            response = openai.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=10,
                stream=False
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"请求失败: {e}")
            raise
    
    # 其余方法保持不变，只是移除旧的初始化相关代码
    def _check_initialization_response(self, response: str) -> bool:
        """检查初始化回复是否成功"""
        confirmation_keywords = ['好的', '明白', '了解']
        response_lower = response.lower()
        
        for keyword in confirmation_keywords:
            if keyword in response_lower:
                return True
        return False
    
    def test_connection(self, client_type: str, config: Dict[str, Any]) -> bool:
        """测试连接"""
        try:
            return self.client_manager.initialize_client(client_type, config)
        except Exception as e:
            print(f"连接测试失败: {e}")
            return False
    

    def _extract_emotion(self, response: str) -> Optional[str]:
        """从AI回复中提取情感词汇"""
        # 清理回复文本
        cleaned_response = re.sub(r'[^\w\u4e00-\u9fff]', '', response)
        
        # 直接匹配情感词汇
        for emotion in self.emotion_list:
            if emotion in cleaned_response:
                return emotion
        
        return None
    
    def send_rule_and_detect(self) -> bool:
        """
        规则发送与检测函数
        """
        if not self.client_manager.current_client:
            print("未设置AI客户端，请先调用initialize函数")
            return False
            
        try:
            response = self._send_request("请确认你理解规则")
            success = self._check_initialization_response(response)
            
            if success:
                self.is_initialized = True
                print("规则发送成功，AI已确认")
            else:
                self.is_initialized = False
                print(f"规则发送失败，AI回复: {response}")
                
            return success
            
        except Exception as e:
            print(f"规则发送失败: {e}")
            self.is_initialized = False
            return False
    
    def switch_api(self, new_client_type: str, config: Dict[str, Any]) -> bool:
        """
        切换AI客户端
        """
        print(f"正在切换到 {new_client_type}")
        
        try:
            success = self.client_manager.initialize_client(new_client_type, config)
            
            if success:
                self.is_initialized = True
                print(f"成功切换到 {new_client_type}")
                return True
            else:
                print(f"切换到 {new_client_type} 失败")
                return False
                
        except Exception as e:
            print(f"切换过程中发生错误: {e}")
            return False
    
    def analyze_sentiment(self, text: str, max_retries: int = 2) -> Optional[str]:
        """
        情感检测函数
        """
        if not self.client_manager.current_client:
            print("未设置AI客户端，请先调用initialize函数")
            return None
        
        for attempt in range(max_retries + 1):
            try:
                response = self._send_request(text)
                print(f"AI原始回复: {response}")
                
                # 提取情感
                self.selected_emotion = self._extract_emotion(response)
                
                if self.selected_emotion:
                    return self.selected_emotion
                
                # 如果不在列表中，重新发送规则
                if attempt < max_retries:
                    print(f"无法从回复中提取有效情感，重新发送规则 (尝试 {attempt + 1}/{max_retries})")
                    self.send_rule_and_detect()
                    time.sleep(1)
                else:
                    print("达到最大重试次数，无法获得有效情感分析结果")
                    return None
                    
            except Exception as e:
                print(f"情感分析请求失败: {e}")
                if attempt < max_retries:
                    print(f"重试中... (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(1)
                else:
                    return None
        
        return None

    def test_connection(self, client_type: str, config: Dict[str, Any]) -> bool:
        """测试连接"""
        try:
            return self.client_manager.initialize_client(client_type, config)
        except Exception as e:
            print(f"连接测试失败: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        获取分析器状态
        """
        return {
            "current_client": self.client_manager.current_client,
            "is_initialized": self.is_initialized,
            "emotion_list": self.emotion_list
        }
    
# 使用示例
def main():
    analyzer = SentimentAnalyzer()
    
    # 初始化 DeepSeek
    # print("=== 初始化 DeepSeek ===")
    # deepseek_success = analyzer.initialize(
    #     api_type='deepseek',
    #     api_key='api_key',  # 替换为你的 API key
    #     base_url='https://api.deepseek.com',
    #     model='deepseek-chat'
    # )
    
    print("=== 初始化 qwen ===")
    deepseek_success = analyzer.initialize(
        api_type='ollama',
        api_key='api_key',  # 替换为你的 API key
        base_url='http://localhost:11434/v1/',
        model='qwen2.5'
    )
    if deepseek_success:
        test_texts = [
            "我草，你这个有点吊",
            "嘻嘻",
            "你什么意思！",
            "我喜欢你",
            "我不理解"
        ]
        
        for text in test_texts:
            result = analyzer.analyze_sentiment(text)
            print(f"文本: '{text}' -> 情感: {result}")
            print("-" * 50)

if __name__ == "__main__":
    main()