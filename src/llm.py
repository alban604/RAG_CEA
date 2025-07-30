import lightrag
import os
import asyncio
import requests
from dotenv import load_dotenv
from lightrag.utils import EmbeddingFunc
import numpy as np

class Llm_access:

    def __init__(self):
        load_dotenv(dotenv_path="password_and_key.env")
        self.API_KEY = os.getenv("API_KEY")
        os.environ["HOLIAGEN_API_KEY"]=self.API_KEY
        self.CA = "/home/prog/git/git-2.17.2/etc/ca-bundle.crt"
        self.nb_emb_ge = 0

    async def mistral_generator(self,prompt,system_prompt=None,history_message=[],**kwargs):
        """Appel par API un moteur d'IA de completion

        Args:
            prompt (str): prompt (point de vue utilisateur)
            system_prompt (str, optional): contient le contexte à considérer pour répondre au prompt (point de vue système)
            history_message (list, optional): historique. Non pris en compte pour le moment
        Returns:
            str: réponse de l'IA générative à prompt et sytem_prompt
        """
        try:
            #Génération du prompt qu'on va envoyer à l'IA
            message = []
            if system_prompt:
                message.append({"role": "system", "content": system_prompt})
            message.append({"role": "user","content": str(prompt)})
            """if history_message:
                message.extend(history_message)"""

            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer "+self.API_KEY}
            payload = {  # ou mistral-7b-instruct, à c  onfirmer
                "messages": message,
                "max_tokens": 1024,
                "temperature": 0.7
            }

            url = 'https://litellm-dev.ixia.intra.cea.fr/engines/mistralsmall-22b/chat/completions'

            reponse = requests.post(url, headers=headers, json=payload, verify=self.CA).json()
            return reponse["choices"][0]["message"]["content"].strip()
        
        except Exception as e:
            print("Erreur dans la fonction mistral_generator : "+str(e))
            return 
        
    async def mistral_embed_one_by_one(self,text):
        """Génère les embeddings pour un texte fourni en paramètre en faisant appel à l'API d'un moteur IA d'embeddings

        Args:
            text (str): texte à transformer en embeddings

        Returns:
            list: liste de float correspondant au vecteur du mot texte
        """
        
        url = "https://litellm-dev.ixia.intra.cea.fr/v1/embeddings"
        headers = {
            "Authorization": "Bearer "+self.API_KEY}
        payload = {
            "model": "LITELLM2OLLAMA-bge-m3", 
            "input":text if isinstance(text, list) else [text]
        }
        emb = requests.post(url, headers=headers, json=payload, verify=self.CA).json()
        t_nump = np.array(emb["data"][0]["embedding"])

        self.nb_emb_ge #compteur d'embedding généré
        self.nb_emb_ge+=1
        print(f"[+] Embedding généré: {self.nb_emb_ge} ")
        return t_nump

    async def mistral_embed(self,text):
        """Fais appel à la fonction mistral_embed_one_by_one 1 fois si type(text)=str
                                                            len(text) fois si type(text)=list
            Pour obtenir une liste des embeddings

        Args:
            text (list or str): contenant du texte à transformer en vecteur
        Returns:
            list : liste de vecteurs ou un seul vecteur 
        """
        try :
            if isinstance(text,list):
                tasks = [self.mistral_embed_one_by_one(elt) for elt in text]
                return await asyncio.gather(*tasks)
                #return [await mistral_embed_one_by_one(elt) for elt in text]
            else:
                return await self.mistral_embed_one_by_one(text)
            
        except Exception as e:
            print("Erreur dans la fonction mistral_embed -> "+str(e))

    def _Embed_func(self):
        """Renvoie un objet LightRAG de type fonction d'embedding
        """
        return EmbeddingFunc(func=self.mistral_embed,embedding_dim=1024,max_token_size=5050)
