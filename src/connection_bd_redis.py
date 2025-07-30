import redis
import os
import requests
import hashlib
import asyncio
import json
import time
from generateur_de_data_rag import rag_gen_data
from generateur_de_dict_name_chemin import ajoute_json

class Bd_Redis:

    def __init__(self,numero_de_db,port=6379):
        self.numero_db = numero_de_db
        self.db = redis.StrictRedis(host="localhost", port=port, db=numero_de_db)
        self.dictio_fich_hash_txt = {}

    def calculate_sha256(self,file_content):
        """Calcule le hachage (identifiant unique au contenu d'un doc) du fichier file

        Args:
            file (str): chemin du fichier

        Returns:
            str: identifiant unique (format hexadécimale)
        """
        return hashlib.sha256(file_content).hexdigest()
        # try:
        #     with open(path,"rb") as f:
        #         for byte_block in iter(lambda: f.read(4096), b""):
        #             sha256_hash.update(byte_block)
        #     return sha256_hash.hexdigest()
        # except FileNotFoundError:
        #     print(f"Le fichier {path} n'a pas été trouvé.")
        # except PermissionError:
        #     print(f"Permission refusée pour lire le fichier {path}.")
        # except Exception as e:
        #     #print(f"Une erreur inattendue est survenue: {e}")
        #     print(str(e)[0:100])

    def get_from_key(self,key):
        return self.db.get(key).decode("utf-8")
    
    def get_content_from_key(self, key):
        """retourne le contenu du document 'key' en markdown

        Args:
            key (str): chemin du fichier avec des - à la place des / et avec un .txt à la fin

        Returns:
            str: contenu du document en markdown
        """
        return json.loads(self.get_from_key(key))["content"]
    
    def add_value(self,key:str,value:str,hash=None,file=None):
        """Ajoute un couple (chemin du fichier, contenu)
            Le contenu sera sous la forme d'un json {"content":value,"hash":hash associé}

        Args:
            key (str): chemin du fichier avec des - à la place des / et avec un .txt à la fin
            value (str): contenu du fichier (markdown)
            hash (str, optional): permet de fournir le hash si déjà calculé (sinon None pour calcul automatique). Defaults to None.
            file (str, optional): si le hash vaut None, le code doit calculer le hash pour cela file prend le contenu du fichier. Defaults to None.
        """
        if not(hash):
            value_add = {"content":value,"hash":str(self.calculate_sha256(file))}
        else:
            value_add = {"content":value,"hash":str(hash)}
        value_json = json.dumps(value_add)
        self.db.set(name=key,value=value_json)
    
    def empty_the_db(self):
        you_sure = input(f"You're going to delete every items from the database {str(self.numero_db)}. Are you sure you want to continue ? (yes/y)")
        if you_sure=="yes"or you_sure=="y" or you_sure=="Y":
            for key in self.db.scan_iter("*"):
                self.db.delete(key)
            print("Database reset")
        else:
            print("Operation cancelled")
    
    def scan_hash(self):
        for key in self.db.scan_iter("*"):
            value = self.db.get(key)
            print(f"{key.decode('utf-8')} : {json.loads(value.decode('utf-8'))['hash']}")

    def scan_keys(self):
        return self.db.scan_iter("*")
    
    def taille(self):
        return len(list(self.db.scan_iter("*")))

    def dict_fich_hash_txt(self,origin_path):
        """Génère un dictionnaire qui à chaque clé (chemin du fichier avec - à la place ...) associe le hash du fichier correspondant
        Ce dictionnaire est stocké dans self.dictio_fich_hash_txt

        Args:
            origin_path (str): chemin du dossier à partir duquel on veut générer le dictionnaire 
        """
        for nomfichier in os.scandir(origin_path):
            if nomfichier.is_dir():#si le fichier est un dossier on re-rappelle la fonction sur ce dossier
                try:
                    self.dict_fich_hash_txt(origin_path+"/"+nomfichier.name)
                except:
                    pass
            else:#sinon on l'ajoute au dictionnaire
                chemin_fich = str(origin_path)+"/"+str(nomfichier.name)
                try :
                    nom_txt = chemin_fich.replace("/","-")+".txt"
                    with open(chemin_fich,"rb") as f:
                        self.dictio_fich_hash_txt[nom_txt]=self.calculate_sha256(f.read())
                except Exception as e:
                    print(f"Hachage de {chemin_fich} : FAILED")
                    print(e)

    def add_from_corpus_txt(self,corpus_txt,origin_path,no_maj=False):
        """ajoute les fichiers d'un dossier ne contenant que des txt (transformé par Docling) à la base de donnée
        Cette fonction permet de faire la transition du stockage en dossier local au stockage en base de donnée.

        Args:
            corpus_txt (str): chemin du dossier contenant les txts
            origin_path (str): chemin du dossier d'où viennent les documents (avant d'avoir été transformé en txt) ex :/stic
            no_maj (str) : option de debbugage. Si True le dictionnaire de hachage sera sauvegardé dans un json en local, si le programme doit 
            être relancé à cause d'un problème, le dictionnaire n'aura pas besoin d'être recalculé. 
            ATTENTION Si vous changez de source de données ou changer une partie des données (maj) il faut absolument que no_maj=True
        """
        #corpus_txt => dossier contenant que des txt (déjà passer dans docling)
        #Etape 1 : Etablir un dictionnaire d'équivalence entre chaque fichier et son hash (de document original et non de la version txt)
        if not(os.path.isfile("dictio_hash.json")) or not(no_maj):
            print("Génération du dictionnaire de hachage...")
            self.dict_fich_hash_txt(origin_path)
            if no_maj:
                with open("dictio_hash.json","w") as f:
                    json.dump(self.dictio_fich_hash_txt,fp=f)
            print("[+DICTIONAIRE]")
        else:
            with open("dictio_hash.json","r") as f:
                self.dictio_fich_hash_txt=json.load(f)
        i=1

        #Etape 2 : Ajouter tout les fichiers à la base de données
        for doc in os.scandir(corpus_txt):
            file_name = doc.name
            
            with open(corpus_txt+"/"+file_name,'r') as f:
                try:
                    # print("1--------------------------------")
                    self.add_value(file_name,f.read(),hash=self.dictio_fich_hash_txt[file_name])
                    print(f"[+DB] Document n°{i} {file_name} ajouté à la base de donnée {self.numero_db}")
                except Exception as exp:
                    print(f"[-DB] Document n°{i} {file_name} FAILED") #cela est souvent du au fait qu'on a pas les permissions pour lire le doc donc son hash n'a pas pu etre calculé
                    # print("2---------------------------------------")
                    # print(type(exp))
                    # print(exp)
                    pass
            i+=1
        print("[DONE]")

