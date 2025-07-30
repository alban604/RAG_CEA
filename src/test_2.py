import asyncio
import torch
import inspect
import traceback
#import lightrag
from lightrag import LightRAG, QueryParam
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import EmbeddingFunc
import requests
import os
import numpy as np
import urllib3
from dotenv import load_dotenv
from llm import Llm_access
from connection_bd_redis import process_one_doc_trough_docling
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv(dotenv_path="password_and_key.env")
API_KEY = os.getenv("API_KEY")
EMBEDDING_MODEL = "LITELLM2OLLAMA-bge-m3"
COMPLETION_MODEL = "mistralsmall-22b"
DOSSIER_SAUVEGARDE = "corpus_save"
PATH_DIRECTORY = "dossier_test"
CA = "/home/prog/git/git-2.17.2/etc/ca-bundle.crt"
os.environ["HOLIAGEN_API_KEY"]=API_KEY
nb_emb_ge = 0
init_TRUE = True
rag_instance = None


async def initialisation_rag(vector_graph_storage):
    """Initialise une instance de LightRag
    Args :
        vector_graph_storage (str) : Dossier où l'on souhaite stocker les vecteurs et graphes du rag -> Création automatique
    Return : Instance de LightRag
    """
    try :
        llm = Llm_access()
        rag = LightRAG(working_dir=vector_graph_storage,llm_model_func=llm.mistral_generator,embedding_func=llm._Embed_func())
        await rag.initialize_storages()
        await initialize_pipeline_status()
        return rag
    except Exception as err:
        print("L'initialisation n'a pas fonctionnée : "+str(err))
        return



async def rag_gen_data(vector_graph_storage):
    """Fonction qui gère l'ingestion de données de la base de donnée bd dans le rag
    Pour appeler cette fonction manuellement il faut le faire depuis connection_bd_redis.py (pour éviter les import circulaires)
    Args:
        vector_graph_storage (str): chemin du dossier dans lequel on veut stocker les vecteurs et graphe généré par LightRAG
        bd (<instance de Bd_Redis>) : base de donnée qui contient les données que l'on veut donner au rag
        list_fichier (list[str], optional): Si la list_fichier ne vaut pas None, seul les fichiers qui sont dans cette liste seront ingérés (cela permet de mettre à jour que certains fichiers). Defaults to None.
    """
    try:
        #RAG        
        with open("/stic/110.3.2.4-SDIS/test_stage/organisation_du_stic.txt","r") as f:
            txt = f.read()
            rag = await initialisation_rag(vector_graph_storage)
            await rag.ainsert(txt,file_paths="-stic-110.3.2.4-SDIS-test_stage-organisation_du_stic.txt")
        with open(vector_graph_storage+'/graph_chunk_entity_relation.graphml','r') as graph:
            if len(graph.read())<2:
                print("Le fichier de graphe graph_chunk_entity_relation.graphml n'a pas pu se générer")
                print("Considérez le générer manuellement avec le script generateur_de_graphe.py (le nom a pu changer)")
        print("[END] Vecteur et graphe généré",flush=True)
    
    except Exception as e:
        print("Erreur dans la fonction Main : "+str(e))
        return 
    finally:
        await rag.finalize_storages()


asyncio.run(rag_gen_data("Vector_partial_stic_v2_entraine_test"))