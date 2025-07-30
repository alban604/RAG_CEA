
import json

#Distance de Levenshtein très rapide mais donne des résultats très médiocre
# import Levenshtein
# def comparaison_prompt(prompt1,prompt2):
#     # Calcul de la distance de Levenshtein
#     distance = Levenshtein.distance(prompt1, prompt2)
#     max_length = max(len(prompt1), len(prompt2))
#     similarity = 1 - (distance / max_length)
#     return similarity

def comparaison_prompt(p1, p2):
    """Compare deux phrases s1 et s2 et retourne un coefficient de proximité sémantique

    Args:
        s1 (str): phrase n°1
        s2 (str): phrase n°2

    Returns:
        int: coefficient de proximité sémantique
    """
    tokens1 = set(p1.lower().split())
    tokens2 = set(p2.lower().split())
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / len(union) if union else 0

def comparaison_avec_prompt_calcule(prompt,vector_graph_storage):
    """Compare le prompt que l'utilisateur est entrain de taper à toutes les suggestions possibles (dans kv_store_llm_response_cache.json) 
    pour retourner les 2 meilleures

    Args:
        prompt (str): prompt que l'utilisateur est entrain de taper
        vector_graph_storage (str): dossier de stockage des vecteurs et graphe du lightrag que l'on utilise

    Returns:
        List[str]: Liste des deux meilleures suggestions 
    """
    #Récupère toutes les suggestions possibles, c'est-à-dire toutes les questions dont le rag a déjà enregistré la réponse
    set_question_connu = set()
    with open(vector_graph_storage+"/kv_store_llm_response_cache.json",'r') as f:#Pour cela on va dans l'historique des prompt répondu 
        dictio = json.load(f)
        for key in dictio["hybrid"].keys():
            question = str(dictio["hybrid"][key]['original_prompt'])
            set_question_connu.add(question)
    
    #tri des suggestions dans l'ordre de pertinence 
    meilleur_suggestion = sorted(list(set_question_connu),key=lambda x:comparaison_prompt(x,prompt))[-3:]
    return meilleur_suggestion

if __name__=="__main__":
    print(comparaison_avec_prompt_calcule("aar ","Vector_wiki_ssi_entraine"))