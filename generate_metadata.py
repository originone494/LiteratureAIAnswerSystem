import os
import json
from pdf_preprocessor import extract_metadata_from_markdown

def main(force_update=False):
    files_dir = "./Files"
    
    if not os.path.exists(files_dir):
        print("Files directory does not exist")
        return
    
    # 遍历 Files 目录下的每个文献文件夹
    for paper_dir in os.listdir(files_dir):
        paper_path = os.path.join(files_dir, paper_dir)
        if not os.path.isdir(paper_path):
            continue
        
        # 检查是否已经有 metadata.json
        metadata_path = os.path.join(paper_path, "metadata.json")
        if os.path.exists(metadata_path) and not force_update:
            print(f"Metadata already exists for {paper_dir}, skipping...")
            continue
        
        # 查找 Markdown 文件
        md_file_path = os.path.join(paper_path, paper_dir, f"{paper_dir}.md")
        if os.path.exists(md_file_path):
            print(f"Processing {paper_dir}...")
            with open(md_file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            metadata = extract_metadata_from_markdown(md_content)
            
            # 保存元数据
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"Generated metadata for {paper_dir}:")
            print(json.dumps(metadata, ensure_ascii=False, indent=2))
        else:
            print(f"Markdown file not found for {paper_dir}, skipping...")

if __name__ == "__main__":
    main(force_update=True)

