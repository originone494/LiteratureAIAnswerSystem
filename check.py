from knowledge_base import KnowledgeBaseService
import config_data


service = KnowledgeBaseService(name=config_data.evaluate_collection_name,dir=config_data.evaluate_dir)

all_data = service.chroma.get()


# 查看文档总数
total_count = len(all_data.get('ids', []))
print(f"向量库中的文档块总数: {total_count}")

# 查看所有文档的原始文本
for chunk in all_data.get('documents'):
    print(chunk)
    print("\n")
