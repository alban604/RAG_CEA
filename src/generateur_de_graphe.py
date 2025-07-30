import asyncio
import json
import re
from typing import Any, Dict, List
from datetime import datetime
import traceback

def sanitize_text(text: str) -> str:
    """Nettoie le texte en supprimant les balises < > et en échappant les caractères XML."""
    if not text:
        return ""
    # Convertir en chaîne si ce n'est pas déjà le cas (par ex. si un int ou float passe par là)
    text = str(text) 
    text = re.sub(r'<[^>]+>', '', text)
    # L'ordre d'échappement est important : d'abord '&', sinon '&amp;' deviendrait '&amp;amp;'
    text = (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))
    return text

def sanitize_id(node_id: str) -> str:
    """
    Nettoie les IDs pour les rendre compatibles avec XML.
    Remplace les caractères non autorisés et les espaces par des underscores.
    """
    if not node_id:
        return "id_manquant"
    
    # Convertir en chaîne si ce n'est pas déjà le cas
    node_id = str(node_id)

    # XML NCNames (pour les IDs) peuvent contenir lettres, chiffres, underscores, tirets, points.
    # Ils doivent commencer par une lettre ou un underscore.
    # Simplifions pour éviter tout caractère problématique non géré.
    # Remplacer tout ce qui n'est pas alphanumérique ou underscore par un underscore
    node_id = re.sub(r'[^\w.-]', '_', node_id) # \w = [a-zA-Z0-9_]

    # S'assurer que l'ID ne commence pas par un chiffre, un point ou un tiret (si c'est le cas, préfixer par '_')
    if re.match(r'^[0-9.-]', node_id):
        node_id = '_' + node_id
    
    # Éliminer les underscores consécutifs (par exemple, "test__id" -> "test_id")
    node_id = re.sub(r'_{2,}', '_', node_id)

    # Supprimer les underscores au début ou à la fin si l'ID n'est pas seulement un underscore
    node_id = node_id.strip('_')
    if not node_id: # Si l'ID devient vide après nettoyage (ex: "   ")
        return "empty_id"

    return node_id[:100]  # Limiter la longueur pour éviter des IDs trop longs