def get_all_doc_name_from_a_repertory(repertory_path):
    """Retourne une liste avec tout les chemins des documents du dossier repertory_path (réccursif)

    Args:
        repertory_path (str): chemin du dossier parent dont on veut étudier le contenu

    Returns:
        List[str]: Liste avec les chemins des documents qui sont présents dans le dossier repertory_path (et ses sous-dossiers)
    """
    dossier_paths = []
    file_paths = []
    for nomfichier in os.scandir(repertory_path):
        if nomfichier.is_dir():
            dossier_paths.append(repertory_path+"/"+nomfichier.name)
        else:
            file_paths.append(repertory_path+"/"+nomfichier.name)
    #On lit tout les dossiers
    to_return = file_paths
    for doss in dossier_paths:
        to_return += get_all_doc_name_from_a_repertory(doss)
    return to_return

async def process_one_doc_trough_docling(chemin_doc,return_file_name_and_path=False):
    """Envoie un document à doclig-serve pour en récupérer le contenu en markdown

    Args:
        chemin_doc (str): chemin du fichier que l'on souhaite trasnformé (avec des /)
        return_file_binary (bool, Default : False) : doit valoir True si utilisé par process_x_doc...
            Change le return 
    Returns:
        Si return_file_binary == False
            str: contenu du document en markdown
        Si return_file_name_and_path == True
            Tuple(str,str,str) : (chemin_du_doc, contenu en markdown)
    """
    try :
        print(f"[{chemin_doc}] - Envoi du doc à docling")
        with open(chemin_doc, 'rb') as f:
            files = {'files': (chemin_doc,f)} 
            result = requests.post("http://aar002:5001/v1alpha/convert/file/async", files=files) #envoie le doc à docling
        for a in range(0,1000000):
            id_doc = result.json()['task_id'] #récupère l'id du doc
            status = requests.get(f"http://aar002:5001/v1alpha/status/poll/{id_doc}").json()['task_status']
            if status=='started':
                pass
            if status=='success':
                if return_file_name_and_path:
                    return chemin_doc,requests.get(f"http://aar002:5001/v1alpha/result/{id_doc}").json()["document"]["md_content"]
                return requests.get(f"http://aar002:5001/v1alpha/result/{id_doc}").json()["document"]["md_content"]
        print("Le document n'a pas eu le temps d'être processé par docling")
        print("Vérifiez qu'il est ou non lisible par docling ou modifiez le for a in range avec une valeur plus grande")
        return None
    except:
        print("Erreur dans la fonction process_one_doc_trough_docling")
