from config import DEFAULT_MIN_REZULTAT_ZA_TOCKE
import csv
import sys
import os
import json
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

    popravki_imen = nalozi_popravke_tekmovalcev_datoteko()

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
    # all_competitions.add("Gradac<br>18.10.2025")
    filename = f"tekme_{izbran_tip}_not.json"
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            prazne_tekme = json.load(f)
        for t in prazne_tekme:
            all_competitions.add(t)  # samo dodaj v set
    tekme_sorted = sorted(all_competitions, key=extract_date_from_competition_name)
    # Zdaj še shranimo tekme posebej
    with open(f"tekme_{izbran_tip}.csv", "w", encoding="utf-8-sig", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Upoštevane tekme"])
        for tekma in tekme_sorted:
            writer.writerow([tekma])
    # Zgradi results po tekmovalcih
    for (slog, kategorija), tekme in raw_results.items():
        for tekmovanje, seznam in tekme.items():
            razvrščeni = sorted(seznam, key=lambda x: x[2], reverse=True)
            for i, (tekmovalec, klub, rezultat) in enumerate(razvrščeni):
                if rezultat < DEFAULT_MIN_REZULTAT_ZA_TOCKE.get(izbran_tip, 130):
                    točke = 0
                    print('jebiga premalo: ' + tekmovalec + ' ' + str(rezultat) + ' min: ' + str(DEFAULT_MIN_REZULTAT_ZA_TOCKE.get(izbran_tip, 130)))
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
    with open(f"povzetek_{izbran_tip}.csv", "w", encoding="utf-8-sig", newline='') as f:
        writer = csv.writer(f)
        for (slog, kategorija), tekmovalci in results.items():
            writer.writerow([])
            writer.writerow([f"{slog} – {kategorija}"])
            header = ['Mesto', 'Tekmovalec', 'Klub'] + tekme_sorted + ['Skupaj']
            writer.writerow(header)

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

    print(f"✅ Povzetek za tip '{izbran_tip}' shranjen v 'povzetek_{izbran_tip}.csv'.")

    # Shranjevanje povzetka po klubih z uvrstitvijo in stolpci: Uvrstitev, Klub, Krogi, Točke
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

    print(f"✅ Povzetek po klubih za tip '{izbran_tip}' shranjen v 'povzetek_klubi_{izbran_tip}.csv'.")


def generiraj_povzetek_za_tip_final(izbran_tip):
    from collections import defaultdict
    import csv

    results = defaultdict(lambda: defaultdict(lambda: {
        'klub': '',
        'tekme': {},
        'skupaj_krogi': 0,
        'skupaj_točke': 0
    }))
    all_competitions = set()
    raw_results = defaultdict(lambda: defaultdict(list))

    popravki_imen = nalozi_popravke_tekmovalcev_datoteko()

    with open("rezultati_filtrirani.csv", encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tip = row['Tip'].strip()
            if tip != izbran_tip:
                continue
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
    tekme_sorted = sorted(all_competitions, key=extract_date_from_competition_name)

    # Shranimo seznam tekem
    with open(f"tekme_{izbran_tip}.csv", "w", encoding="utf-8-sig", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Upoštevane tekme"])
        for tekma in tekme_sorted:
            writer.writerow([tekma])

    # Zgradi results po tekmovalcih
    for (slog, kategorija), tekme in raw_results.items():
        for tekmovanje, seznam in tekme.items():
            razvrščeni = sorted(seznam, key=lambda x: x[2], reverse=True)
            for i, (tekmovalec, klub, rezultat) in enumerate(razvrščeni):
                if rezultat < DEFAULT_MIN_REZULTAT_ZA_TOCKE.get(izbran_tip, 130):
                    točke = 0
                else:
                    točke = točkovanje[i] if i < len(točkovanje) else 0
                podatki = results[(slog, kategorija)][tekmovalec]
                podatki['klub'] = klub
                podatki['tekme'][tekmovanje] = {'krogi': rezultat, 'točke': točke}

    # Fertik logika: ne upoštevamo najslabšega rezultata samo, če ima tekmovalec vse tekme
    for (slog, kategorija), tekmovalci in results.items():
        for tekmovalec, podatki in tekmovalci.items():
            tekme = podatki['tekme']
            if len(tekme) == len(tekme_sorted):
                # poišči najslabšo tekmo: najmanj točk, pri enakih točkah najmanj krogi
                naj_slabša_tekma = min(
                    tekme.items(),
                    key=lambda x: (x[1]['točke'], x[1]['krogi'])
                )[0]
                # Označi zvezdico
                podatki['tekme'][naj_slabša_tekma]['točke'] = f"*{podatki['tekme'][naj_slabša_tekma]['točke']}"

                # Seštej samo preostale tekme
                podatki['skupaj_krogi'] = sum(
                    v['krogi'] if isinstance(v['krogi'], int) else int(str(v['krogi']).lstrip("*"))
                    for k, v in tekme.items() if k != naj_slabša_tekma
                )
                podatki['skupaj_točke'] = sum(
                    v['točke'] for k, v in tekme.items() if k != naj_slabša_tekma
                )
            else:
                # Če nima vseh tekem, seštej vse
                podatki['skupaj_krogi'] = sum(
                    v['krogi'] if isinstance(v['krogi'], int) else int(str(v['krogi']).lstrip("*"))
                    for v in tekme.values()
                )
                podatki['skupaj_točke'] = sum(v['točke'] for v in tekme.values())

    # Shranjevanje povzetka po tekmovalcih
    with open(f"povzetek_{izbran_tip}_final.csv", "w", encoding="utf-8-sig", newline='') as f:
        writer = csv.writer(f)
        for (slog, kategorija), tekmovalci in results.items():
            writer.writerow([])
            writer.writerow([f"{slog} – {kategorija}"])
            header = ['Mesto', 'Tekmovalec', 'Klub'] + tekme_sorted + ['Skupaj']
            writer.writerow(header)

            # Razvrsti tekmovalce po točkah, nato po krogih
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

    print(f"✅ Povzetek za tip '{izbran_tip}' shranjen v 'povzetek_{izbran_tip}_final.csv'.")

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

    # Shranjevanje povzetka po klubih
    with open(f"povzetek_klubi_{izbran_tip}_final.csv", "w", encoding="utf-8-sig", newline='') as f:
        writer = csv.writer(f)

        # Najprej upoštevane tekme - vsaka v svojo vrstico
        writer.writerow(["Upoštevane tekme"])
        for tekma in tekme_sorted:
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
                podatki['skupaj_tekmovalci'],
                podatki['skupaj_krogi'],
                podatki['skupaj_točke']
            ])


def main(tp, frtk):
    # print(f"tip = {tp}, fertik = {frtk}")
    if frtk:
        print("po novem")
        generiraj_povzetek_za_tip_final(tp)
    else:
        print("po starem")
        generiraj_povzetek_za_tip(tp)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        tip = sys.argv[1]
    else:
        tip = "AH"  # default
    fertik = sys.argv[2].lower() in ("true", "1", "yes") if len(sys.argv) > 2 else False
    main(tip, fertik)
