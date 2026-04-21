from pdfdeal import Doc2X
from pdfdeal.file_tools import get_files, unzips, auto_split_md
import config_data
import os
import re
import json
from Tool import md_to_plain_text_with_images,batch_resize_inplace

def extract_metadata_from_markdown(md_content):
    metadata = {
        "title": "",
        "authors": [],
        "abstract": "",
        "keywords": [],
        "article_id": "",
        "doi": "",
        "journal": "",
        "received_date": "",
        "revised_date": "",
        "accepted_date": "",
        "fund": ""
    }
    
    # 分割成段落
    paragraphs = [p.strip() for p in md_content.split('\n\n') if p.strip()]
    
    i = 0
    while i < len(paragraphs):
        para = paragraphs[i]
        
        # 匹配文章编号和 DOI
        if not metadata["article_id"] and (("文章编号" in para) or ("DOI" in para)):
            article_id_match = re.search(r'文章编号[：:]\s*([^\s]+)', para)
            doi_match = re.search(r'DOI[：:]\s*([^\s]+)', para)
            if article_id_match:
                metadata["article_id"] = article_id_match.group(1).strip()
            if doi_match:
                metadata["doi"] = doi_match.group(1).strip()
            i += 1
            continue
        
        # 匹配标题
        if para.startswith('# ') and not metadata["title"]:
            metadata["title"] = para[2:].strip()
            i += 1
            continue
        
        # 匹配作者
        if not metadata["authors"] and i > 0 and paragraphs[i-1].startswith('# '):
            # 检查是否是作者行（格式类似：秦小林 \( {}^{1,2 * } \) ,古徐 \( {}^{1,2} \)...）
            if re.search(r'\\\(|\\\)', para) or re.search(r'[，,]', para):
                # 清理作者行
                authors_text = re.sub(r'\\\(.*?\\\)', '', para)  # 移除LaTeX格式的标注
                authors_text = re.sub(r'\s+', ' ', authors_text)
                authors = [a.strip() for a in re.split(r'[，,]', authors_text) if a.strip()]
                metadata["authors"] = authors
                i += 1
                continue
        
        # 匹配摘要
        if para.startswith('摘') and ('要' in para) and not metadata["abstract"]:
            abstract_text = para[para.find('要') + 1:].strip()
            # 清理开头的冒号或空格
            abstract_text = re.sub(r'^[：:\s]+', '', abstract_text)
            metadata["abstract"] = abstract_text
            i += 1
            continue
        
        # 匹配关键词
        if para.startswith('关键词') and not metadata["keywords"]:
            keywords_text = para[para.find('关键词') + 3:].strip()
            # 清理开头的冒号或空格
            keywords_text = re.sub(r'^[：:\s]+', '', keywords_text)
            keywords = [k.strip() for k in re.split(r'[；;]', keywords_text) if k.strip()]
            metadata["keywords"] = keywords
            i += 1
            continue
        
        # 匹配收稿/修回/录用日期和基金项目
        if "收稿日期" in para and not metadata["received_date"]:
            received_match = re.search(r'收稿日期[：:]\s*([^\s；；。]+)', para)
            revised_match = re.search(r'修回日期[：:]\s*([^\s；；。]+)', para)
            accepted_match = re.search(r'录用日期[：:]\s*([^\s；；。]+)', para)
            fund_match = re.search(r'基金项目[：:]\s*([^。]+)', para)
            if received_match:
                metadata["received_date"] = received_match.group(1).strip()
            if revised_match:
                metadata["revised_date"] = revised_match.group(1).strip()
            if accepted_match:
                metadata["accepted_date"] = accepted_match.group(1).strip()
            if fund_match:
                metadata["fund"] = fund_match.group(1).strip()
            i += 1
            continue
        
        i += 1
    
    return metadata

def pdf_preprocess(filename):
    metadata = {}
    
    if not os.path.exists(f"./Files/{filename}/{filename}"):
        print(f"处理文献:{filename}")
        Client = Doc2X(config_data.Doc2X_Api)
        out_type = "md"

        file_list, rename_list = get_files(path="./Files/" + filename, mode="pdf", out=out_type)
        success, failed, flag = Client.pdf2file(
            pdf_file=file_list,
            output_path=f"./Files/{filename}",
            output_names=rename_list,
            output_format=out_type,
        )
        print(success, failed, flag)

        zips = []
        for file in success:
            if file.endswith(".zip"):
                zips.append(file)

        target_md = f"./Files/{filename}/{filename}/{filename}.md"
        if os.path.exists(target_md):
            os.remove(target_md)

        success, failed, flag = unzips(zip_paths=zips)
        print(success, failed, flag)

        md_file_path = f"./Files/{filename}/{filename}/{filename}.md"

        str, failed = auto_split_md(mdfile=md_file_path, out_type="replace")
        print(str, failed)

        batch_resize_inplace(f"./Files/{filename}/{filename}/images", 0.5)
    
    # 读取完整的 Markdown 内容来提取元数据
    md_file_path = f"./Files/{filename}/{filename}/{filename}.md"
    if os.path.exists(md_file_path):
        with open(md_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        metadata = extract_metadata_from_markdown(md_content)
        
        # 保存元数据到 JSON 文件
        metadata_file = f"./Files/{filename}/metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    content = md_to_plain_text_with_images(f"./Files/{filename}/{filename}/{filename}.md")
    return content, metadata
