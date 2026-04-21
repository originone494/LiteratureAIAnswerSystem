import streamlit as st

st.set_page_config(page_title="文献管理系统", layout="wide")

page_chat = st.Page("pages/chat.py", title="交流界面", default=True)
page_knowledgebase = st.Page("pages/KnowledgeBase.py", title="知识库管理")

pg = st.navigation([page_chat, page_knowledgebase])
pg.run()
