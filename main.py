"""Point d'entrée du script en ligne de commande de prévisions météo."""

from api_client import run


def main():
    """Lance le programme en déléguant à `api_client.run`.

    Returns:
        None
    """
    run()

if __name__ == "__main__":
    main()