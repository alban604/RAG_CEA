from pymongo import MongoClient
import lightrag
import os
from lightrag.kg.mongo_impl import MongoKVStorage
from lightrag.kg.mongo_impl import MongoDocStatusStorage
from lightrag.kg.mongo_impl import MongoGraphStorage
from lightrag.kg.mongo_impl import MongoVectorDBStorage
from lightrag.kg.shared_storage import initialize_pipeline_status
from llm import Llm_access
import asyncio
url = "mongodb://vectoruser:toto!@localhost:27017/vectordb?authSource=vectordb"

llm = Llm_access()

client = MongoClient(url)

os.environ["MONGO_URI"] = "mongodb://vectoruser:toto!@localhost:27017/vectordb?authSource=vectordb"
os.environ["MONGO_DATABASE"] = "LightRAG"
os.environ["MONGO_KG_COLLECTION"] = "vector_tester"


db = client['tester']
workspace = "tester"
# kv_storage = MongoKVStorage(namespace="kv_storage", global_config={}, embedding_func=llm._Embed_func())
# vector_storage = MongoVectorDBStorage(namespace="vector_storage", global_config={ "embedding_batch_num": 32,"vector_db_storage_cls_kwargs": {
#             "cosine_better_than_threshold": 0.2
#         }}, embedding_func=llm._Embed_func())
# graph_storage = MongoGraphStorage(namespace="graph_storage", global_config={}, embedding_func=llm._Embed_func())
# #doc_status_storage = MongoDocStatusStorage(namespace="doc_status_storage", global_config={}, embedding_func=llm._Embed_func())
async def rag_test():
    rag = lightrag.LightRAG("tester",llm_model_func=llm.mistral_generator,embedding_func=llm._Embed_func(),kv_storage="MongoKVStorage",vector_storage="MongoVectorDBStorage")
    await rag.initialize_storages()
    await initialize_pipeline_status()
    await rag.ainsert("Alban a 19 ans il est étudiant à l'ensimag")
    await rag.finalize_storages()
    await rag.aquery("Quel age à Alban ?",param=lightrag.QueryParam(mode='local'))

asyncio.run(rag_test())