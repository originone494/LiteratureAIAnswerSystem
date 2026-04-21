import openai
from deepeval.models.base_model import DeepEvalBaseLLM

import config_data


class Tongyi(DeepEvalBaseLLM):
    """用于 DeepEval 评估的阿里云百炼平台通义千问模型自定义类"""
    def __init__(self):
        # 初始化模型名称和 API 密钥
        self.model_name = config_data.chat_model_name
        self.api_key = config_data.api_key
        # 配置 OpenAI 客户端，使其指向阿里云百炼平台的兼容端点
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=config_data.api_url
        )

    def load_model(self):
        """此方法需返回模型对象。对于 API 调用，通常返回客户端实例本身。"""
        return self.client

    def generate(self, prompt: str) -> str:
        """同步生成方法。核心是调用模型 API 并提取纯文本响应。"""
        chat_model = self.load_model()
        try:
            response = chat_model.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            # 提取模型返回的文本内容
            return response.choices[0].message.content
        except Exception as e:
            print(f"调用模型时发生错误：{e}")
            return ""

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self):
        return config_data.chat_model_name