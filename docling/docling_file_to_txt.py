import docling
import torch
from torch.nn import DataParallel
#from docling import Corpus
from docling.document_converter import DocumentConverter
from pytorch_lightning import Trainer
import os
import asyncio
import multiprocessing
import gc
from dotenv import load_dotenv


def log_ajoute_fich_lu(valeur):
    """ecrit dans le fichier /home/ad283893/progression.txt la valeur "valeur" qui correspond au pourcentage de document traduit 
    Cette valeur est récupérer est affiché 
    Args:
        valeur (int): estimation du pourcentage de documents trasnformés
    """
    with open("/home/ad283893/progression.txt", "w") as fichier:
        fichier.write(str(valeur))

class Corpus_Stockage :
    def __init__(self):
        self.corpus = {}
        self.converter = DocumentConverter()
        self.liste_nom_fichier = []
    def add_doc(self,name,content,i=1):
        """Ajoute le fichier au corpus

        Args:
            name (_type_): nom du fichier
            content (_type_): contenu du fichier
            i (int, optional): Doit toujours valoir 1 au lancer de la fonction. Defaults to 1.
        """
        if name in self.corpus.keys():#si le fichier contient un homologue on rajoute un 2 ou un 3 ... à la fin
            self.add_doc(self,name+str(i+1),content,i+1)
        else: 
            self.corpus[name]=content
    def get_corpus(self):
        return self.corpus

def corpus_aux(dossier : str,corpus_s : object):
    """
    Fonction réccursive qui remplit l'argument liste_nom_fichier de corpus_s (instance de Corpus_Stockage) avec une liste de
    tout les chemins de chaque fichier
    Args :
        dossier (str) :chemin du dossier qui 
        corpus_s (instance de classe) : instance de la classe Corpus_Stockage
    Returns :
        None
    """
    for nomfichier in os.scandir(dossier):
        if nomfichier.is_dir():#si le fichier est un dossier on re-rappelle la fonction sur ce dossier
            try:
                corpus_aux(dossier+"/"+nomfichier.name,corpus_s)
            except:
                print(f"Dossier {dossier}/{nomfichier.name} illisible")
        else:#sinon on l'ajoute au corpus
            chemin_fich = str(dossier)+"/"+str(nomfichier.name)
            try :
                corpus_s.liste_nom_fichier.append(chemin_fich)
            except:
                print(f"Avertissement : le fichier {chemin_fich} n'a pas pu être lu.")

    return

