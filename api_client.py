"""Client pour l'API Open-Meteo (géocodage + prévisions météo).
 
Ce module regroupe :
- les exceptions dédiées à la gestion des erreurs d'appel API,
- la fonction bas niveau `_get_json` qui effectue les requêtes HTTP,
- les fonctions métier `get_coordinate` et `get_forecast`,
- la fonction d'affichage `display_forecast`,
- les fonctions de saisie `get_nb_day` et `get_city`,
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

def get_coordinate(name):
    """Récupère les coordonnées d'une ville via l'API de géocodage.

    Interroge l'API Open-Meteo et retient le premier résultat en cas
    d'homonymes.

    Args:
        name (str): Nom de la ville recherchée.

    Returns:
        tuple[float, float] | None: Un couple (latitude, longitude), ou None
            si aucune ville ne correspond au nom.

    Raises:
        APIError: Si l'appel à l'API de géocodage échoue.
    """
    
    params = {"name": name}

    city_data = _get_json(c.GEOCODING_URL, params=params)

    results = city_data.get("results")
    if results is not None:
        first_result = results[0]

        return (first_result.get("latitude"), first_result.get("longitude"))
    
    return None





def get_forecast(latitude, longitude, nb_day=1):
    """Récupère les prévisions de températures pour une ville.

    Géocode d'abord la ville via `get_coordinate`, puis interroge l'API de
    prévisions pour obtenir les températures min/max de chaque jour.

    Args:
        name (str): Nom de la ville.
        nb_day (int): Nombre de jours de prévisions (1 à 16). Vaut 1 par défaut.

    Returns:
        tuple[dict, str] | None: Un couple (daily, unité), où `daily` contient
            les listes "time", "temperature_2m_max" et "temperature_2m_min",
            et l'unité est par exemple "°C". Retourne None si la ville
            est introuvable.

    Raises:
        APIError: Si l'un des appels à l'API échoue.
    """

    params = {"latitude": latitude,
                "longitude": longitude,
                "timezone": "auto",
                "forecast_days": nb_day,
                "daily": ["temperature_2m_max", "temperature_2m_min"]}

    data = _get_json(c.FORECAST_URL, params=params)

    temperature_unit = data.get("daily_units").get("temperature_2m_max")
    daily = data.get("daily")
    return daily, temperature_unit
        

def display_forecast(coordinate, name, nb_day):
    """Affiche dans le terminal les prévisions d'une ville, jour par jour.

    Les erreurs d'API sont interceptées et affichées au lieu d'être propagées.

    Args:
        latitude (float): Latitude de la ville (utilisée pour l'affichage).
        longitude (float): Longitude de la ville (utilisée pour l'affichage).
        name (str): Nom de la ville.
        nb_day (int): Nombre de jours de prévisions à afficher (1 à 16).

    Returns:
        None
    """
    try:
        latitude, longitude = coordinate
        daily, temperature_unit = get_forecast(latitude, longitude, nb_day)

        for time, temperature_2m_max, temperature_2m_min in zip(daily.get("time"), daily.get("temperature_2m_max"), daily.get("temperature_2m_min")):
                    if temperature_2m_max is not None:
                        print(f"A {name} au coordonées {latitude, longitude} le {time} il {"fait" if c.to_day == time else "fera"} {temperature_2m_max} {temperature_unit} max et {temperature_2m_min} {temperature_unit} min")
                    else:
                        print(f"Prévision impossible en ce moment pour le {time}")
    except APIError as error:
        print(f"Erreur : {error}")

def get_nb_day():
    """Demande à l'utilisateur un nombre de jours de prévisions valide.

    Redemande tant que la saisie n'est pas un entier compris entre 1 et 16.

    Returns:
        int: Le nombre de jours saisi, entre 1 et 16.
    """
    nb_day = None
    while nb_day is None or not 0 < nb_day < 17:
        try:
            nb_day = int(input("Entrer un nombre entre 1 et 16 : "))
            if not 0 < nb_day < 17:
                print("Le nombre doit être entre 1 et 16 !")
        except ValueError:
            print("Veuillez entrer un nombre entier valide")

    return nb_day

def get_city():
    """Demande une ville à l'utilisateur jusqu'à ce qu'elle soit trouvée.

    Boucle d'obtention : redemande tant que l'API ne retourne aucune
    coordonnée pour le nom saisi.

    Returns:
        tuple[tuple[float, float], str]: Un couple ((latitude, longitude), nom)
            où `nom` est le nom tel que saisi par l'utilisateur.

    Raises:
        APIError: Si l'appel à l'API échoue (réseau, timeout, HTTP...).
    """
    coordinates = None
    while coordinates is None:
        name = input("Entrer un nom de ville : ").strip()

        try:
            coordinates = get_coordinate(name)

            if coordinates is None:
                raise CityNotFoundError(name)

    

        except CityNotFoundError:
            print("Nom invalide ou introuvable : ")

    return (coordinates, name)


def run():
    """Point d'entrée du programme.
 
    Demande le nombre de jours puis la ville, et affiche les prévisions.
    Les erreurs d'API survenues pendant la saisie de la ville sont affichées.
 
    Returns:
        None
    """
    nb_day = get_nb_day()
 
    try:
        coordinates, name = get_city()
    except APIError as error:
        print(f"Erreur : {error}")
    else:
        display_forecast(coordinates, name, nb_day)
  






    



    

