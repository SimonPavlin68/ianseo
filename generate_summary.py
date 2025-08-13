from config import MIN_REZULTAT_ZA_TOCKE
import csv
import sys
from collections import defaultdict
from datetime import datetime
from utils import normaliziraj_klub, nalozi_popravke_tekmovalcev_datoteko


# def nalozi_popravke(path):
#     popravki = {}
#     with open(path, encoding='utf-8-sig') as f:
#         reader = csv.DictReader(f)
#         for row in reader:
#            napačno = row['napačno'].strip().upper()
#            pravilno = row['pravilno'].strip()
#            popravki[napačno] = pravilno
#     return popravki


def capitalize_ime(ime):
    return ' '.join(beseda.capitalize() for beseda in ime.strip().split())


def pogojni_capitalize(ime):
    if " " not in ime.strip():
        return ime.capitalize()
    else:
        return ime


def popravi_ime(ime, popravki):
    ime_upper = ime.strip().upper()
    popravki_ci = {k.upper(): v for k, v in popravki.items()}
    if ime_upper in popravki_ci:
        return capitalize_ime(popravki_ci[ime_upper])
    return capitalize_ime(ime)


def extract_date_from_competition_name(name):
    parts = name.split("<br>")
    if len(parts) == 2:
        try:
            return datetime.strptime(parts[1].strip(), "%d.%m.%Y")
        except ValueError:
            pass
    return datetime.max  # če ni datuma, naj gre na konec


