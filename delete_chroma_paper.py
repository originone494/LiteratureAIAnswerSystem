import chromadb

import config_data

client = chromadb.PersistentClient(config_data.persist_dir)
collection = client.get_collection(config_data.collection_name)

# 方法一：精确匹配 metadata 中的某个字段
collection.delete(where={"source": "Benchmarking Large Language Models in Retrieval-Augmented Generation.pdf"})