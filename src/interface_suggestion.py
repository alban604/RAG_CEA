import gradio as gr
from rag_answer import rag_answer
from ldap3 import Server, Connection, NTLM, ALL
import re
import os
from dotenv import load_dotenv
from similarite_mots import comparaison_avec_prompt_calcule
import json

#VARIABLE à adapter 
VECTOR_GRAPH_STORAGE = "/appli/stage_rag_ov/Vector_partial_stic_v2_entraine" #dossier de vecteur et graphe du LightRAG qu'on veut lancer

#Chargement des variables d'environnements
load_dotenv(dotenv_path="password_and_key.env")
SERVICE_USER = os.getenv("SERVICE_USER")
SERVICE_PASSWORD = os.getenv("SERVICE_PASSWORD")

LDAP_SERVER = "ldaps://intra.cea.fr"       # ou ldaps://... pour sécurité
LDAP_DOMAIN = "intra.cea.fr"   
BASE_DN = "DC=intra,DC=cea,DC=fr"       

#Initilisation des variables globales
suggestion_liste = ["",""]
groupe_a_avoir_actuel = None #global


def authentifier(username, password):
    """Fonction d'authentification

    Args:
        username (str): 
        password (str): 

    Returns:
        Bool: True si authentification réussi, False sinon
    """
    global groupe_a_avoir_actuel
    #POUR LE DEBBUGAGE A ENLEVER 
    if username=="" and password=="":
        return True
    try:
        server = Server(LDAP_SERVER,use_ssl=True,get_info=ALL)
        service_conn = Connection(server,user=f"{LDAP_DOMAIN}\\{SERVICE_USER}",password=SERVICE_PASSWORD,authentication=NTLM,auto_bind=True)
        search_filter = f"(sAMAccountName={username})"
        service_conn.search(BASE_DN, search_filter, attributes=["distinguishedName","memberOf"])
        if not service_conn.entries:
            return False
        #user_dn = service_conn.entries[0].distinguishedName.value
        ntlm_user = LDAP_DOMAIN+"\\"+username
        user_conn = Connection(server, user=ntlm_user, password=password, authentication=NTLM)

        if user_conn.bind():
            #TEST DU GROUPE
            groupes = []
            user_entry = service_conn.entries[0]
            if 'memberOf' in user_entry:
                groupes_dns = user_entry.memberOf.values
                for dn in groupes_dns:
                    match = re.search(r'CN=([^,]+)', dn)
                    if match:
                        groupes.append(match.group(1))
                        if match.group(1)[:len(groupe_a_avoir_actuel)]==groupe_a_avoir_actuel:
                            user_conn.unbind()
                            service_conn.unbind()
                            return True 
            
            service_conn.unbind()
            return False

        else:
            service_conn.unbind()
            return False

    except Exception as e:

        print("erreur : "+str(e))
        return False


async def chat_fn(message, history, mode, type_txt):
    """Fonction de chat -> Retourne une réponse au message entré en paramètre
    Args:
        message (str): message/question de l'utilisateur
        history (str): historique des chats précédents (géré par Gradio)
        mode (str): mode à utiliser pour parcourir les données [Complexe et précise, Simple et rapide]
        type_txt (str): mode de réponse du llm [Réponses détaillées, Réponses condensées, Réponses en bulletpoint]
    Returns:
        str: réponse de l'IA à l'utilisateur
    """
    history.append({"role":"user","content":message})
    yield history
    status_message = {"role": "assistant", "content": "*Traitement...*"}
    history.append(status_message)
    yield history
    response = await rag_answer(message, VECTOR_GRAPH_STORAGE, history, mode, type_txt)  
    history.remove(status_message)
    history.append({"role":"assistant","content":response})
    yield history
     
def get_suggestion1(user_prompt):
    """Fonction pour obtenir des suggestions (ici la 1er suggestion) basées sur l'entrée de l'utilisateur

    Args:
        user_prompt (str): le prompt que l'utilisateur est entrain de taper

    Returns:
        Mise à jour de l'objet gradio associé à la suggestion n°1
    """
    global suggestion_liste 
    suggestion_liste = comparaison_avec_prompt_calcule(user_prompt,VECTOR_GRAPH_STORAGE)
    return gr.update(value=suggestion_liste[-1]) 

def get_suggestion2(user_prompt):
    """Fonction pour obtenir des suggestions (ici la 2e suggestion) basées sur l'entrée de l'utilisateur

    Args:
        user_prompt (str): le prompt que l'utilisateur est entrain de taper

    Returns:
        Mise à jour de l'objet gradio associé à la suggestion n°2
    """
    global suggestion_liste
    return gr.update(value=suggestion_liste[-2]) 

def GetSourcesFromLlmReponse(reponse):
    """Renvoie la liste des sources à partir de la reponse du rag de LightRAG
    Args:
        reponse (str): reponse du rag à un prompt

    Returns:
        List [str]: liste des sources mentionnées dans le fichier (les sources sont les chemins des fichiers avec des tirets à la place des /)
    """
    liste_source_return = []
    if len(reponse)>14:#Si la réponse est rop petite elle n'a pas de sources
        for i in range(14,len(reponse)): 
            if reponse[i-14:i]=="### Références":  #On cherche la zone des sources à la fin de la réponse du rag
                sources_space = reponse[i:]
                if len(sources_space)<=5:
                    return
                sources_space = sources_space.split("\n")   #On sépare la zone des sources par ligne
                for source_not_extracted in sources_space :
                    if len(source_not_extracted)>5:   #Si la ligne est plus petite que 5, pas de source
                        for l in range(5,len(source_not_extracted)-1):
                            if source_not_extracted[l-5:l]=="[KG] " or source_not_extracted[l-5:l]=="[KC] ": #Sur chaque ligne on recherche la mention de KG ou KC 
                                liste_source_return.append(source_not_extracted[l:])
                return liste_source_return
    return liste_source_return