async def generate_lightrag_graphml(entities_file: str, relationships_file: str, output_file: str) -> None:
    """Parfois lorsque Lightrag ingère des données, il ne parvient pas à créer le graphe (cela se traduit par un fichier graph_chunk_entity_relation.graphml vide)
    Cette fonction permet à partir de vdb_entities et vdb_relationships de recréer un fichier de graphe
    Args:
        entities_file (str): chemin vers le fichier vdb_entities.json
        relationships_file (str): chemin vers le fichier vdb_relationships.json
        output_file (str): chemin vers le graphe (pour LightRAG il doit se nommer graph_chunk_entity_relation.graphml)
    """
    try:
        # Charger les données
        with open(entities_file, 'r', encoding='utf-8') as f:
            entities_data = json.load(f)

        with open(relationships_file, 'r', encoding='utf-8') as f:
            relationships_data = json.load(f)

        # --- DÉCLARATION DES CLÉS (KEY) : Très important pour GraphML ---
        # J'ai ajusté les attr.name pour qu'ils soient plus lisibles que d0, d1...
        # et correspondent mieux à votre usage. L'ID (d0, d1, etc.) reste le même.
        graphml_header = """<?xml version='1.0' encoding='utf-8'?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
    <key id="d11" for="edge" attr.name="created_at" attr.type="long"/>
    <key id="d10" for="edge" attr.name="file_path" attr.type="string"/>
    <key id="d9" for="edge" attr.name="source_id" attr.type="string"/> 
    <key id="d8" for="edge" attr.name="keywords" attr.type="string"/>
    <key id="d7" for="edge" attr.name="description" attr.type="string"/>
    <key id="d6" for="edge" attr.name="weight" attr.type="double"/>
    <key id="d5" for="node" attr.name="created_at" attr.type="long"/>
    <key id="d4" for="node" attr.name="file_path" attr.type="string"/>
    <key id="d3" for="node" attr.name="source_id" attr.type="string"/>
    <key id="d2" for="node" attr.name="description" attr.type="string"/>
    <key id="d1" for="node" attr.name="type" attr.type="string"/>
    <key id="d0" for="node" attr.name="name" attr.type="string"/>
    <graph edgedefault="undirected">""" # <-- `edgedefault="undirected"` est un bon choix par défaut si pas de direction spécifique.

        graphml_footer = """
    </graph>
</graphml>"""

        graphml_nodes = []
        graphml_edges = []
        
        # Ensemble pour suivre les IDs de nœuds déjà ajoutés et éviter les doublons
        # et pour vérifier si les sources/cibles des arêtes existent
        existing_node_ids = set()
        existing_edges = set()  # Pour suivre les arêtes existantes et empêcher les doublons

        # Traitement des entités (nœuds)
        for entity in entities_data.get('data', []): # Utiliser .get pour éviter KeyError si 'data' manque
            # Utilisez entity_name comme base pour l'ID du nœud, puis nettoyez-le.
            # L'ID interne de l'entité (si présente) pourrait aussi être une bonne base.
            raw_node_id_base = entity.get("entity_name") or entity.get("id") # Prioriser entity_name, sinon 'id'
            
            if not raw_node_id_base: # Si ni entity_name ni id n'existent
                print(f"Avertissement: Entité sans 'entity_name' ni 'id', ignorée: {entity}")
                continue

            node_id = sanitize_id(raw_node_id_base)
            
            # Gestion des IDs en doublon après assainissement
            original_node_id = node_id
            counter = 1
            while node_id in existing_node_ids:
                node_id = f"{original_node_id}_{counter}"
                counter += 1
                if counter > 1000: # Prévention de boucle infinie pour des IDs très similaires
                    print(f"Avertissement: Trop de doublons pour l'ID '{original_node_id}'. Ignoré.")
                    node_id = None # Marquer comme non utilisable
                    break
            
            if node_id is None: # Si on a échoué à trouver un ID unique
                continue

            existing_node_ids.add(node_id) # Ajouter l'ID nettoyé et unique

            node_content = f"""
        <node id="{node_id}">
            <data key="d0">{sanitize_text(entity.get("entity_name", ""))}</data>
            <data key="d1">{sanitize_text(entity.get("entity_type", "category"))}</data>
            <data key="d2">{sanitize_text(entity.get("content", ""))}</data>
            <data key="d3">{sanitize_text(entity.get("source_id", "manual"))}</data>
            <data key="d4">{sanitize_text(entity.get("file_path", ""))}</data>
            <data key="d5">{int(datetime.now().timestamp())}</data>
        </node>"""
            graphml_nodes.append(node_content)

        # Traitement des relations (arêtes)
        edge_counter = 0 # Utilisé si vous voulez des IDs d'arêtes uniques (optionnel pour GraphML)
        duplicate_count = 0  # Pour compter les doublons ignorés
        
        for relation in relationships_data.get('data', []):
            raw_source_id = relation.get("src_id")
            raw_target_id = relation.get("tgt_id")

            if not raw_source_id or not raw_target_id:
                print(f"Avertissement: Relation avec source ou cible manquante, ignorée: {relation}")
                continue

            source_id = sanitize_id(raw_source_id)
            target_id = sanitize_id(raw_target_id)
            
            # Vérifier si les nœuds source et cible existent vraiment dans notre ensemble d'IDs traités
            if source_id not in existing_node_ids:
                print(f"Avertissement: Nœud source '{source_id}' de la relation '{raw_source_id}' introuvable, relation ignorée.")
                continue
            if target_id not in existing_node_ids:
                print(f"Avertissement: Nœud cible '{target_id}' de la relation '{raw_target_id}' introuvable, relation ignorée.")
                continue

            # Créer une clé unique pour l'arête (non orientée donc triée)
            edge_key = tuple(sorted((source_id, target_id)))
            
            # Vérifier si cette arête existe déjà
            if edge_key in existing_edges:
                duplicate_count += 1
                print(f"Avertissement: Arête dupliquée entre {source_id} et {target_id} ignorée.")
                continue
                
            # Ajouter la nouvelle arête à l'ensemble des arêtes existantes
            existing_edges.add(edge_key)

            edge_content = f"""
        <edge source="{source_id}" target="{target_id}">
            <data key="d6">{float(relation.get("weight", 1.0))}</data>
            <data key="d7">{sanitize_text(relation.get("description", "no_infos"))}</data>
            <data key="d8">{sanitize_text(relation.get("keywords", "no_infos"))}</data>
            <data key="d9">{sanitize_text(relation.get("source_id", "manual"))}</data>
            <data key="d10">{sanitize_text(relation.get("file_path", ""))}</data>
            <data key="d11">{int(datetime.now().timestamp())}</data>
        </edge>"""
            graphml_edges.append(edge_content)
            edge_counter += 1

        # Assemblage final
        graphml_content = (
            graphml_header + 
            "\n".join(graphml_nodes) + 
            "\n".join(graphml_edges) + 
            graphml_footer
        )

        if duplicate_count > 0:
            print(f"{duplicate_count} arêtes en doublon ont été ignorées.")

        # Sauvegarde
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(graphml_content)
        
        print(f"Graphe GraphML généré avec succès dans '{output_file}'")
        print(f"Statistiques: {len(existing_node_ids)} nœuds, {edge_counter} arêtes uniques")

    except FileNotFoundError as e:
        print(f"Erreur: Fichier non trouvé. Assurez-vous que '{e.filename}' existe.")
        traceback.print_exc()
    except json.JSONDecodeError as e:
        print(f"Erreur de décodage JSON dans l'un des fichiers. Vérifiez le format JSON.")
        traceback.print_exc()
    except Exception as e:
        print(f"Une erreur inattendue s'est produite: {e}")
        traceback.print_exc()