def creer_corpus_par_gpu(l_document,num_gpu,DOSSIER_SAUVEGARDE,progression_coef,init=False):
    """Cette fonction attribue à un gpu (celui dont le numéro est num_gpu) une liste de document qu'il doit lire 
    puis transformer en texte et enregistrer en .txt dans le DOSSIER_SAUVEGARDE

    Args:
        l_document (list): liste des chemins de tout les documents à traiter
        num_gpu (int): Numéro du GPU sur lequel on souhaite travailler
        DOSSIER_SAUVEGARDE (str): Dossier où vont se sauvegarder les traudtcions en .txt
    """

    i=0
    l_extension_possible = ["docx","pdf","xlsx","html","xhtml","csv","png","jpeg","tiff","bmp","webp","md","markdown","adoc","pptx"]
    os.environ["CUDA_VISIBLE_DEVICES"] = str(num_gpu) #attribution du gpu num_gpu à la fonction
    converter = DocumentConverter()
    if init:#ce n'est que pour le calcul du gpu 0 qu'on indique une approximation du pourcentage d'avancée de la transformation
        progression = 0
    for j in range(0,len(l_doc_transf)//1000):
        l_doc_transf = list(converter.convert_all(l_document[j*1000:(j+1)*1000],raises_on_error=False))
        for i in range(0,len(l_document)):
            content = l_doc_transf[i].document.export_to_markdown()
            nom = l_document[i].replace('/','-')
            with open(DOSSIER_SAUVEGARDE+"/"+nom+".txt","w") as f:
                f.write(content)
            print(f"[+] {nom}")

    #pour la fin
    l_doc_transf = list(converter.convert_all(l_document[len(l_doc_transf)//1000*1000:],raises_on_error=False))
    for i in range(0,len(l_document)):
        content = l_doc_transf[i].document.export_to_markdown()
        nom = l_document[i].replace('/','-')
        with open(DOSSIER_SAUVEGARDE+"/"+nom+".txt","w") as f:
            f.write(content)
        print(f"[+] {nom}")



    # for chemin_fich in l_document:
    #     try:
    #         # if i%100==0:
    #         #     del converter
    #         #     gc.collect()
    #         #     torch.cuda.empty_cache()
    #         #     converter = DocumentConverter()
    #         if chemin_fich.split('.')[-1] in l_extension_possible:

    #             nom_fich = chemin_fich.replace('/','-') #dans le nom du fichier on transforme les / en - 
    #             if DOSSIER_SAUVEGARDE+"/"+nom_fich+".txt" not in os.scandir(DOSSIER_SAUVEGARDE): #si le fichier n'existe pas déjà
    #                 with open(DOSSIER_SAUVEGARDE+"/"+nom_fich+".txt",'w') as f:
    #                     contenu = converter.convert(chemin_fich).document
    #                     f.write(contenu.export_to_markdown())
    #                 print(f"[+] {chemin_fich} -> Téléchargé")
    #             else:
    #                 print(f"[+] {chemin_fich} -> A déjà été téléchargé")
    #         else:
    #             print(f"[-] {chemin_fich} -> FAILED")
    #         if init:
    #             progression+=progression_coef
    #             log_ajoute_fich_lu(progression)

        # except:
        #     print(f"PROBLEME VOIR CORPUS_PAR_GPU {chemin_fich} -> FAILED")
        # i+=1

def creer_corpus_doc_txt(dossier,DOSSIER_SAUVEGARDE):
    """fonction qui écrit dans un DOSSIER_SAUVEGARDE chaque fichier du dossier "dossier" transformer en texte (markdown)
    dans un fichier .txt 

    Args:
        dossier (str): dossier duquel vous voulez extraire les documents et tout les sous-documents (des sous-dossiers)
        DOSSIER_SAUVEGARDE (str): nom du dossier dans lequel vous souhaitez sauvegarder les doc transformés en .txt
    """
    corpus_stockage = Corpus_Stockage()
    print("Parcours de tout les fichiers en cours...")
    corpus_aux(dossier,corpus_stockage)
    print("Parcours de tout les fichiers : Réussi")
    print("Téléchargement du contenu des fichiers...")
    #
    corpus = corpus_stockage.liste_nom_fichier
    l_extension_possible = ["docx","pdf","xlsx","html","xhtml","csv","png","jpeg","tiff","bmp","webp","md","markdown","adoc","pptx"]
    os.makedirs(DOSSIER_SAUVEGARDE, exist_ok=True)
    os_scan_dir = os.listdir(DOSSIER_SAUVEGARDE)
    corpus=[elt for elt in corpus if (elt.split('.')[-1] in l_extension_possible) and elt.replace('/','-')+".txt" not in os_scan_dir]
    n=len(corpus)
     # pour déterminer la progression
    progression_coef = 16/n*100
    #log_ajoute_fich_lu(0)
    #

    #dictionnaire par extension
    l_doc_trie = {}
    for d in corpus:
        extension = d.split(".")[-1]
        if extension in l_doc_trie.keys():
            l_doc_trie[extension].append(d)
        else:
            l_doc_trie[extension]=[d]
    i=0

    for ext,l_chemin in l_doc_trie.items():
        print(f"[{ext}] - Starting... - {str(len(l_chemin))} éléments à transformer")
        repartition_fich_en_coeur = [[l_chemin[j] for j in range(0,len(l_chemin)) if j%16==i] for i in range(0,16)] #Répartit dans 4 listes les documents à transformer afin de donner une liste à chaque gpu
        processus = []
        for i in range(16): #créer un process pour chaque gpu
            if i== 0:
                p = multiprocessing.Process(target=creer_corpus_par_gpu, args=(repartition_fich_en_coeur[i], i%4, DOSSIER_SAUVEGARDE,progression_coef,True))
            else:
                p = multiprocessing.Process(target=creer_corpus_par_gpu, args=(repartition_fich_en_coeur[i], i%4, DOSSIER_SAUVEGARDE,progression_coef))
            processus.append(p)
            p.start()

        for p in processus:
            p.join()
        print(f"[{ext}] - Done")

    print("-> DONE")
    

if __name__=="__main__":
    # PATH_DIRECTORY = "/stic/ESI/Infogérance/Archives/Archives 2017-2022/PréparationRéversibilité/Rapports_Varonis"
    # TXT_DIRECTORY = "/nobackup/ad283893/corpus_test_2"
    #PATH_DIRECTORY = "/stic"
    #TXT_DIRECTORY = "/nobackup/ad283893/corpus_stic"
    # PATH_DIRECTORY = "archive_test/dossier_test"
    # TXT_DIRECTORY = "/nobackup/ad283893/corpus_test"
    #PATH_DIRECTORY=os.getenv("PATH_DIRECTORY")
    #TXT_DIRECTORY=os.getenv("TXT_DIRECTORY")
    PATH_DIRECTORY = "/stic"
    TXT_DIRECTORY = "/nobackup/ad283893/corpus_stic"
    creer_corpus_doc_txt(dossier=PATH_DIRECTORY,DOSSIER_SAUVEGARDE=TXT_DIRECTORY)
    

