from deepeval.test_case import LLMTestCase
from deepeval.metrics import ContextualRelevancyMetric, ContextualRecallMetric, ContextualPrecisionMetric
from deepeval import evaluate
from rag import RagService
import config_data
import pandas as pd
from chat_tongyi_deepval import Tongyi
from deepeval.evaluate.configs import CacheConfig

import os
os.environ["DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE"] = "300"
os.environ["DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE"] = "120"

single = False

#single = True

if single:
    df = pd.read_excel("./data/QA.xlsx")
    sample_df = df.sample(n=min(1, len(df)))
    gold_answer = sample_df["Answer"].astype(str).iloc[0]
    question = sample_df["Question"].astype(str).iloc[0]

    # 初始化模型和指标
    model = Tongyi()
    relevancy = ContextualRelevancyMetric(model=model)
    recall = ContextualRecallMetric(model=model)
    precision = ContextualPrecisionMetric(model=model)

    # 初始化 RAG 服务
    rag = RagService(collection_name=config_data.collection_name, per_dir=config_data.persist_dir)

    # 检索和生成
    retrieved_docs = rag.vector_service.get_retriever().invoke(input=question)
    retrieval_contexts = [doc.page_content for doc in retrieved_docs]
    response = rag.test_chain.invoke({"input": question})

    # 构建单个测试用例
    test_case = LLMTestCase(
        input=question,
        actual_output=str(response),
        retrieval_context=retrieval_contexts,
        expected_output=gold_answer  # 用于某些需要参考答案的指标
    )

    cache_config = CacheConfig(use_cache=True, write_cache=True)

    # 评估
    results = evaluate([test_case], [relevancy, recall, precision],cache_config=cache_config )
    print(results)

    print("\n问题：")
    print(question)
    print("\n回答：")
    print(response)
    print("\n上下文：")
    print(retrieval_contexts)
    print("\n标准回答：")
    print(gold_answer)
else:
    df = pd.read_excel("./data/QA.xlsx")

    test_cases = []

    # 初始化模型和指标
    model = Tongyi()
    relevancy = ContextualRelevancyMetric(model=model)
    recall = ContextualRecallMetric(model=model)
    precision = ContextualPrecisionMetric(model=model)

    # 初始化 RAG 服务
    rag = RagService(collection_name=config_data.collection_name, per_dir=config_data.persist_dir)

    for idx, row in df.iterrows():
        question = str(row["Question"])
        gold_answer = str(row["Answer"])

        # 检索和生成
        retrieved_docs = rag.vector_service.get_retriever().invoke(input=question)
        retrieval_contexts = [doc.page_content for doc in retrieved_docs]
        response = rag.test_chain.invoke({"input": question})

        # 构建单个测试用例
        test_case = LLMTestCase(
            input=question,
            actual_output=str(response),
            retrieval_context=retrieval_contexts,
            expected_output=gold_answer  # 用于某些需要参考答案的指标
        )

        test_cases.append(test_case)

    cache_config = CacheConfig(use_cache=True, write_cache=True)

    # 评估
    results = evaluate(test_cases, [relevancy, recall, precision],cache_config=cache_config)
    print(results)
