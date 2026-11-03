from zhipuai import ZhipuAI
from config.settings import ZHIPU_API_KEY

_client = ZhipuAI(api_key=ZHIPU_API_KEY)

def embed(texts: list) -> list:
    """把一批文本转成向量，返回向量列表"""
    resp = _client.embeddings.create(model="embedding-3", input=texts)
    return [item.embedding for item in resp.data]
