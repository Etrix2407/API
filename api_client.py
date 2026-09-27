"""Client pour l'API Open-Meteo (géocodage + prévisions météo).

Ce module regroupe :
- les exceptions dédiées à la gestion des erreurs d'appel API,
- la fonction bas niveau `_get_json` qui effectue les requêtes HTTP,
- les fonctions métier `get_coordinate` et `get_Forecast`,
- la fonction `run` qui orchestre l'interaction avec l'utilisateur.
"""

import config as c
import requests, json


class APIError(Exception):
    """Exception de base pour toutes les erreurs liées à l'API."""
    pass

class Timeout(APIError):
    """Levée quand une requête dépasse le délai d'attente configuré.

    Args:
        url (str): URL appelée.
        timeout (int | float): Délai d'attente (en secondes) qui a été dépassé.
    """
    def __init__(self, url, timeout):
        self.url = url
        self.timeout = timeout
        super().__init__(f"temps {timeout} dépasser sur {url}")

class HTTPError(APIError):
    """Levée quand le serveur répond avec un code HTTP d'erreur.

    Args:
        url (str): URL appelée.
        status_code (int): Code de statut HTTP retourné.
        reason (str): Raison associée au code de statut.
    """
    def __init__(self, url, status_code, reason):
        self.url = url
        self.code = status_code
        self.reason = reason
        super().__init__(f"Error {status_code} : {reason} ({url})")

class JsonError(APIError):
    """Levée quand la réponse de l'API n'a pas pu être décodée en JSON.

    Args:
        url (str): URL appelée.
    """
    def __init__(self, url):
        super().__init__(f"Erreur au niveau du .json")

class NetworkError(APIError):
    """Levée en cas d'erreur réseau (connexion impossible, DNS, etc.).

    Args:
        url (str): URL appelée.
        original_error (Exception): Exception d'origine levée par `requests`.
    """
    def __init__(self, url, original_error):
        self.url = url
        self.original_error = original_error
        super().__init__(f"erreur résaux sur {url} : {original_error}")

class CityNotFoundError(APIError):
    """Levée quand la géolocalisation ne retourne aucun résultat pour la ville.

    Args:
        city_name (str): Nom de la ville recherchée.
    """
    def __init__(self, city_name):
        self.city_name = city_name
        super().__init__(f"Ville introuvable : '{city_name}'")

def _get_json(url, params):
    """Effectue une requête GET et retourne le corps de la réponse en JSON.

    Ajoute automatiquement l'en-tête d'authentification si une clé d'API
    est définie dans la configuration, puis convertit les exceptions
    levées par `requests` en exceptions du module (`Timeout`, `HTTPError`,
    `NetworkError`, `JsonError`, `APIError`).

    Args:
        url (str): URL de l'endpoint à appeler.
        params (dict): Paramètres de la requête (query string).

    Returns:
        dict: Contenu de la réponse désérialisé depuis le JSON.

    Raises:
        Timeout: Si le délai d'attente est dépassé.
        HTTPError: Si le serveur retourne un code d'erreur HTTP.
        NetworkError: En cas d'erreur de connexion réseau.
        JsonError: Si la réponse n'est pas un JSON valide.
        APIError: Pour toute autre erreur liée à `requests`.
    """
    headers = {"Authorization": f"Bearer {c.API_KEY}"} if c.API_KEY else {}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=c.TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
         raise Timeout(url, c.TIMEOUT)
    except requests.exceptions.HTTPError:
          raise HTTPError(url, response.status_code, response.reason)
    except requests.exceptions.ConnectionError as error:
        raise NetworkError(url, error)
    except requests.exceptions.JSONDecodeError:
        raise JsonError(url)
    except requests.exceptions.RequestException as error:
        raise APIError(f"Erreur réseaux : {error}")

def get_coordinate():
    """Demande un nom de ville à l'utilisateur et récupère ses coordonnées.

    Interroge l'API de géocodage Open-Meteo et retient le premier résultat
    retourné en cas d'ambiguïté (plusieurs villes homonymes).

    Returns:
        tuple[float, float, str]: Un triplet (latitude, longitude, nom de la
            ville) correspondant au premier résultat de la recherche.

    Raises:
        CityNotFoundError: Si aucune ville ne correspond au nom saisi.
        APIError: Si l'appel à l'API de géocodage échoue.
    """
    name = input("Entrer un nom de ville : ")
    params = {"name": name}

    data = _get_json(c.GEOCODING_URL, params=params)
    results = data.get("results")
    if not results:
        raise CityNotFoundError(name)


    first_result = results[0]
    return (first_result.get("latitude"), first_result.get("longitude"), first_result.get("name"))

def get_Forecast(nb_day=1):
    """Récupère et affiche les prévisions météo pour une ville donnée.

    Demande d'abord les coordonnées de la ville via `get_coordinate`, puis
    interroge l'API de prévisions Open-Meteo pour obtenir les températures
    min/max de chaque jour et les affiche dans le terminal. Si la
    géolocalisation échoue, l'erreur est affichée et la fonction s'arrête.

    Args:
        nb_day (int): Nombre de jours de prévisions à récupérer (1 à 16).
            Vaut 1 par défaut.

    Returns:
        None: La fonction affiche directement les résultats ; elle retourne
            None immédiatement en cas d'erreur lors de la géolocalisation.

    Raises:
        APIError: Si l'appel à l'API de prévisions échoue.
    """
    try:
        coordinates = get_coordinate()

    except APIError as e:
        print(f"Error : {e}")
        return None

    latitude, longitude, name = coordinates

    params = {"latitude": latitude,
                "longitude": longitude,
                "timezone": "auto",
                "forecast_days": nb_day,
                "daily": ["temperature_2m_max", "temperature_2m_min"]}

    data = _get_json(c.FORECAST_URL, params=params)

    temperature_unit = data.get("daily_units").get("temperature_2m_max")
    daily = data.get("daily")
    for time, temperature_2m_max, temperature_2m_min in zip(daily.get("time"), daily.get("temperature_2m_max"), daily.get("temperature_2m_min")):
        print(f"A {name} au coordonées {latitude, longitude} le {time} il {"fait" if c.to_day == time else "fera"} {temperature_2m_max} {temperature_unit} max et {temperature_2m_min} {temperature_unit} min")



def run():
    """Point d'entrée principal du programme.

    Demande à l'utilisateur un nombre de jours de prévisions valide (entre
    1 et 16, en redemandant tant que la saisie est invalide), puis lance
    la récupération et l'affichage des prévisions via `get_Forecast`.

    Returns:
        None
    """
    nb_day = None
    while nb_day is None or nb_day > 16 or nb_day < 1:

        try:
            nb_day = int(input("Entrez un nombre max 16 : "))
            if nb_day > 16 or nb_day < 1:
                print("Le nombre doit être entre 1 et 16.")
        except ValueError:
            print("Veuillez entrer un nombre entier valide.")

    get_Forecast(nb_day)



    



    