def downloader(chatbot):
    """Fonction qui renvoie les chemins des fichiers de source (utile pour gradio)

    Args:
        chatbot (list[dict[str:str]]): list de dictionnaires de la forme  {"role": "assistant", "content": "I am happy to provide you that report and plot."},

    Returns:
        list : Liste des chemins des fichiers de sources
    """
    sources = []
    for conv in chatbot:
        if conv["role"]=="assistant":
            reponse = conv["content"]
            sources += GetSourcesFromLlmReponse(reponse) #récupère les sources de tout l'historique
    
    #on transforme les sources qui sont les chemins avec les tirets en chemin de fichier 
    try:
        with open(VECTOR_GRAPH_STORAGE+"/from_name_to_chemin.json",'r') as f:
            dictio_nom_to_chemin = json.load(f)
        return [dictio_nom_to_chemin[source+".txt"] for source in sources if source+".txt" in dictio_nom_to_chemin.keys()] 
    except:
        print("Le json from_name_to_chemin n'a potentiellement pas été généré pour ce stockage de vecteur et de graphe.\nRéférez vous à la doc pour trouver le script qui permet de le créer")

def lancer_chat(prefixe_autorise,launching_port,list_dossier_source):
    """Lance une instance de Gradio avec un chat qui a accès au doc du groupe 'groupe'
    
    Args:
        prefixe_autorise (str): préfixe du groupe duquel on souhaite autorisé l'accès (ex : "GRE - 110.3.2")
        launching_port (str): port sur lequel le service va être accessible
        list_dossier_source (List[str]): liste des chemins des dossiers sources que Gradio a le droit d'ouvrir (permet de citer les sources)
    PREREQUIS : Avoir choisit la  valeur de la variable globale suivante (voir ligne 11)
        VECTOR_GRAPH_STORAGE : dossier de vecteur et de graphe sur lequel on veut lancer le rag

    """
    global groupe_a_avoir_actuel
    groupe_a_avoir_actuel = prefixe_autorise
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue", neutral_hue="blue")) as demo:
        chatbot = gr.Chatbot("", type="messages",autoscroll=False,show_copy_button=True,layout='bubble')
        with gr.Row():
            with gr.Column(scale=2):
                txt = gr.Textbox(placeholder="Entrez votre question ici...",label="Questions",elem_id="textbox")
                gr.Markdown("### Remarques utiles : ")
                gr.Markdown(" - Les suggestions sont des réponses pré-enregistrés et l'IA peut donc y répondre instantanément !")
                gr.Markdown(" - Les suggestions étant basées sur des **mots-clés** : pas besoin de faire de phrase pour les trouver 😉")
            with gr.Column(scale=2):
                suggestion1 = gr.Textbox(label="🛠-Suggestion 1")
                suggestion2 = gr.Textbox(label="🛠-Suggestion 2")
                gr.Markdown("")
                gr.Markdown("")
                gr.Markdown("")
        telecharger = gr.Button("📥 Télécharger les sources")
        file_button = gr.File(label="Sources")
        with gr.Row():
            with gr.Column(scale=2):
                mode_a_choisir = gr.Radio(choices=["Simple et rapide","Complexe et précise"],label="Mode",value="Complexe et précise",interactive=True) #,info=text_mode_a_choisir
                gr.Markdown("### Remarques sur les modes : ")
                gr.Markdown(" - Les suggestions ne sont ultra-rapides qu'avec le mode 'Complexe et précise' (mode avec lequel elles sont entrainées)")
            with gr.Column(scale=2):
                t_texte_a_choisir = gr.Radio(choices=["Détaillées", "Condensées", "Bulletpoint"], label="Type de réponse", value="Détaillées", interactive=True)
                gr.Markdown("### Remarques sur les types de réponses : ")
                gr.Markdown(" - Les types de réponses ne fonctionne pas si vous utilisez les suggestions.")
 
        txt.change(fn=get_suggestion1,inputs=[txt],outputs=suggestion1)
        txt.change(fn=get_suggestion2,inputs=[txt],outputs=suggestion2)
        suggestion1.submit(fn=chat_fn, inputs=[suggestion1, chatbot, mode_a_choisir, t_texte_a_choisir], outputs=chatbot)
        suggestion2.submit(fn=chat_fn, inputs=[suggestion2, chatbot, mode_a_choisir, t_texte_a_choisir], outputs=chatbot)
        telecharger.click(fn=downloader, inputs=chatbot,outputs=file_button)

        txt.submit(fn=chat_fn, inputs=[txt, chatbot, mode_a_choisir, t_texte_a_choisir], outputs=chatbot)
        
        demo.launch(server_name="0.0.0.0", server_port=launching_port,allowed_paths=list_dossier_source, auth=authentifier,ssl_keyfile="/appli/cert/key.pem",ssl_certfile="/appli/cert/cert.pem",ssl_verify=False) #

lancer_chat(prefixe_autorise="GRE - 110.3.2",launching_port=7875,list_dossier_source=["/stic"])
