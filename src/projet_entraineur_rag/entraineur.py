import lightrag
import os
import asyncio
import requests
from dotenv import load_dotenv
from lightrag.utils import EmbeddingFunc
import numpy as np
import traceback
from llm import Llm_access

async def question_entraineur(vector_graph_storage,mode="Complexe et précise",rep_type="Réponses détaillées"):
    """Génère une question à partir des connaissances des documents ingérés

    Args:
        question_user (str): Question de l'utilisateur
        vector_graph_storage (str) : chemin du dossier où LightRag doit lire les vecteurs et graphes (Attention : Il est conseillé de ne pas utiliser le même que l'entrainé)
        mode (str): mode à utiliser pour parcourir les données [Complexe et précise,Simple et rapide]
        rep_type (str): mode de réponse du llm [Réponses détaillés,Réponses condensées,Réponses en bulletpoint]
        clear_cache (bool, optional): Supprime le contenu du dossier data\ si True (permet d'oublier les vecteurs de l'itération précédente)
    """
    try:
        llm = Llm_access()
        rag = lightrag.LightRAG(working_dir=vector_graph_storage,llm_model_func=llm.mistral_generator,embedding_func=llm._Embed_func(),enable_llm_cache=False,enable_llm_cache_for_entity_extract=False)
        await rag.initialize_storages()
        dictio_mode={"Simple et rapide":"naive","Complexe et précise":"hybrid"}
        dictio_rep_type = {"Réponses détaillées":'Multiple Paragraphs',"Réponses condensées":'Single Paragraph',"Réponses en bulletpoint":'Bullet Points'}
        reponse = await rag.aquery("Choisis une question au hasard sur un document au hasard ? Repond à cette réquête juste par la question sans rien ajouter. La question doit être en français.",param=lightrag.QueryParam(mode=dictio_mode[mode],response_type=dictio_rep_type[rep_type]))
        await rag.finalize_storages()
        
        return reponse
    
    except Exception as e:
        print("Erreur dans la fonction Main : "+str(e))
        #traceback.print_exc()
        return 

if __name__=="__main__":
    asyncio.run(question_entraineur("vector_tester"))