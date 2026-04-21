from flask import Flask, jsonify, request, send_from_directory
import os
import uuid
import config_data
from knowledge_base import KnowledgeBaseService
from pdf_preprocessor import pdf_preprocess
import shutil
from werkzeug.utils import secure_filename
from rag import RagService
from file_history_store import (
    get_history, 
    list_conversations, 
    set_selected_papers, 
    get_selected_papers,
    delete_conversation,
    set_conversation_title
)
from langchain_core.messages import HumanMessage, AIMessage

app = Flask(__name__)

# 配置
UPLOAD_FOLDER = 'Files'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 确保上传文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 服务初始化
_rag_service = None
_kb_service = None

def get_rag_service():
    global _rag_service
    if _rag_service is None:
        _rag_service = RagService(config_data.persist_dir)
    return _rag_service

def get_kb_service():
    global _kb_service
    if _kb_service is None:
        _kb_service = KnowledgeBaseService(name=config_data.collection_name, dir=config_data.persist_dir)
    return _kb_service

# 检查文件类型
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API 路由
@app.route('/')
def index():
    return send_from_directory('.', 'chat.html')

@app.route('/chat')
def chat_page():
    return send_from_directory('.', 'chat.html')

@app.route('/kb')
def kb_page():
    return send_from_directory('.', 'knowledge_base.html')

# 静态文件服务 - 提供图片访问
@app.route('/Files/<path:filename>')
def serve_files(filename):
    return send_from_directory('Files', filename)

# 查找图片API - 根据文件名查找图片路径
@app.route('/api/find-image/<filename>')
def find_image(filename):
    import glob
    try:
        # 在 Files 目录下递归搜索图片
        search_pattern = os.path.join("Files", "**", "images", filename)
        matches = glob.glob(search_pattern, recursive=True)
        
        if matches:
            # 找到匹配的图片，返回相对路径
            img_path = matches[0]
            # 将 Windows 路径分隔符转换为 URL 风格
            img_path = img_path.replace(os.sep, '/')
            # 返回相对于根目录的路径
            return jsonify({
                'success': True,
                'path': '/' + img_path
            })
        else:
            return jsonify({
                'success': False,
                'error': '未找到图片'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ================== 文献管理 API ==================
@app.route('/api/papers', methods=['GET'])
def get_papers():
    try:
        service = get_kb_service()
        papers = service.get_all_documents()
        return jsonify({
            'success': True,
            'papers': papers
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/upload', methods=['POST'])
def upload_paper():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有文件'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '只支持 PDF 文件'}), 400
        
        # 保存文件
        filename = secure_filename(file.filename)
        name_without_ext = os.path.splitext(filename)[0]
        file_dir = os.path.join(app.config['UPLOAD_FOLDER'], name_without_ext)
        os.makedirs(file_dir, exist_ok=True)
        
        file_path = os.path.join(file_dir, filename)
        file.save(file_path)
        
        # 预处理 PDF
        content, metadata = pdf_preprocess(name_without_ext)
        
        # 载入知识库
        service = get_kb_service()
        result = service.upload_by_str(content, name_without_ext, metadata)
        
        return jsonify({
            'success': True,
            'message': result,
            'paper_name': name_without_ext
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/delete/<paper_name>', methods=['DELETE'])
def delete_paper(paper_name):
    try:
        service = get_kb_service()
        success, num_deleted = service.delete_documents_by_source(paper_name)
        
        if success:
            # 删除文件系统中的文件
            file_dir = os.path.join(app.config['UPLOAD_FOLDER'], paper_name)
            if os.path.exists(file_dir):
                shutil.rmtree(file_dir)
            
            return jsonify({
                'success': True,
                'message': f'成功删除，共删除 {num_deleted} 个文本块'
            })
        else:
            return jsonify({
                'success': False,
                'error': '删除失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/paper/<paper_name>', methods=['GET'])
def get_paper_detail(paper_name):
    try:
        service = get_kb_service()
        papers = service.get_all_documents()
        
        if paper_name in papers:
            return jsonify({
                'success': True,
                'paper': papers[paper_name]
            })
        else:
            return jsonify({
                'success': False,
                'error': '文献不存在'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ================== 聊天 API ==================
@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    try:
        conversations = list_conversations()
        return jsonify({
            'success': True,
            'conversations': conversations
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversation/<session_id>', methods=['GET'])
def get_conversation(session_id):
    try:
        history = get_history(session_id)
        messages = []
        for msg in history.messages:
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})
            
        
        selected_papers = get_selected_papers(session_id)
        
        return jsonify({
            'success': True,
            'messages': messages,
            'selected_papers': selected_papers
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversation/new', methods=['POST'])
def create_new_conversation():
    try:
        new_session_id = str(uuid.uuid4())
        history = get_history(new_session_id)
        history.add_messages([AIMessage(content="你好，有什么可以帮助你？")])
        
        return jsonify({
            'success': True,
            'session_id': new_session_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversation/<session_id>/delete', methods=['DELETE'])
def delete_conversation_api(session_id):
    try:
        success = delete_conversation(session_id)
        return jsonify({
            'success': success
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversation/<session_id>/selected_papers', methods=['GET'])
def get_selected_papers_api(session_id):
    try:
        selected_papers = get_selected_papers(session_id)
        return jsonify({
            'success': True,
            'selected_papers': selected_papers
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversation/<session_id>/selected_papers', methods=['PUT'])
def set_selected_papers_api(session_id):
    try:
        data = request.get_json()
        selected_papers = data.get('selected_papers', [])
        set_selected_papers(session_id, selected_papers)
        
        return jsonify({
            'success': True
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        user_message = data.get('message')
        
        if not session_id or not user_message:
            return jsonify({
            'success': False,
            'error': 'session_id 和 message 是必填'
        }), 400
        
        selected_papers = get_selected_papers(session_id)
        
        # 1. 获取 RAG 服务
        rag_service = get_rag_service()
        if selected_papers and len(selected_papers) > 0:
            chain = rag_service.get_chain_for_session(selected_sources=selected_papers)
        else:
            chain = rag_service.get_chain_for_session()
        
        # 2. 配置
        session_config = {
            'configurable': {
                'session_id': session_id
            }
        }
        
        # 3. 调用 RAG 链
        ai_response = chain.invoke({'input': user_message}, session_config)
        
        # 4. 获取完整对话历史
        history = get_history(session_id)
        messages = []
        for msg in history.messages:
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'messages': messages
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)
