import config_data
from file_history_store import list_conversations, get_history, get_selected_papers, set_selected_papers
from langchain_core.messages import HumanMessage, AIMessage
import streamlit as st
from streamlit import session_state
from rag import RagService
import uuid
from Tool import convert_image_paths
from knowledge_base import KnowledgeBaseService

st.set_page_config(page_title="智能问答系统", layout="wide")


def load_conversations():
    """加载对话列表到session_state"""
    if "conversations" not in session_state:
        session_state.conversations = []

    # 从文件系统加载对话
    conversations = list_conversations()
    session_state.conversations = conversations

    # 如果还没有当前对话，选择第一个或创建新的
    if "current_session_id" not in session_state:
        if conversations:
            session_state.current_session_id = conversations[0]["session_id"]
        else:
            # 创建新对话
            new_session_id = str(uuid.uuid4())
            session_state.current_session_id = new_session_id
            # 创建一个空的历史文件
            history_store = get_history(new_session_id)
            # 添加初始消息
            history_store.add_messages([
                AIMessage(content="你好，有什么可以帮助你？")
            ])
            # 重新加载对话列表
            session_state.conversations = list_conversations()


def load_current_conversation_messages():
    """加载当前对话的消息到session_state.messages中（用于显示）"""
    if "current_session_id" not in session_state:
        load_conversations()

    session_id = session_state.current_session_id
    history_store = get_history(session_id)

    # 将BaseMessage转换为显示格式
    display_messages = []
    for msg in history_store.messages:
        if isinstance(msg, HumanMessage):
            display_messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            display_messages.append({"role": "assistant", "content": msg.content})
        else:
            pass

    # 如果对话为空，添加默认欢迎消息
    if not display_messages:
        display_messages.append({"role": "assistant", "content": "你好，有什么可以帮助你？"})

    session_state.messages = display_messages


def switch_conversation(session_id):
    """切换到指定对话"""
    session_state.current_session_id = session_id
    load_current_conversation_messages()
    # 清除可能的输入缓存
    if "input_processed" in session_state:
        del session_state.input_processed


def create_new_conversation():
    """创建新对话并切换到它"""
    new_session_id = str(uuid.uuid4())

    # 创建新对话文件
    history_store = get_history(new_session_id)
    # 添加欢迎消息
    history_store.add_messages([
        AIMessage(content="你好，有什么可以帮助你？")
    ])

    # 切换到新对话
    switch_conversation(new_session_id)
    # 重新加载对话列表
    session_state.conversations = list_conversations()


# 初始化服务
if "rag" not in session_state:
    session_state.rag = RagService(config_data.persist_dir)

if "kb_service" not in session_state:
    session_state.kb_service = KnowledgeBaseService(name=config_data.collection_name, dir=config_data.persist_dir)

# 加载对话
load_conversations()
load_current_conversation_messages()

with st.sidebar:
    if st.button("New Chat", icon="➕️"):
        create_new_conversation()
        st.rerun()

    # 对话列表
    if not session_state.conversations:
        st.caption("暂无历史对话")
    else:
        for conv in session_state.conversations:
            session_id = conv["session_id"]
            title = conv["title"]
            is_current = session_id == session_state.current_session_id

            with st.container():
                display_title = title
                if len(display_title) > 14:
                    display_title = display_title[:14] + "..."

                label = f" {display_title}"

                if is_current:
                    label = f"▶ **{display_title}**"

                if st.button(
                        label,
                        key=f"conv_{session_id}",
                        use_container_width=True,

                ):
                    if not is_current:
                        switch_conversation(session_id)
                        st.rerun()

# 主界面 - 三列布局
left_col, main_col, right_col = st.columns([1, 3, 1.5])

with left_col:
    # 左侧已经在sidebar里了，这里留空
    pass

