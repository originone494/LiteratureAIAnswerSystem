import pandas as pd
import config_data
from knowledge_base import KnowledgeBaseService

df = pd.read_excel("./data/train.xlsx")

# sample_df = df.sample(n=min(6000, len(df)))

contexts = df["Context"].astype(str).tolist()

service = KnowledgeBaseService(name=config_data.evaluate_collection_name,dir=config_data.evaluate_dir)

a = 1

for context in contexts:
    service.upload_by_str(context,"train")
    a+=1
    print(a)

print("结束")