def generiraj_povzetek_za_tip(izbran_tip):
    results = defaultdict(lambda: defaultdict(lambda: {
        'klub': '',
        'tekme': {},
        'skupaj_krogi': 0,
        'skupaj_točke': 0
    }))
    all_competitions = set()
    raw_results = defaultdict(lambda: defaultdict(list))

    # popravki_imen = nalozi_popravke("popravki_imen.csv")
    # print("--- staro ---")
    # print(popravki_imen)
    popravki_imen = nalozi_popravke_tekmovalcev_datoteko()
    # print("--- novo ---")
    # print(popravki_imen)

    with open("rezultati_filtrirani.csv", encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tip = row['Tip'].strip()
            if tip != izbran_tip:
                continue  # preskoči rezultate, ki niso za izbran tip
            tekmovanje = f"{pogojni_capitalize(row['Lokacija'])}<br>{row['Datum']}"
            kategorija_polno = row['Kategorija'].strip()
            rezultat = int(row['Rezultat'])

            if ' - ' in kategorija_polno:
                slog, kategorija = kategorija_polno.split(' - ', 1)
            else:
                slog = ''
                kategorija = kategorija_polno

            tekmovalec_raw = row['Tekmovalec'].strip()
            tekmovalec = popravi_ime(tekmovalec_raw, popravki_imen)
            klub_raw = row['Klub'].strip()
            klub = normaliziraj_klub(klub_raw)
            all_competitions.add(tekmovanje)
            raw_results[(slog, kategorija)][tekmovanje].append((tekmovalec, klub, rezultat))

    točkovanje = [25, 20, 15, 12] + list(range(11, 0, -1))
    # tekme_sorted = sorted(all_competitions)
    tekme_sorted = sorted(all_competitions, key=extract_date_from_competition_name)
    print("--- bum ---")
    print(tekme_sorted)

    # Zgradi results po tekmovalcih
    for (slog, kategorija), tekme in raw_results.items():
        for tekmovanje, seznam in tekme.items():
            razvrščeni = sorted(seznam, key=lambda x: x[2], reverse=True)
            for i, (tekmovalec, klub, rezultat) in enumerate(razvrščeni):
                if rezultat < MIN_REZULTAT_ZA_TOCKE.get(izbran_tip, 130):
                    točke = 0
                    print('jebiga premalo: ' + tekmovalec + ' ' + str(rezultat) + ' min: ' + str(MIN_REZULTAT_ZA_TOCKE.get(izbran_tip, 130)))
                else:
                    točke = točkovanje[i] if i < len(točkovanje) else 0
                podatki = results[(slog, kategorija)][tekmovalec]
                podatki['klub'] = klub
                podatki['tekme'][tekmovanje] = {'krogi': rezultat, 'točke': točke}
                podatki['skupaj_krogi'] += rezultat
                podatki['skupaj_točke'] += točke

    # Zgradi povzetek po klubih
    klubi_summary = defaultdict(lambda: {
        'skupaj_tekmovalci': 0,
        'skupaj_krogi': 0,
        'skupaj_točke': 0
    })

    for (slog, kategorija), tekmovalci in results.items():
        for tekmovalec, podatki in tekmovalci.items():
            klub = podatki['klub']
            klubi_summary[klub]['skupaj_tekmovalci'] += 1
            klubi_summary[klub]['skupaj_krogi'] += podatki['skupaj_krogi']
            klubi_summary[klub]['skupaj_točke'] += podatki['skupaj_točke']

    # Shranjevanje povzetka po tekmovalcih
    # with open("povzetek.csv", "w", encoding="utf-8-sig", newline='') as f:
    with open(f"povzetek_{izbran_tip}.csv", "w", encoding="utf-8-sig", newline='') as f:
        writer = csv.writer(f)
        for (slog, kategorija), tekmovalci in results.items():
            writer.writerow([])
            writer.writerow([f"{slog} – {kategorija}"])
            header = ['Mesto', 'Tekmovalec', 'Klub'] + tekme_sorted + ['Skupaj']
            writer.writerow(header)

            # uvrstitve = sorted(
            #    tekmovalci.items(),
            #    key=lambda x: x[1]['skupaj_točke'],
            #    reverse=True
            # )

            # Razvrsti tekmovalce po točkah, nato pa po krogih
            uvrstitve = sorted(
                tekmovalci.items(),
                key=lambda x: (x[1]['skupaj_točke'], x[1]['skupaj_krogi']),
                reverse=True
            )

            for mesto, (tekmovalec, podatki) in enumerate(uvrstitve, start=1):
                row = [
                    str(mesto),
                    tekmovalec,
                    podatki['klub'],
                ]
                for t in tekme_sorted:
                    tekma = podatki['tekme'].get(t)
                    if tekma:
                        row.append(f"{tekma['krogi']}/{tekma['točke']}")
                    else:
                        row.append('')
                row.append(f"{podatki['skupaj_krogi']}/{podatki['skupaj_točke']}")
                writer.writerow(row)

    # print("✅ Povzetek shranjen v 'povzetek.csv'.")
    print(f"✅ Povzetek za tip '{izbran_tip}' shranjen v 'povzetek_{izbran_tip}.csv'.")

    # Shranjevanje povzetka po klubih z uvrstitvijo in stolpci: Uvrstitev, Klub, Krogi, Točke
    # Povzetek po klubih
    # with open("povzetek_klubi.csv", "w", encoding="utf-8-sig", newline='') as f:
    with open(f"povzetek_klubi_{izbran_tip}.csv", "w", encoding="utf-8-sig", newline='') as f:
        writer = csv.writer(f)

        # Najprej upoštevane tekme - vsaka v svojo vrstico
        writer.writerow(["Upoštevane tekme"])
        for tekma in sorted(all_competitions):
            writer.writerow([tekma])

        writer.writerow([])  # prazna vrstica za ločitev

        # Naslov in header za klubovsko tabelo
        writer.writerow(["Povzetek po klubih"])
        writer.writerow(['Uvrstitev', 'Klub', 'Število tekmovalcev', 'Krogi', 'Točke'])

        # Nato podatki
        sortirani_klubi = sorted(klubi_summary.items(), key=lambda x: x[1]['skupaj_točke'], reverse=True)
        for mesto, (klub, podatki) in enumerate(sortirani_klubi, start=1):
            writer.writerow([
                mesto,
                klub,
                podatki['skupaj_tekmovalci'],  # tukaj je število unikatnih tekmovalcev
                podatki['skupaj_krogi'],
                podatki['skupaj_točke']
            ])

    # print("✅ Povzetek po klubih shranjen v 'povzetek_klubi.csv'.")
    print(f"✅ Povzetek po klubih za tip '{izbran_tip}' shranjen v 'povzetek_klubi_{izbran_tip}.csv'.")


def main(tip):
    # zdaj imaš parameter tip, ki ga lahko uporabiš
    generiraj_povzetek_za_tip(tip)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        tip = sys.argv[1]
    else:
        tip = "AH"  # default
    main(tip)
