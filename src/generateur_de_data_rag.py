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
    
async def insert(rag,donnee_txt,nom_du_fich,i):
    """Insére une donnée dans LightRag

    Args:
        rag (instance de LightRag): instance de Lightrag
        donnee_txt (str): le contenu 
        nom_du_fich (str): chemin du fichier (en général avec des - à la place des /)
        i (int): numéro du fichier traité
    """
    try:
        nom_du_fich = nom_du_fich.decode('utf-8') if isinstance(nom_du_fich, bytes) else str(nom_du_fich)
        #print(f"[++] Création d'une tache {i} ---- Doc : {nom_du_fich[:-4]}",flush=True)
        await rag.ainsert(str(donnee_txt),file_paths=[nom_du_fich[:-4]])
        print(f"[++] Insertion réussi {i} ---- Doc : {nom_du_fich[:-4]}",flush=True)
    except Exception as e:
        print(f"[DEBUG] nom_du_fich = {nom_du_fich} ({type(nom_du_fich)})")
        print(f"[DEBUG] file_paths = {[nom_du_fich[:-4]]} ({type(nom_du_fich[:-4])})")
        print(f"[DEBUG] content :  ({type(donnee_txt)})")
        print(f"[ERROR] Exception lors de l'insertion du fichier : {nom_du_fich}")
        print(f"Type : {type(e).__name__}")
        print(f"Message : {e}")
        print("[TRACEBACK]")
        traceback.print_exc()


async def ingere_connaissance(rag,bd,list_fichier=None): #ATTENTION list_fichier contient les chemins avec des tirets
    """Intègre les connaissances de la base de donnée bd dans l'instance du rag passsé en paramètre
        PREREQUIS : bd doit contenir la traduction en txt des documents que l'on souhaite ingérer 

    Args:
        rag : Instance de LightRag à laquelle on souhaite ajouter les données
        bd (<instance de Bd_Redis>) : base de donnée de laquelle on veut ingérer les connaissances du rag 
        list_fichier (list) : liste de fichier qu'on veut insérer dans le rag depuis le dossier (si =None tout les fichiers seront traités)
    Returns:
        rag : Instance de LightRag à laquelle on a ajouté les données
    """
    try:
        i=1
        async with asyncio.TaskGroup() as tg: #réalise les ainsert des données dans le rag en simultanée
            tasks = []
            for key in bd.scan_keys():
                try:
                    nom_du_fich = key.decode('utf-8')
                    if "-ESI-" in nom_du_fich:
                        print(nom_du_fich)
                    if list_fichier==None or nom_du_fich in list_fichier:
                        content = bd.get_content_from_key(key)
                        if len(content)>15: #si le document est vide ou presque cela peut créer une erreur  #en cas de doc vide on le passe
                            content = json.dumps({"document_title" : nom_du_fich,"document_content":content})
                            print(f"[+] Ouverture du fichier : {i} ---- Doc : {nom_du_fich[:-4]}")
                            i+=1
                            task = tg.create_task(insert(rag,content,nom_du_fich,i))
                            tasks.append(task)
                        else:
                            print(f"[-] Fichier vide : {i} ---- Doc : {key[:-4]}")
                            i+=1
                except Exception as e:
                    print(f"[-] ECHEC de l'ingestion de donnée : {i} ---- Doc : {key[:-4]}")
                    print(e)
                    traceback.print_exc()

        return rag
    except Exception as e:
        print("Erreur dans ingere_connaissance ->"+str(e))

async def rag_gen_data(vector_graph_storage,bd,list_fichier=None):
    """Fonction qui gère l'ingestion de données de la base de donnée bd dans le rag
    Pour appeler cette fonction manuellement il faut le faire depuis connection_bd_redis.py (pour éviter les import circulaires)
    Args:
        vector_graph_storage (str): chemin du dossier dans lequel on veut stocker les vecteurs et graphe généré par LightRAG
        bd (<instance de Bd_Redis>) : base de donnée qui contient les données que l'on veut donner au rag
        list_fichier (list[str], optional): Si la list_fichier ne vaut pas None, seul les fichiers qui sont dans cette liste seront ingérés (cela permet de mettre à jour que certains fichiers). Defaults to None.
    """
    try:
        #RAG        
        rag = await initialisation_rag(vector_graph_storage)
        rag = await ingere_connaissance(rag,bd,list_fichier=list_fichier)
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


if __name__=="__main__":
    #asyncio.run(rag_answer("Donne moi un exemple de commande pour cloner un depot git",clear_cache=True))
    #asyncio.run()
    pass
    #NE PAS LANCER RAG_GEN_DATA (il doit être lancer depuis connection_bd_redis.py avec la fonction appel_rag_gen_data())