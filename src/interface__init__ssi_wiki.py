import gradio as gr
from rag_answer import rag_answer
from ldap3 import Server, Connection, NTLM, ALL
import re
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="password_and_key.env")
SERVICE_USER = os.getenv("SERVICE_USER")
SERVICE_PASSWORD = os.getenv("SERVICE_PASSWORD")

LDAP_SERVER = "ldaps://intra.cea.fr"       # ou ldaps://... pour sécurité
LDAP_DOMAIN = "intra.cea.fr"   
BASE_DN = "DC=intra,DC=cea,DC=fr"       
DICTIO_GROUP = {"stic":"GRE - 110.3.2"}

#PATH_DIRECTORY = "dossier_test"
VECTOR_GRAPH_STORAGE = "/appli/stage_rag_ov/Vector_wiki_ssi_entraine"

#######################################

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

async def chat_fn(message, history,mode,type_txt):
    """Fonction de chat -> Retourne une réponse au message entré en paramètre

    Args:
        message (str): message/question de l'utilisateur
        history (str): historique des chats précédents (gérer par Gradio)
        mode (str): mode à utiliser pour parcourir les données [Complexe et précise,Simple et rapide]
        type_txt (str): mode de réponse du llm [Réponses détaillés,Réponses condensées,Réponses en bulletpoint]

    Returns:
        str: reponse de l'IA à l'utilisateur
    """
    response = await rag_answer(message,VECTOR_GRAPH_STORAGE,history,mode,type_txt)
    return response

#server_name="0.0.0.0",server_port=7860
def lancer_chat(groupe):
    """lance une instance de gradio avec un chat qui a accès au doc du groupe "groupe"
    Les droits associés au "groupe" sont contenus dans le DICTIO_GROUP

    Args:
        groupe (str): ["stic"]
    """
    global groupe_a_avoir_actuel
    groupe_a_avoir_actuel = DICTIO_GROUP[groupe]
    #dictio_mode={"Simple et rapide":"naive","Complexe et précise":"hybrid"}
    #text_mode_a_choisir = "**Local** : Pour des recherches très précises.\n **Global** : Requêtes nécessitant une vue d'ensemble du corpus.\n **Hybrid** : Combine les approches locales et globales. \n **Mix** : Pour des recherches complexes. \n **Naive** : Recherches basiques ou rapides, sans besoin de finesse.\n"
    mode_a_choisir = gr.Radio(choices=["Simple et rapide","Complexe et précise"],label="Mode",value="Complexe et précise",interactive=True) #,info=text_mode_a_choisir
    t_texte_a_choisir = gr.Radio(choices=["Réponses détaillées","Réponses condensées","Réponses en bulletpoint"],label="Type de réponse",value="Réponses détaillées",interactive=True)
    additional_inp = [mode_a_choisir,t_texte_a_choisir]
    #Interface Gradio
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue",neutral_hue="blue")) as demo:
        gr.ChatInterface(type="messages",fn=chat_fn, title="RAG Chatbot 💬",description=f"Un chatbot rag qui répond à vos questions sur les documents du wiki et ssi",
        additional_inputs=additional_inp,additional_inputs_accordion="Paramètres de recherche")
        demo.launch(server_name="0.0.0.0",server_port=7899,auth=authentifier)

lancer_chat("stic")
