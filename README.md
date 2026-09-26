# API
API Météo

Petit script Python en ligne de commande qui récupère les prévisions météo d'une ville via l'API Open-Meteo, en géocodant d'abord le nom de la ville.

Fonctionnement
Demande à l'utilisateur un nombre de jours de prévisions (entre 1 et 16).
Demande le nom d'une ville, puis la géolocalise via l'API de géocodage Open-Meteo.
Récupère les températures min/max prévues pour chaque jour et les affiche dans le terminal.
Prérequis
Python 3.10+
Installation
bash
git clone <url-du-repo>
cd <nom-du-dossier>
pip install -r requirements.txt
Configuration

Le script utilise un fichier .env à la racine du projet pour une éventuelle clé d'API :

API_KEY=votre_clé_ici

Note : l'API Open-Meteo utilisée ici (plan gratuit) ne nécessite pas de clé. La variable API_KEY est optionnelle et peut être laissée vide ou absente.

Utilisation
bash
python main.py

Exemple d'exécution :

Entrez un nombre max 16 : 3
Entrer un nom de ville : Paris
A Paris au coordonnées (48.85, 2.35) le 2026-09-27 il fait 22.1 °C max et 12.3 °C min
A Paris au coordonnées (48.85, 2.35) le 2026-09-28 il fait 20.8 °C max et 11.0 °C min
A Paris au coordonnées (48.85, 2.35) le 2026-09-29 il fait 19.5 °C max et 10.7 °C min
Structure du projet
Fichier	Rôle
main.py	Point d'entrée du programme
api_client.py	Appels à l'API Open-Meteo (géocodage + prévisions) et gestion des erreurs
config.py	Configuration (URLs des API, timeout, clé d'API)
requirements.txt	Dépendances Python
Gestion des erreurs

Le client API définit plusieurs exceptions dédiées (Timeout, HTTPError, JsonError, NetworkError, CityNotFoundError) pour distinguer les différents cas d'échec (ville introuvable, délai dépassé, erreur réseau, etc.).

Limitations connues
Un seul résultat de géocodage est utilisé (le premier retourné par l'API), même en cas d'ambiguïté (villes homonymes).
