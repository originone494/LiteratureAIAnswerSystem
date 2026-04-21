import os
import json
from langchain_chroma import Chroma
import config_data
import hashlib
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime
import os
from typing import Set

def check_md5(md5_str: str):
    """检查传入的md5字符串是否处理过"""
    if not os.path.exists(config_data.md5_path):
        open(config_data.md5_path, 'w', encoding='utf-8').close()
        return False
    else:
        for line in open(config_data.md5_path, 'r', encoding='utf-8').readlines():
            line = line.strip()
            if line == md5_str:
                return True
        return False


def save_md5(md5_str: str):
    with open(config_data.md5_path, 'a', encoding='utf-8') as f:
        f.write(md5_str + '\n')


def get_string_md5(input_str: str, encoding='utf-8'):
    # 将字符串转换为字节数组
    str_bytes = input_str.encode(encoding)
    md5_obj = hashlib.md5()
    md5_obj.update(str_bytes)
    md5_hex = md5_obj.hexdigest()
    return md5_hex


def get_metadata_from_file(filename):
    """从文件系统加载元数据"""
    metadata_file = f"./Files/{filename}/metadata.json"
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


class KnowledgeBaseService(object):
    def __init__(self , name, dir):
        os.makedirs(dir, exist_ok=True)
        self.chroma = Chroma(
            collection_name=name,
            embedding_function=DashScopeEmbeddings(model=config_data.embedding_model_name,
                                                   dashscope_api_key=config_data.api_key),
            persist_directory=dir,
        )  # 向量库存储的实例 chroma 向量库对象
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=config_data.chunk_size,
            chunk_overlap=config_data.chunk_overlap,
            separators=config_data.separators,
            length_function=len
        )  # 文本分割器的对象

    def upload_by_str(self, data, filename, paper_metadata=None):
        """将传入的字符串进行向量化，存入向量数据库中"""

        # 先得到传入字符串的 md5 值
        md5_hex = get_string_md5(data)

        if check_md5(md5_hex):
            return "内容已经存在知识库中"

        primary_separator = "=+=+=+=+=+=+=+=+="
        if primary_separator in data:
            primary_chunks = data.split(primary_separator)
            primary_chunks = [chunk.strip() for chunk in primary_chunks if chunk.strip()]
        else:
            primary_chunks = [data]

        # 对每个一级分割块，如果仍超过阈值，用spliter进一步分割
        knowledge_chunks = []
        for chunk in primary_chunks:
            if len(chunk) > config_data.max_split_char_number:
                # 使用spliter进行二级分割（针对长文本）
                sub_chunks = self.spliter.split_text(chunk)
                knowledge_chunks.extend(sub_chunks)
            else:
                knowledge_chunks.append(chunk)



        # 3. 为每个文本块生成元数据
        metadatas = []
        for i, chunk in enumerate(knowledge_chunks):
            metadata = {
                "source": filename, #来源文献
                "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),#生成时间
                "operator": "",
                "chunk_index": i,  # 记录块索引
                "total_chunks": len(knowledge_chunks),  # 总块数
                "chunk_length": len(chunk)  # 块长度
            }
            metadatas.append(metadata)

        # 4. 将分割后的文本块和元数据存入向量数据库
        self.chroma.add_texts(
            knowledge_chunks,
            metadatas=metadatas,
        )

        save_md5(md5_hex)

        return f"内容已成功载入向量库，共分割为 {len(knowledge_chunks)} 个文本块"

    def get_all_documents(self):
        """获取向量库中所有文档的元数据信息，按论文（source）分组"""
        try:
            # 获取Chroma集合中的所有文档
            collection = self.chroma._collection
            if collection is None:
                return {}

            # 获取所有文档的ID、元数据和内容
            results = collection.get(include=["metadatas", "documents"])

            if not results or not results.get("ids"):
                return {}

            # 按source（论文）分组
            papers = {}
            for doc_id, metadata, content in zip(results["ids"], results["metadatas"], results["documents"]):
                source = metadata.get("source", "未知来源")
                if source not in papers:
                    # 从文件系统加载文献元数据
                    paper_metadata = get_metadata_from_file(source)
                    papers[source] = {
                        "chunks": [],
                        "total_chunks": 0,
                        "create_time": metadata.get("create_time", "未知时间"),
                        "operator": metadata.get("operator", ""),
                        "metadata": paper_metadata  # 添加文献元数据
                    }

                papers[source]["chunks"].append({
                    "id": doc_id,
                    "content": content,
                    "metadata": metadata
                })
                papers[source]["total_chunks"] = len(papers[source]["chunks"])

            return papers
        except Exception as e:
            print(f"获取文档列表失败: {e}")
            return {}
    
    def delete_documents_by_source(self, source):
        """删除指定来源的所有文档"""
        try:
            collection = self.chroma._collection
            if collection is None:
                return False
            
            # 获取指定来源的所有文档ID
            results = collection.get(include=["metadatas"])
            ids_to_delete = []
            for doc_id, metadata in zip(results["ids"], results["metadatas"]):
                if metadata.get("source") == source:
                    ids_to_delete.append(doc_id)
            
            if ids_to_delete:
                # 删除这些文档
                collection.delete(ids=ids_to_delete)
                return True, len(ids_to_delete)
            return True, 0
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False, 0
    
    def delete_file_history(self, file_path):
        """删除历史记录中的某个文件"""
        if os.path.exists(config_data.md5_path):
            # 读取所有历史记录
            try:
                with open(config_data.md5_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 过滤掉我们不需要的内容（这里比较简单，因为我们没有保存文件路径，只保存了md5）
                # 所以这里我们暂时保留原样，或者考虑更完善的方案
                # 暂时只删除向量库中的内容和文件系统中的文件
            except Exception as e:
                print(f"更新历史记录失败: {e}")

