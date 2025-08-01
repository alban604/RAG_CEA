# 🧠 RAG Chatbot – Retrieval-Augmented Generation

Ce projet est un **chatbot IA** basé sur la technique du **Retrieval-Augmented Generation (RAG)**. Il permet de répondre à des questions en langage naturel en s'appuyant sur un **corpus documentaire**.

---

## 🚀 Objectif

L'objectif de ce projet est de construire un assistant conversationnel capable de fournir des réponses précises et contextualisées à partir d'un ensemble de documents. Cela permet de :
- Interroger facilement une base documentaire,
- Obtenir des réponses les plus pertinentes possibles
- Obtenir des réponses avec un délai de calcul le plus faible possible

---

## 🧰 Technologies utilisées

- **[Docling](https://github.com/ygarrot/docling)** – Pour l'extraction et la transformation du corpus documentaire en texte exploitable.
- **[Lightrag](https://github.com/Ygarrot/lightrag)** – Pour la mise en œuvre du pipeline RAG (indexation, retrieval, génération).
- **[Gradio](https://gradio.app/)** – Pour l'interface utilisateur simple et interactive.

---

## ⚙️ Fonctionnement

1. **Prétraitement des documents** : Docling est utilisé pour parser et convertir le corpus (PDF, HTML, DOCX, etc.) en texte brut structuré.
2. **Indexation et récupération** : Lightrag indexe les documents transformés et gère le retrieval de contexte pertinent en fonction de la question posée.
3. **Génération de réponse** : Le contexte est injecté dans un modèle de langage pour générer une réponse cohérente et documentée.
4. **Interface** : Gradio fournit une interface Web où l’utilisateur peut poser ses questions et recevoir des réponses instantanément.

---

## 🧱 Structure du code
- **connexion_bd_redis.py** : contient tout les fonctions de transfert et d'utilisation de la base redis qui contient le corpus documentaire transformé en texte (après OCR, etc...)
**generateur_de_data_rag.py** : contient les fonctions qui permettent l'ingestion de donnée par le rag et donc la création de vecteurs et graphes sur ces dernières
**generateur_de_dict_name_chemin.py** : génère un dictionnaire qui associe les clés des documents dans la base de données aux chemins de ceux-ci. Cela permet de récupérer les sources depuis l'interface Gradio
**generateur_de_graphe.py** : permet -en cas d'échec de LightRAG dans la génération du graphe- de le générer manuellement
**interface_Gradio.py** : code de l'interface avec l'utilisateur
**llm.py** : interface avec les llms de mistral auquel on accède par API
**rag_answer.py** : fonction de "requête" du rag pour obtenir une réponse à un prompt
**similarites_mots.py** : contient les fonctions qui permettent de déterminer les suggestions de prompt faites à l'utilisateur 
---

## 🗓 Exemple du rendu 
<img width="1444" height="870" alt="image" src="https://github.com/user-attachments/assets/6c8b9c0f-9748-4275-8461-9479152ba269" />