async def process_x_doc_trough_docling(list_chemin_doc):
    """Envoie x document à doclig-serve pour en récupérer le contenu en markdown

    Args:
        list_chemin_doc (List[str]): chemin du fichier que l'on souhaite transformé (avec des /)

    Returns:
        List[(str,str,str)]: liste de tuple de format (chemin_du_doc, contenu en markdown)
    """
    #lancement de la transformation - Etape 1 : envoie du doc à docling
    async with asyncio.TaskGroup() as tg: #réalise les ainsert des données dans le rag en simultanée
        tasks = []
        for chemin_doc in list_chemin_doc:
            task = tg.create_task(process_one_doc_trough_docling(chemin_doc,True))
            tasks.append(task)
    
        results = await asyncio.gather(*tasks)

    return results
#process_one_doc_trough_docling("archive_test/SSI/DSSN-CS-I-2019-010.pdf")
#print(asyncio.run(process_x_doc_trough_docling(["/appli/stage_rag_ov/archive_test/SSI/DSSN-CS-I-2019-010.pdf","/appli/stage_rag_ov/archive_test/SSI/RSSN-SSI-02-05.pdf","/appli/stage_rag_ov/archive_test/SSI/joe_20230802_0177_0001.pdf"])))

async def add_db_from_repertory(db,repertory_path,parallel_docling_doc=100):
    """Ajoute un repertoire de document de tout type (ex : pdf) (réccursivement) à une base de donnée 
        NOTES : Docling-serve étant très long : il est recommandé de passer par un dossier de document txt sur aar002 plutot que d'utiliser cette fonction
    Args:
        db (_type_): _description_
        repertory_path (_type_): _description_
        parallel_docling_doc (int, optional): _description_. Defaults to 100.
    """
    all_chemin = get_all_doc_name_from_a_repertory(repertory_path)
    split_all_chemin = [all_chemin[a*parallel_docling_doc:(a+1)*parallel_docling_doc] for a in range(0,len(all_chemin)//parallel_docling_doc)]+[all_chemin[len(all_chemin)//parallel_docling_doc:]]
    for list_chemin in split_all_chemin:
        l_result = await process_x_doc_trough_docling(list_chemin)
        for chemin,contenu in l_result:
            cle = chemin.replace("/","-")+".txt" #pour de la compatibilité avec le reste du système qui est adpaté au clé du format chemin-du-doc.pdf.txt
            with open(chemin,'rb') as f:
                db.add_value(cle,contenu,file=f.read())

def update_data_base(db,dossier,vector_graphe_storage,maj_db=True,maj_data_rag=True):
    """Fonction qui met à jour la base de donnée si des documents ont été modifiés ou été rajoutés dans "dossier"
    Notes : cette fonction est réccursive 
    Args:
        db (<object>): objet de la classe bd_Redis
        dossier (str): chemin du dossier que l'on compare à la bd pour voir si des docs ont été changés ou rajoutés (réccursif)
        vector_graphe_storage (str): Dossier dans lequel on stocke les vecteurs du rag (pour mise à jour du du json_from_name_to_chemin.json et pour mise à jour du rag)
        maj_db (bool) : Si False, la base de donnée ne sera pas mise à jour, les documents nécessitant une mise à jour seront retournés
        maj_data_rag (bool): Si True, va faire ingérer automatiquement les données à mettre à jour au rag dont les fichiers de vecteurs et graphe sont stockés dans vector_graph_storage les fichiers de vecteurs et graphe.
    """
    db_scan_iter = list(db.scan_keys())
    print(f"[...] Etude du dossier {str(dossier)}")
    doc_a_modif_to_chemin = {}
    doc_a_modif_rag = []
    for nomfichier in os.scandir(dossier):
            print("Etude du fichier : " +str(nomfichier.name))
            if nomfichier.is_dir():#si le fichier est un dossier on re-rappelle la fonction sur ce dossier
                try:
                    update_data_base(db,dossier+"/"+nomfichier.name,vector_graphe_storage)
                except:
                    print(f"Dossier {dossier}/{nomfichier.name} illisible")
            else:
                chemin_fich = str(dossier)+"/"+str(nomfichier.name)
                
                nom_txt = chemin_fich.replace("/","-")+".txt"
                found = False
                for key in db_scan_iter:
                    if nom_txt==key.decode("utf-8"):
                        found=True

                        #on regarde si le fichier n'a pas été mis à jour
                        value = db.get_from_key(key)
                        hash_db = json.loads(value)['hash']
                        with open(dossier+"/"+nomfichier.name,'rb') as f:
                            content = f.read()
                            hachage = db.calculate_sha256(content)
                            time.sleep(10)
                            if hash_db != hachage:
                                #alors on procède à la mise à jour
                                try :
                                    print(f"Le hash du document {nom_txt} a changé.")
                                    #print(str(hash_db)+" -> "+str(hachage))
                                    if maj_db:
                                        content = asyncio.run(process_one_doc_trough_docling(dossier+"/"+nomfichier.name))
                                        db.add_value(nom_txt,content,hash=hachage)
                                    doc_a_modif_rag.append(nom_txt)
                                except Exception as e:
                                    print(f"[-] Le document {dossier}/{nomfichier.name} n'a pas pu être transformé par docling")
                        break
    
                if not(found):
                    try : 
                        print(f"Document {nom_txt} non trouvé")
                        if maj_db:
                            content = asyncio.run(process_one_doc_trough_docling(dossier+"/"+nomfichier.name))
                            with open(dossier+"/"+nomfichier.name,'rb') as f:
                                db.add_value(nom_txt,content,file=f.read())
                            doc_a_modif_to_chemin[nom_txt]=dossier+"/"+nomfichier.name
                        doc_a_modif_rag.append(nom_txt)
                    except Exception as e :
                        print(e)
                        print(f"[-] Le document {dossier}/{nomfichier.name} n'a pas pu être transformé par docling")
    print(f"[++] Dossier consulté : {str(dossier)}")
    if doc_a_modif_rag!=[] and maj_db: #Il y a des documents à mettre à jour dans le rag
        print("Les documents suivants vont être mis à jour/ ajouter :")
        print(doc_a_modif_rag)
        if maj_data_rag:
            asyncio.run(rag_gen_data(vector_graphe_storage,db,doc_a_modif_rag))
    #mise à jour du json_from_name_to_chemin.json pour citer les sources avec les fichiers qui ont été ajoutés à la base de données
    if maj_db:
        ajoute_json(doc_a_modif_to_chemin,vector_graphe_storage)

    return doc_a_modif_rag

async def appel_rag_gen_data(vector_graph_storage,num_bd,list_fichier=None):
    """Appel la fonction rag_genere_data du fichier generateur_de_data_rag.py
    rag_genere_data créé/met à jour l'ensemble des vecteurs et graphes nécésssaires à LightRAG

    Args:
        vector_graph_storage (str): chemin du dossier dans lequel on veut stocker les vecteurs et graphe généré par LightRAG
        num_bd (int): numéro de la base de donnée de laquelle on souhaite exploiter les données
        list_fichier (List[str], optional): Si vaut None, tout les fichiers de num_bd seront ingérés. Si ne vaut pas None, seuls les fichiers de list_fichier seronts ingérés. Defaults to None.
    """
    bd = Bd_Redis(num_bd)
    await rag_gen_data(vector_graph_storage,bd,list_fichier)

if __name__=="__main__":
    #print(list(os.listdir('partial_corpus_stic_ESI')))
    #asyncio.run(appel_rag_gen_data("Vector_partial_stic_v2",1,list(os.listdir('partial_corpus_stic_ESI'))))
    #bd_1 = Bd_Redis(1)
    #print(bd_1.taille())
    # print(list(bd_2.scan_keys())[0])
    # print(bd_2.get_content_from_key(list(bd_2.scan_keys())[0]))
    
    #bd_1 = Bd_Redis(1)
    #print(bd_1.get_content_from_key("-stic-ESI-Infogérance-Archives-Archives 2017-2022-Maintenance Matériel Multimedia-Consultation-DCE-Complement_2_DCE_160135.pdf.txt".encode("utf-8")))
    #update_data_base(bd_1,"wiki_ssi_content","Vector_wiki_ssi")
    #bd_1.add_from_corpus_txt("/appli/stage_rag_ov/partial_corpus_stic_ESI","/stic",no_maj=True)
    #bd_1.add_from_corpus_txt("corpus_wiki_ssi","wiki_ssi_content")
    bd = Bd_Redis(3)
    # #asyncio.run(add_db_from_repertory(bd,"archive_test/ssi_deux_doc",5))
    # list_change = update_data_base(bd,"archive_test/ssi_deux_doc","Vector_wiki_ssi_entraine",maj_db=True,maj_data_rag=False)
    # print(list_change)
    # l = list(bd.scan_keys())
    # for obj in l:
    #     print(obj)
    