import streamlit as st
import subprocess
import threading
import time
import requests
import os

st.set_page_config(page_title="知识库管理", layout="wide")

# 启动 Flask 后端
def start_flask():
    try:
        # 检查是否已在运行
        requests.get("http://localhost:5000/", timeout=1)
        return True
    except:
        pass
    
    # 启动 Flask
    try:
        subprocess.Popen(
            ["python", "api.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # 等待启动
        time.sleep(3)
        return True
    except Exception as e:
        st.error(f"启动后端失败: {e}")
        return False

# 页面标题
st.title("📚 知识库管理系统")

# 说明
st.markdown("""
### 新架构介绍

我们已经采用了前后端分离的架构：
- **后端**: Flask API（运行在 http://localhost:5000）
- **前端**: 现代化的 HTML/JS 界面

### 使用方法

1. **方式一（推荐）**: 直接在浏览器中访问 http://localhost:5000
2. **方式二**: 使用下方的内嵌界面
""")

st.divider()

# 启动按钮
if st.button("🚀 启动知识库界面", type="primary"):
    with st.spinner("正在启动后端服务..."):
        success = start_flask()
        
        if success:
            st.success("✅ 后端服务已启动！")
            st.info("💡 建议直接访问 http://localhost:5000 获得更好的体验")
        else:
            st.error("❌ 启动失败")

st.divider()

# 内嵌页面（可选）
try:
    # 检查是否可访问
    requests.get("http://localhost:5000/", timeout=2)
    
    st.subheader("内嵌界面")
    st.caption("如需更好的体验，请直接访问 http://localhost:5000")
    
    # 使用 iframe 嵌入
    st.components.v1.iframe(
        "http://localhost:5000",
        height=800,
        scrolling=True
    )
except:
    st.warning("⚠️ 后端服务未运行，请先点击上方的启动按钮")
