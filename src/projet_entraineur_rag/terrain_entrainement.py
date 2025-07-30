import entraineur
import entraine
import asyncio

def log(txt):
    with open("log_trainning.txt",'a') as f:
        f.write(str(txt) + "\n")

def init_log():
    open("log_trainning.txt",'w')

async def launch_trainning(storage_entraineur,storage_entraine,nb_tour_entrainement=10000):
    """
    Lance un entrainement du rag entrainé
    Ce rag va stocker dans son fichier kv_llm_response_cache.json plein de questions qui serviront à faire les suggestions

    Args:
        storage_entraineur (str): dossier de stockage du rag entraineur 
        storage_entraine (str): dossier de stockage du rag entraine. Même contenu du dossier mais recommandé d'avoir deux dossiers identiques différents
        nb_tour_entrainement (int, optional): nombre de tours d'entrainement. Defaults to 10000.
    """
    init_log()
    log("[ENTRAINEMENT]")
    for a in range(0,nb_tour_entrainement):
        question="\n"
        while "\n" in question : #évites les problèmes où la question n'en est pas vraiment une ou n'est pas que ça
            question = await entraineur.question_entraineur(storage_entraineur)
            for a in range(0,1000):
                if question==None:
                    question = await entraineur.question_entraineur(storage_entraineur)
                else:
                    break

        await entraine.rag_answer(question,storage_entraine)
        log(f"Q{a} : "+question)
    log("[ENTRAINEMENT FINI]")
    print("ENTRAINEMENT FINI")

asyncio.run(launch_trainning("Vector_partial_stic_v2","Vector_partial_stic_v2_entraine"))