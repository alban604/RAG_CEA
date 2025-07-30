import lightrag
import asyncio
from llm import Llm_access

async def rag_answer(question_user,vector_graph_storage,historique=None,mode="Complexe et précise",rep_type="Réponses détaillées"):
    """Génère une réponse à la question_user à partir des connaissances des documents ingérés

    Args:
        question_user (str): Question de l'utilisateur
        vector_graph_storage (str) : chemin du dossier où LightRag doit écrire son cache (vecteur et graphe)
        historique (str) : l'historique des précédentes requêtes et réponses 
        mode (str): mode à utiliser pour parcourir les données [Complexe et précise,Simple et rapide]
        rep_type (str): mode de réponse du llm [Réponses détaillés,Réponses condensées,Réponses en bulletpoint]
    """
    try:
        llm = Llm_access()
        rag = lightrag.LightRAG(working_dir=vector_graph_storage,llm_model_func=llm.mistral_generator,embedding_func=llm._Embed_func())
        await rag.initialize_storages()
        dictio_mode={"Simple et rapide":"naive","Complexe et précise":"hybrid"}
        dictio_rep_type = {"Réponses détaillées":'Multiple Paragraphs',"Réponses condensées":'Single Paragraph',"Réponses en bulletpoint":'Bullet Points',"Détaillées":'Multiple Paragraphs',"Condensées":'Single Paragraph',"Bulletpoint":'Bullet Points'}
        reponse = await rag.aquery(question_user,param=lightrag.QueryParam(mode=dictio_mode[mode],conversation_history=historique,response_type=dictio_rep_type[rep_type]))
        await rag.finalize_storages()
        print(reponse)
        
        return reponse
    
    except Exception as e:
        print("Erreur dans la fonction rag_answer() : "+str()+" "+str(e))
        #traceback.print_exc()
        return 

if __name__=="__main__":
    asyncio.run(rag_answer("Qu'est ce que le groupe SDIS ?","Vector_partial_stic_v2_entraine"))