# Exemple d'utilisation
if __name__ == "__main__":
    # Créez des fichiers JSON d'exemple si vous n'en avez pas pour tester
    # Supposons que vdb_entities.json et vdb_relationships.json existent dans Vector_wiki_ssi/
    
    # Exemple de contenu pour vdb_entities.json
    sample_entities = {
        "data": [
            {"entity_name": "Global Climate Change Summit", "entity_type": "event", "content": "The Global Climate Change Summit is an event held by the United Nations.", "source_id": "chunk-c8585a0099d20edb2fa5290feb659136", "file_path": "wiki_ssi_content-wiki_p10_CST avec slurm.html"},
            {"entity_name": "Environmental Sustainability", "entity_type": "concept", "content": "Environmental sustainability is a key topic discussed at the summit.", "source_id": "chunk-c8585a0099d20edb2fa5290feb659136", "file_path": "wiki_ssi_content-wiki_p10_CST avec slurm.html"},
            {"entity_name": "SCI", "entity_type": "acronym", "content": "Information about SCI.", "source_id": "chunk-13cd32f91ec9a9285f4313a2c06cac7f", "file_path": "wiki_ssi_content-wiki_p48_Verif-conf-nx-client.html"},
            {"entity_name": "NX Client", "entity_type": "software", "content": "Information about NX Client.", "source_id": "chunk-13cd32f91ec9a9285f4313a2c06cac7f", "file_path": "wiki_ssi_content-wiki_p48_Verif-conf-nx-client.html"},
            {"entity_name": "Vérification de la configuration du client NX", "entity_type": "process", "content": "This process checks the NX client configuration.", "source_id": "chunk-13cd32f91ec9a9285f4313a2c06cac7f", "file_path": "wiki_ssi_content-wiki_p48_Verif-conf-nx-client.html"}
        ]
    }


    VECTOR_STORAGE = "Vector_partial_stic_v2"
    
    entities_file = VECTOR_STORAGE+'/vdb_entities.json'
    relationships_file = VECTOR_STORAGE+'/vdb_relationships.json'
    output_file = VECTOR_STORAGE+'/graph_chunk_entity_relation.graphml'
    
    asyncio.run(generate_lightrag_graphml(entities_file, relationships_file, output_file))