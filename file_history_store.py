import os
from typing import Sequence, List, Dict
import json
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_to_dict, messages_from_dict


def get_history(session_id, storage_path: str = "./chat_history"):
    return FileChatMessageHistory(session_id, storage_path)


def list_conversations(storage_path: str = "./chat_history") -> List[Dict[str, str]]:
    """列出所有对话会话

    Returns:
        List[Dict]: 每个对话的信息字典，包含session_id、title、created_time等
    """
    conversations = []

    # 确保目录存在
    os.makedirs(storage_path, exist_ok=True)

    # 遍历目录中的所有文件
    for filename in os.listdir(storage_path):
        # 跳过 .meta 文件
        if filename.endswith(".meta"):
            continue
            
        file_path = os.path.join(storage_path, filename)

        # 只处理文件，忽略目录
        if os.path.isfile(file_path):
            session_id = filename
            conversation_info = {
                "session_id": session_id,
                "title": _get_conversation_title(file_path),
                "created_time": _get_file_creation_time(file_path),
                "modified_time": _get_file_modification_time(file_path),
                "message_count": _get_message_count(file_path)
            }
            conversations.append(conversation_info)

    # 按修改时间倒序排列（最新的在前面）
    conversations.sort(key=lambda x: x["modified_time"], reverse=True)
    return conversations


def _get_conversation_metadata(file_path: str) -> Dict:
    """读取对话元数据文件"""
    meta_path = file_path + ".meta"
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_conversation_metadata(file_path: str, metadata: Dict) -> None:
    """保存对话元数据文件"""
    meta_path = file_path + ".meta"
    try:
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def set_conversation_title(session_id: str, title: str, storage_path: str = "./chat_history") -> None:
    """设置对话自定义标题"""
    file_path = os.path.join(storage_path, session_id)
    metadata = _get_conversation_metadata(file_path)
    metadata["title"] = title
    _save_conversation_metadata(file_path, metadata)


def get_selected_papers(session_id: str, storage_path: str = "./chat_history") -> List[str]:
    """获取会话选中的文献列表"""
    file_path = os.path.join(storage_path, session_id)
    metadata = _get_conversation_metadata(file_path)
    return metadata.get("selected_papers", [])


def set_selected_papers(session_id: str, selected_papers: List[str], storage_path: str = "./chat_history") -> None:
    """设置会话选中的文献列表"""
    file_path = os.path.join(storage_path, session_id)
    metadata = _get_conversation_metadata(file_path)
    metadata["selected_papers"] = selected_papers
    _save_conversation_metadata(file_path, metadata)


def delete_conversation(session_id: str, storage_path: str = "./chat_history") -> bool:
    """删除对话及其元数据文件"""
    file_path = os.path.join(storage_path, session_id)
    meta_path = file_path + ".meta"

    success = True

    # 删除主文件
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            success = False

    # 删除元数据文件
    if os.path.exists(meta_path):
        try:
            os.remove(meta_path)
        except Exception:
            success = False

    return success


def _get_conversation_title(file_path: str) -> str:
    """从对话文件中提取标题（优先使用元数据中的自定义标题）"""
    # 首先检查元数据中是否有自定义标题
    metadata = _get_conversation_metadata(file_path)
    custom_title = metadata.get("title")
    if custom_title:
        return custom_title

    # 如果没有自定义标题，使用原有逻辑提取
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            messages_data = json.load(f)

        if not messages_data:
            return "空对话"

        # 查找第一条人类消息
        for msg_data in messages_data:
            if msg_data.get("type") == "human":
                content = msg_data.get("data", {}).get("content", "")
                # 提取前30个字符作为标题
                if len(content) > 30:
                    return content[:30] + "..."
                return content if content else "无标题"

        return "新对话"
    except Exception:
        return "损坏的对话"


def _get_file_creation_time(file_path: str) -> str:
    """获取文件创建时间"""
    try:
        stat = os.stat(file_path)
        import time
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_ctime))
    except Exception:
        return "未知时间"


def _get_file_modification_time(file_path: str) -> str:
    """获取文件修改时间"""
    try:
        stat = os.stat(file_path)
        import time
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
    except Exception:
        return "未知时间"


def _get_message_count(file_path: str) -> int:
    """获取消息数量"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            messages_data = json.load(f)
        return len(messages_data)
    except Exception:
        return 0


class FileChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id, storage_path):
        self.session_id = session_id  # 会话id
        self.storage_path = storage_path  # 不同会话id的存储文件所在的文件夹路径

        # 完整的文件路径
        self.file_path = os.path.join(self.storage_path, self.session_id)

        if not self.file_path.endswith(".json"):
            self.file_path += ".json"

        # 确保文件夹是存在的
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        all_messages = list(self.messages)
        all_messages.extend(messages)

        new_messages = messages_to_dict(all_messages)

        print(f"[历史存储] 保存 {len(messages)} 条消息到会话 {self.session_id}")

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(new_messages, f)

    @property  # 将 messages 方法变成成员变量属性使用
    def messages(self) -> list[BaseMessage]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                messages_data = json.load(f)
                return messages_from_dict(messages_data)
        except FileNotFoundError:
            return []

    def clear(self) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump([], f)
