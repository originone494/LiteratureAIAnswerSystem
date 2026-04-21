import base64
import glob
import re
import os
import markdown
from bs4 import BeautifulSoup

def find_image_file(filename):

    search_pattern = os.path.join("Files", "**", "images", filename)
    matches = glob.glob(search_pattern, recursive=True)
    if matches:
        return matches[0]

    return None


def convert_image_paths(content):
    # 正则匹配Markdown图片语法
    pattern = r'!\[([^\]]*)\]\(\s*(?:\./)?images/([^)]+\.(?:jpg|jpeg|png|gif))\s*\)'

    def replace_match(match):
        alt_text = match.group(1)
        filename = match.group(2)

        img_path = find_image_file(filename)



        if img_path:
            try:
                with open(img_path, "rb") as f:
                    img_bytes = f.read()
                    img_b64 = base64.b64encode(img_bytes).decode()
                # 根据文件扩展名确定MIME类型
                ext = filename.split('.')[-1].lower()
                mime_type = f"image/{ext}" if ext != 'jpg' else "image/jpeg"


                return f'![{alt_text}](data:{mime_type};base64,{img_b64})'
            except Exception as e:
                print(f"转换图片失败 {filename}: {e}")
                return match.group(0)  # 出错时保持原样
        else:
            # 图片文件不存在，保持原样
            return match.group(0)

    return re.sub(pattern, replace_match, content)

def md_to_plain_text_with_images(md_file_path):
    with open(md_file_path, 'r', encoding='utf-8') as file:
        md_content = file.read()
    
    # 获取文件所在目录路径
    file_dir = os.path.dirname(md_file_path)
    # 获取文献名称（从路径中提取）
    # 路径格式: ./Files/{文献名}/{文献名}/{文献名}.md
    path_parts = file_dir.split(os.sep)
    paper_name = path_parts[-2] if len(path_parts) >= 2 else ""
    
    # 替换相对图片路径为完整路径
    def replace_image_path(match):
        alt = match.group(1)
        img_path = match.group(2)
        # 构建完整的图片路径: /Files/{文献名}/{文献名}/images/{文件名}
        full_path = f"/Files/{paper_name}/{paper_name}/{img_path}"
        return f"![{alt}]({full_path})"
    
    # 匹配 Markdown 图片语法并替换路径
    pattern = r'!\[([^\]]*)\]\(\s*(?:\./)?images/([^)]+\.(?:jpg|jpeg|png|gif))\s*\)'
    md_content = re.sub(pattern, replace_image_path, md_content)
    
    # 转换为 HTML
    html = markdown.markdown(md_content)
    
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html, "html.parser")
    
    # 处理所有 <img> 标签，保留完整的 Markdown 格式
    for img in soup.find_all('img'):
        alt = img.get('alt', '无描述')
        src = img.get('src', '未知路径')
        # 保留完整的 Markdown 图片语法
        img_text = f"![{alt}]({src})"
        img.replace_with(img_text)
    
    # 提取纯文本（此时图片已被替换为 Markdown 文本）
    plain_text = soup.get_text()
    return plain_text


from PIL import Image

def resize_by_ratio(input_path, output_path, ratio):
    with Image.open(input_path) as img:
        # 原始宽高
        w, h = img.size
        # 新宽高（保持整数）
        new_w = int(w * ratio)
        new_h = int(h * ratio)
        # 使用高质量重采样方法
        resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        # 保存（可根据需要调整质量）
        resized_img.save(output_path)

def batch_resize_inplace(input_dir, ratio, extensions=('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(extensions):
            name, ext = os.path.splitext(filename)
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(input_dir, f"{name}{ext}")
            resize_by_ratio(input_path, output_path, ratio)
