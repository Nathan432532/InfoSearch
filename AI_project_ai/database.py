import json

def lees_lokale_backups():
    """Leest de lokale JSON back-up voor het geval de backend API offline is."""
    try:
        with open('bedrijven_db.json', 'r') as f:
            return json.load(f)
    except:
        return []

def save_lokale_backup(data):
    with open('bedrijven_db.json', 'w') as f:
        json.dump(data, f, indent=4)