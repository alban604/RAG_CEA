# 🧠 RAG Chatbot – Retrieval-Augmented Generation

Ce projet est un **chatbot intelligent** basé sur la technique du **Retrieval-Augmented Generation (RAG)**. Il permet de répondre à des questions en langage naturel en s'appuyant sur un **corpus documentaire personnalisé**.

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

## 🗓 Exemple du rendu 
<img width="1444" height="870" alt="image" src="https://github.com/user-attachments/assets/6c8b9c0f-9748-4275-8461-9479152ba269" />
