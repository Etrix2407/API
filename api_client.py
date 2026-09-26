import config as c
import requests, json


class APIError(Exception):
    pass

class Timeout(APIError):
    def __init__(self, url, timeout):
        self.url = url
        self.timeout = timeout
        super().__init__(f"temps {timeout} dépasser sur {url}")

class HTTPError(APIError):
    def __init__(self, url, status_code, reason):
        self.url = url
        self.code = status_code
        self.reason = reason
        super().__init__(f"Error {status_code} : {reason} ({url})")

class JsonError(APIError):
    def __init__(self, url):
        super().__init__(f"Erreur au niveau du .json")

class NetworkError(APIError):
    def __init__(self, url, original_error):
        self.url = url
        self.original_error = original_error
        super().__init__(f"erreur résaux sur {url} : {original_error}")

class CityNotFoundError(APIError):
    def __init__(self, city_name):
        self.city_name = city_name
        super().__init__(f"Ville introuvable : '{city_name}'")

def _get_json(url, params):

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
    name = input("Entrer un nom de ville : ")
    params = {"name": name}

    data = _get_json(c.GEOCODING_URL, params=params)
    results = data.get("results")
    if not results:
        raise CityNotFoundError(name)


    first_result = results[0]
    return (first_result.get("latitude"), first_result.get("longitude"), first_result.get("name"))

def get_Forecast(nb_day=1):
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
    nb_day = None
    while nb_day is None or nb_day > 16 or nb_day < 1:

        try:
            nb_day = int(input("Entrez un nombre max 16 : "))
            if nb_day > 16 or nb_day < 1:
                print("Le nombre doit être entre 1 et 16.")
        except ValueError:
            print("Veuillez entrer un nombre entier valide.")

    get_Forecast(nb_day)

    



    

