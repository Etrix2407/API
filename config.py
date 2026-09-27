"""Configuration du projet : URLs des API, timeout et clé d'API.

Charge les variables d'environnement depuis un fichier `.env` (via
python-dotenv) et expose les constantes utilisées par `api_client.py`.
"""

import os
from dotenv import load_dotenv
from datetime import date

# Date du jour au format ISO (ex: "2026-09-27")
to_day = date.today().isoformat()

# Chargement des variables d'environements
load_dotenv()

# URL de l'API de géocodage Open-Meteo (résolution nom de ville -> coordonnées).
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
# URL de l'API de prévisions météo Open-Meteo.
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
# Délai d'attente (en secondes) pour les requêtes HTTP.
TIMEOUT = 10
# Clé d'API optionnelle, lue depuis la variable d'environnement API_KEY.
API_KEY = os.getenv("API_KEY")