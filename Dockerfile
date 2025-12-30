# Base image : Toujours vérifier la dernière version stable sur Docker Hub
FROM n8nio/n8n:latest

USER root

# Installation de Python et PIP pour les scripts Data avancés
RUN apk add --update --no-cache python3 py3-pip build-base

# Création d'un environnement virtuel pour éviter les conflits
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Installation des librairies Data & IA essentielles
# Adapte cette liste selon tes besoins (ex: numpy, requests, pandas)
RUN pip install pandas requests numpy gnews newspaper3k lxml_html_clean

# Retour à l'utilisateur node pour la sécurité (Least Privilege Principle)
USER node