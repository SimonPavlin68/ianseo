import json
import re
import requests
from bs4 import BeautifulSoup
import csv
from config import COMPETITIONS_PATH, CATEGORIES_PATH, EXCLUDED_CATEGORIES_PATH
from utils import normaliziraj_klub


def clean_club(text: str) -> str:
    return text.replace('\xa0', ' ').replace('\n', ' ').strip()


def parse_competition_info(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    center_div = soup.find("div", class_="results-header-center")
    if not center_div:
        return None, None, None, None

    divs = center_div.find_all("div")
    if len(divs) < 2:
        return None, None, None, None

    ime_tekme = divs[0].get_text(strip=True)

    drugi_div = divs[1]
    deli_teksta = drugi_div.decode_contents().split("<br/>")
    deli_teksta = [BeautifulSoup(s, "html.parser").get_text(strip=True) for s in deli_teksta if s.strip()]

    klub = deli_teksta[0] if len(deli_teksta) > 0 else ""
    lokacija = ""
    datum = ""
    if len(deli_teksta) > 1:
        # Poskusi ločiti po zadnji vejici
        raw = deli_teksta[1]
        parts = raw.rsplit(",", 1)
        if len(parts) == 2:
            lokacija = parts[0].strip()
            datum_raw = parts[1].strip()
            try:
                # Slovar za pretvorbo mesecev (angleška kratica → številka)
                meseci = {
                    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
                }

                parts = datum_raw.split()
                if len(parts) == 3 and parts[1] in meseci:
                    day = int(parts[0])
                    month = meseci[parts[1]]
                    year = int(parts[2])
                    datum = f"{day}.{month}.{year}"
                else:
                    datum = datum_raw
            except Exception as e:
                datum = datum_raw
        else:
            lokacija = raw

    return ime_tekme, klub, lokacija, datum


def parse_competition_results(url, allowed_categories, tip):
    resp = requests.get(url)
    resp.raise_for_status()
    html_text = resp.text

    ime_tekme, klub, lokacija, datum = parse_competition_info(html_text)

    soup = BeautifulSoup(html_text, "html.parser")
    current_category = None
    data = []

    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            ths = tr.find_all("th")
            tds = tr.find_all("td")

            # 1. Detekcija kategorije
            if len(ths) == 1 and "colspan" in ths[0].attrs:
                cat_text = ths[0].get_text(strip=True)
                # print(f"🏷️ Najdena kategorija: {cat_text}")
                m = re.match(r"(.+?)\s*-\s*(.+)", cat_text)
                if m:
                    stil = m.group(1).strip()
                    kategorija = re.sub(r"\s*\[.*?\]", "", m.group(2)).strip()  # <- ta vrstica je nova
                    if stil in allowed_categories and kategorija in allowed_categories[stil]:
                        # current_category = cat_text
                        current_category = f"{stil} - {kategorija}"  # brez oklepajev
                    else:
                        # print(f"⚠️ Kategorija '{stil} - {kategorija}' ni dovoljena.")
                        current_category = None
                else:
                    print("⚠️ Neveljaven format kategorije:", cat_text)
                    current_category = None
                continue

            # 2. Preskoči, če kategorija ni nastavljena
            if current_category is None:
                continue

            # 3. Obdelava rezultatov
            if len(tds) >= 5:
                mesto = tds[0].get_text(strip=True)
                tekmovalec = tds[1].get_text(strip=True)
                klub_tekmovalca = clean_club(tds[2].get_text())

                # Tip: Dvorana
                if tip == "Dvorana":
                    if len(tds) >= 6:
                        rezultat = tds[5].get_text(strip=True)
                    else:
                        print(f"❌ Premalo stolpcev za Dvorano: {len(tds)}")
                        continue

                # Tip: Tarčno
                elif tip == "Tarčno":
                    if len(tds) < 8:
                        print("❌ Napačno število stolpcev za Tarčno:", len(tds))
                        print([td.get_text(strip=True) for td in tds])
                        continue
                    rezultat = tds[5].get_text(strip=True)  # vsota serij

                # Vsi ostali tipi (3D, AH, …)
                else:
                    if len(tds) >= 5:
                        rezultat = tds[4].get_text(strip=True)
                    else:
                        print(f"❌ Premalo stolpcev za {tip}: {len(tds)}")
                        continue

                klub_tekmovalca = normaliziraj_klub(klub_tekmovalca) or klub_tekmovalca
                # 4. Shrani rezultat, če gre za slovenski klub
                if re.match(r"^\d{3}", klub_tekmovalca):
                    data.append({
                        "Tekmovanje": ime_tekme or "Neznano tekmovanje",
                        "Organizator": klub or "",
                        "Lokacija": lokacija or "",
                        "Datum": datum or "",
                        "Kategorija": current_category,
                        "Mesto": mesto,
                        "Tekmovalec": tekmovalec,
                        "Klub": klub_tekmovalca,
                        "Rezultat": rezultat,
                        "Tip": tip
                    })
                else:
                    print("⚠️ Klub ni v LZS: " + klub_tekmovalca)

    print(f"✅ Najdenih rezultatov: {len(data)}")
    return data


def main():
    with open(COMPETITIONS_PATH, "r", encoding="utf-8") as f:
        competitions = json.load(f)

    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        allowed_categories = json.load(f)

    try:
        with open(EXCLUDED_CATEGORIES_PATH, "r", encoding="utf-8") as f:
            excluded_pairs = json.load(f)  # npr: ["Dolgi lok::Mlajši od 13 let"]
    except FileNotFoundError:
        excluded_pairs = []

    # 🔍 Filtriraj allowed_categories glede na izključene
    filtered_categories = {}
    izkljuceni_log = []

    for stil, kategorije in allowed_categories.items():
        dovoljene = []
        for kat in kategorije:
            key = f"{stil}::{kat}"
            if key not in excluded_pairs:
                dovoljene.append(kat)
            else:
                izkljuceni_log.append(key)
        if dovoljene:
            filtered_categories[stil] = dovoljene

    # 🖨️ Izpis izključenih kombinacij
    if izkljuceni_log:
        print("🛑 Izključene kategorije:")
        for k in izkljuceni_log:
            print(f" - {k}")
    else:
        print("✅ Nobena kategorija ni bila izključena.")

    all_results = []

    for comp in competitions:
        if comp.get("disabled", False):
            print(f"⏭️ Tekma '{comp.get('info')}' je neaktivna, preskočena.")
            continue  # preskoči to tekmo
        print(f"\n📦 Pridobivanje rezultatov iz: {comp['url']} ({comp.get('info', '')})")
        try:
            results = parse_competition_results(comp["url"], filtered_categories, comp["type"])
            print(f"✅ Tekma '{comp.get('info')}' vrnila {len(results)} rezultatov po filtriranju")
            all_results.extend(results)
        except Exception as e:
            print(f"❌ NAPAKA pri prenosu {comp['url']}: {e}")

    print(f"\n📊 Skupno rezultatov po vseh tekmah: {len(all_results)}")

    if all_results:
        keys = ["Tekmovanje", "Organizator", "Lokacija", "Datum", "Kategorija", "Mesto", "Tekmovalec", "Klub", "Rezultat", "Tip"]
        with open("rezultati_filtrirani.csv", "w", encoding="utf-8-sig", newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_results)
        print("💾 Rezultati shranjeni v 'rezultati_filtrirani.csv'.")
    else:
        print("⚠️ Ni bilo rezultatov za združevanje.")


if __name__ == "__main__":
    main()
