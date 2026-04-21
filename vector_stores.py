from langchain_chroma import Chroma
import config_data
from langchain_core.vectorstores import VectorStoreRetriever
from typing import Optional, List


class VectorStoreService:
    def __init__(self, embedding , per_dir, collection_name=None):
        self.embedding = embedding
        if collection_name is None:
            collection_name = config_data.collection_name
        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embedding,
            persist_directory=per_dir
        )

    def get_retriever(self, selected_sources: Optional[List[str]] = None):
        """返回向量检索器，支持多种搜索策略和来源过滤
        
        Args:
            selected_sources: 可选的来源列表，如果提供则只检索这些来源的文档
        """
        # 如果指定了来源，使用纯相似度搜索并增加返回数量
        if selected_sources and len(selected_sources) > 0:
            search_kwargs = {
                "k": max(config_data.return_count_k, 5),  # 至少返回5个
                "filter": {"source": {"$in": selected_sources}}
            }
            search_type = "similarity"  # 纯相似度搜索，不设阈值
        else:
            # 根据配置选择搜索类型
            search_kwargs = {"k": config_data.return_count_k}
            search_type = config_data.search_type

            # 根据search_type设置不同的搜索参数
            if search_type == "similarity_score_threshold":
                search_kwargs["score_threshold"] = config_data.similarity_score_threshold
            elif search_type == "mmr":
                search_kwargs["fetch_k"] = config_data.fetch_k
                search_kwargs["lambda_mult"] = config_data.mmr_lambda_param

        # 创建检索器
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )
