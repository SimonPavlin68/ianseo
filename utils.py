import csv
import os
import json
from config import MIN_TOCKE_PATH

def nalozi_normalizacijo_datoteko() -> dict:
    pot_do_csv = 'normalizacija_klubov.csv'
    normalizacija = {}
    try:
        with open(pot_do_csv, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for vrstica in reader:
                stara = vrstica['stara_oznaka'].strip()
                pravilna = vrstica['pravilno_ime'].strip()
                normalizacija[stara] = pravilna
    except FileNotFoundError:
        print(f"⚠️ Datoteka {pot_do_csv} ni bila najdena. Normalizacija bo prazna.")
    return normalizacija


# TODO tole je duplikat: nalozi_popravke(path) iz generate_summary.py
def nalozi_popravke_tekmovalcev_datoteko() -> dict:
    pot_do_csv = 'popravki_imen.csv'
    normalizacija = {}
    try:
        with open(pot_do_csv, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for vrstica in reader:
                stara = vrstica['napačno'].strip()
                pravilna = vrstica['pravilno'].strip()
                normalizacija[stara] = pravilna
    except FileNotFoundError:
        print(f"⚠️ Datoteka {pot_do_csv} ni bila najdena. Normalizacija bo prazna.")
    return normalizacija


# Naloži ob zagonu modula (lahko pa to narediš tudi dinamično, če želiš)
NORMALIZACIJA_KLUBOV = nalozi_normalizacijo_datoteko()


def normaliziraj_klub(klub_ime: str) -> str:
    oznaka = klub_ime.strip().split(" ")[0]
    normalizirano = NORMALIZACIJA_KLUBOV.get(oznaka)

    if normalizirano and normalizirano != klub_ime:
        print(f"🔄 Klub spremenjen: '{klub_ime}' → '{normalizirano}'")
        return normalizirano
    return klub_ime


def osvezi_normalizacijo():
    global NORMALIZACIJA_KLUBOV
    NORMALIZACIJA_KLUBOV = nalozi_normalizacijo_datoteko()


POKALSKI_NASLOVI = {
    "AH": "Slovenski Arrowhead pokal 2025",
    "3D": "Slovenski 3D pokal 2025",
    "Tarčno": "Slovenski tarčni pokal 2025",
    "Dvorana": "Slovenski dvoranski pokal 2025"
}

# Branje vrednosti iz datoteke
def load_min_tocke():
    if os.path.exists(MIN_TOCKE_PATH):
        with open(MIN_TOCKE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # privzete vrednosti, če datoteka ne obstaja
        return {
            "AH": 130,
            "3D": 159,
            "Dvorana": 180,
            "Tarčno": 216
        }

# Shranjevanje/spreminjanje vrednosti
def save_min_tocke(tocke_dict):
    with open(MIN_TOCKE_PATH, "w", encoding="utf-8") as f:
        json.dump(tocke_dict, f, indent=4)