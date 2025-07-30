import lightrag
from llm import Llm_access

llm=Llm_access()
rag = lightrag.LightRAG(working_dir="Vector_partial_stic_v2",llm_model_func=llm.mistral_generator,embedding_func=llm._Embed_func())
rag.finalize_storages()