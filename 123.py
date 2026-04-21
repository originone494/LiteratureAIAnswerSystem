import streamlit as st

# 文件上传部分
st.header("📤 上传文献")

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

upload_file = st.file_uploader(
    "请上传PDF文件",
    type=['pdf'],
    accept_multiple_files=False,  # 仅接受一个文件
    key=f"uploader_{st.session_state['uploader_key']}"
)