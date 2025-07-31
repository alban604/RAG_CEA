import json
import os
dictionnaire = {}
def genere_dictionnaire(dossier_fichier):
    """Génère un dictionnaire d'équivalence entre les noms des fichiers (avec des tirets à la place des / et finissant en .txt) et les chemins des fichiers
    Le dictionnaire est stocké dans la variable global dictionnaire

    Args:
        dossier_fichier (str): Dossier qui contient tout les fichiers (pdf,docs,...) à partir desquels on veut faire le dictionnaire (exemple : '/stic')
    """
    global dictionnaire
    for nomfichier in os.scandir(dossier_fichier):
            if nomfichier.is_dir():#si le fichier est un dossier on re-rappelle la fonction sur ce dossier
                try:
                    genere_dictionnaire(dossier_fichier+"/"+nomfichier.name)
                except:
                    pass
            else:#sinon on l'ajoute au dictionnaire
                chemin_fich = str(dossier_fichier)+"/"+str(nomfichier.name)
                nom_txt = chemin_fich.replace("/","-")+".txt"
                dictionnaire[nom_txt]=chemin_fich

def genere_json(dossier_fichier,vector_graph_storage):
    """Génère un json d'équivalence entre les noms des fichiers (avec des tirets à la place des /) et les chemins des fichiers
    Le json sera enregistré dans le dossier vector_graph_storage (dossier des vecteurs et graphe du rag)
    Ce json est nécéssaire pour pouvoir télécharger les sources des recherches du rag depuis gradio
    Le json généré écrasera la version précédente si existante
    Args:
        dossier_fichier (str): Dossier qui contient tout les fichiers (pdf,docs,...) à partir desquels on veut faire le dictionnaire (exemple : '/stic')
        vector_graph_storage (str): Dossier de stockage des vecteurs du graphe (dans lequel on enregistre le json)
    """
    global dictionnaire
    genere_dictionnaire(dossier_fichier)
    with open(vector_graph_storage+"/from_name_to_chemin.json",'w') as f:   
        f.write(json.dumps(dictionnaire)) 

def ajoute_json(dictionnaire_add,vector_graph_storage):
    """Ajoute à un json existant un ensemble de set de valeur (nom,chemin) présent dans le dictionnaire "dictionnaire_add" dans le json "from_name_to_chemin.json"
    Cela permet de mettre à jour le système de récupération des sources sans avoir à recalculer tout le dictionnaire json

    Args:
        dictionnaire_add (dict[str:str]): dictionnaire qui associe à un nom txt (ex : chemin-to-doc.pdf.txt) le chemin du fichier (ex: chemin/to/doc.pdf) 
        vector_graph_storage (str): Dossier de stockage des vecteurs du graphe (dans lequel est enregistré le json "from_name_to_chemin.json")
    """
    with open(vector_graph_storage+"/from_name_to_chemin.json",'r') as f:  
        dictio_json = json.load(f)
    with open(vector_graph_storage+"/from_name_to_chemin.json",'w') as f:  
        for key in dictionnaire_add.keys():
            dictio_json[key]=dictionnaire_add[key]
        f.write(json.dumps(dictio_json))

#ajoute_json({"albanus-dm-bb.docx.txt":"alban/dm-bb.docx.txt"},"Vector_wiki_ssi_entraine")

if __name__=="__main__":
    VECTOR_GRAPH_STORAGE = "Vector_partial_stic_v2"
    DOSSIER_SOURCE = "/stic"
    genere_json(DOSSIER_SOURCE,VECTOR_GRAPH_STORAGE)