with main_col:
    # 中间：聊天区域
    st.header("智能问答系统")
    
    # 显示当前会话使用的文献
    current_session_id = session_state.current_session_id
    selected_papers = get_selected_papers(current_session_id)
    if selected_papers:
        st.info(f"📚 当前会话使用 {len(selected_papers)} 篇文献进行问答")
    else:
        st.info("📚 当前会话使用所有文献进行问答")
    
    st.divider()
    
    # 显示当前对话的消息
    for message in session_state.messages:
        st.chat_message(message["role"]).markdown(convert_image_paths(message["content"]), unsafe_allow_html=True)

# 在页面最下方提供用户输入栏（需要放在columns外面）
prompt = st.chat_input()

with right_col:
    # 右侧：文献选择区域
    st.subheader("📚 选择文献")
    
    # 获取当前会话选中的文献
    current_session_id = session_state.current_session_id
    selected_papers = get_selected_papers(current_session_id)
    
    # 获取所有可用文献
    papers = session_state.kb_service.get_all_documents()
    
    if papers:
        # 创建文献选择的checkbox
        paper_options = list(papers.keys())
        
        # 显示当前选中的文献
        if selected_papers:
            st.caption(f"已选择 {len(selected_papers)} 篇文献")
        else:
            st.caption("未选择文献，将使用所有文献")
        
        # 全选/取消全选
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("全选", key="select_all"):
                set_selected_papers(current_session_id, paper_options)
                st.rerun()
        with col2:
            if st.button("取消全选", key="deselect_all"):
                set_selected_papers(current_session_id, [])
                st.rerun()
        
        st.divider()
        
        # 文献列表
        for paper_name in paper_options:
            paper_info = papers[paper_name]
            paper_meta = paper_info.get("metadata", {})
            display_title = paper_meta.get("title") or paper_name
            is_selected = paper_name in selected_papers
            
            if st.checkbox(
                display_title,
                key=f"paper_{paper_name}",
                value=is_selected
            ):
                if not is_selected:
                    # 添加到选中列表
                    new_selected = selected_papers.copy()
                    new_selected.append(paper_name)
                    set_selected_papers(current_session_id, new_selected)
                    st.rerun()
            else:
                if is_selected:
                    # 从选中列表中移除
                    new_selected = [p for p in selected_papers if p != paper_name]
                    set_selected_papers(current_session_id, new_selected)
                    st.rerun()
    else:
        st.info("知识库中暂无文献")

# 处理用户输入（放在columns外面，因为chat_input需要在columns外部
if prompt:
    # 获取当前对话的历史存储
    current_session_id = session_state.current_session_id
    
    # 获取当前会话选中的文献
    selected_papers = get_selected_papers(current_session_id)

    # 1. 立即显示用户消息
    st.chat_message("user").write(prompt)

    # 2. 调用RAG获取回答
    ai_res_list = []
    with st.spinner("思考中..."):
        session_config = {
            "configurable": {
                "session_id": current_session_id
            }
        }
        
        # 获取当前会话的chain，传入选中的文献
        if selected_papers and len(selected_papers) > 0:
            chain = session_state.rag.get_chain_for_session(selected_sources=selected_papers)
        else:
            # 如果没有选中文献，使用默认chain（全库）
            chain = session_state.rag.get_chain_for_session()
        
        # RunnableWithMessageHistory会自动管理历史记录
        # 它会将用户输入和AI响应都保存到历史存储中
        res_stream = chain.stream({"input": prompt}, session_config)


        def capture(generator, cache_list):
            for chunk in generator:
                cache_list.append(chunk)
                yield chunk


        # 3. 流式显示AI回答
        answer = capture(res_stream, ai_res_list)
        st.chat_message("assistant").write_stream(answer)

    # 4. 重新加载当前对话消息（从文件加载所有消息，包括刚刚保存的用户消息和AI消息）
    load_current_conversation_messages()

    # 5. 重新加载对话列表（更新消息数量等）
    session_state.conversations = list_conversations()

    # 6. 触发重新渲染，让页面顶部的消息循环显示更新后的session_state.messages
    st.rerun()
