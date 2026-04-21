from typing import List
from openai import OpenAI
from deepeval.models.base_model import DeepEvalBaseEmbeddingModel
import config_data

class DashScopeEmbeddingModel(DeepEvalBaseEmbeddingModel):
    """DeepEval 自定义嵌入模型 - 阿里云百炼 text-embedding-v4"""
    def __init__(self, dimensions: int = 1024):
        # 初始化 OpenAI 客户端，指向阿里云百炼的兼容端点
        self.client = OpenAI(
            api_key= config_data.api_key,
            base_url=config_data.api_url
        )
        self.model_name = config_data.embedding_model_name
        self.dimensions = dimensions

    def load_model(self):
        """返回模型客户端实例"""
        return self.client

    def embed_text(self, text: str) -> List[float]:
        """生成单个文本的向量"""
        response = self.client.embeddings.create(
            model=self.model_name,
            input=text,
            dimensions=self.dimensions,  # 指定向量维度
            encoding_format="float"
        )
        return response.data[0].embedding

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量生成多个文本的向量，提高效率"""
        response = self.client.embeddings.create(
            model=self.model_name,
            input=texts,
            dimensions=self.dimensions,  # 指定向量维度
            encoding_format="float"
        )
        return [item.embedding for item in response.data]

    async def a_embed_text(self, text: str) -> List[float]:
        """异步生成单个文本的向量"""
        return self.embed_text(text)

    async def a_embed_texts(self, texts: List[str]) -> List[List[float]]:
        """异步批量生成多个文本的向量"""
        return self.embed_texts(texts)

    def get_model_name(self):
        """返回模型名称"""
        return f"DashScope-{self.model_name}"