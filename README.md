# 科技文献智能问答系统

基于大语言模型和 RAG 技术的科技文献问答系统

## 功能特性

- 📚 **知识库管理**：文献上传、查看、删除
- 💬 **智能问答**：基于 RAG 技术的文献问答
- 📋 **会话管理**：对话历史保存和管理
- 🎯 **文献选择**：会话级别的文献选择
- 🎨 **现代化界面**：美观的 Web 界面设计

## 快速开始

### 1. 启动服务

**Windows 用户**：双击运行 `start.bat`

**其他系统**：

```bash
python api.py
```

### 2. 访问界面

服务启动后，在浏览器中访问：

- **聊天界面**：http://localhost:5000
- **知识库管理**：http://localhost:5000/kb

## 使用说明

### 添加文献

1. 访问知识库管理页面
2. 点击上传区域或拖拽 PDF 文件
3. 系统自动解析文献元数据和内容
4. 文献添加到向量数据库

### 问答对话

1. 访问聊天界面
2. 点击「新建对话」开始新对话
3. 在右侧选择要用于问答的文献（可选）
4. 点击「保存选择」（如果选了文献）
5. 在输入框中输入问题并发送
6. AI 根据选中的文献回答问题

## 技术架构

- **后端**：Flask
- **LLM**：通义千问
- **向量数据库**：Chroma
- **前端**：HTML + Tailwind CSS + JavaScript
- **RAG**：LangChain

## 项目结构

```
.
├── api.py                    # Flask 后端 API
├── chat.html                 # 聊天界面
├── knowledge_base.html       # 知识库界面
├── start.bat                 # Windows 启动脚本
├── rag.py                    # RAG 服务
├── knowledge_base.py         # 知识库服务
├── file_history_store.py     # 对话历史存储
├── pdf_preprocessor.py       # PDF 解析
├── vector_stores.py          # 向量存储
├── pages/                    # Streamlit 页面（可选）
│   └── KnowledgeBase.py
├── Files/                    # 上传的文献存储
└── chat_history/             # 对话历史存储
```

## Streamlit 版本（可选）

项目仍然保留原有的 Streamlit 版本：

```bash
streamlit run app.py
```
