from flask import Flask, render_template, request, send_file, redirect, url_for, session, flash, make_response, send_from_directory
import json
import subprocess
import scraper
import csv
from config import COMPETITIONS_PATH, USERS_PATH, CATEGORIES_PATH, MIN_REZULTAT_ZA_TOCKE, EXCLUDED_CATEGORIES_PATH
import logging
import pandas as pd
import pdfkit
import io
import os
import base64
from utils import nalozi_normalizacijo_datoteko, nalozi_popravke_tekmovalcev_datoteko
from utils import POKALSKI_NASLOVI

logging.basicConfig(filename='record.log', level=logging.DEBUG)

app = Flask(__name__)
SECRET_KEY = "nekaj_zelo_tajnega"  # za Flask session
app.secret_key = SECRET_KEY


def load_users():
    with open(USERS_PATH, encoding="utf-8") as f:
        return json.load(f)


def pridobi_tekme_iz_jsona(path=COMPETITIONS_PATH):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def dodaj_tekmo(vnos, path=COMPETITIONS_PATH):
    print(vnos)
    tekme = pridobi_tekme_iz_jsona(path)
    if "added_by" not in vnos:
        vnos["added_by"] = session.get("username", "-")
    tekme.append(vnos)
    with open(path, "w", encoding='utf-8') as f:
        json.dump(tekme, f, ensure_ascii=False, indent=2)


def izbrisi_tekmo(idx):
    with open(COMPETITIONS_PATH, encoding="utf-8") as f:
        tekme = json.load(f)
    if 0 <= idx < len(tekme):
        del tekme[idx]
        with open(COMPETITIONS_PATH, "w", encoding="utf-8") as f:
            json.dump(tekme, f, ensure_ascii=False, indent=2)


def preberi_povzetek_csv(path="povzetek.csv"):
    skupine = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        ime_skupine = None
        tabela = []

        for vrstica in reader:
            if not vrstica:
                if ime_skupine and tabela:
                    skupine.append((ime_skupine, tabela))
                ime_skupine = None
                tabela = []
                continue

            if len(vrstica) == 1 and "–" in vrstica[0]:
                ime_skupine = vrstica[0].strip()
                continue

            tabela.append(vrstica)

        # Zadnja skupina, če ni prazne vrstice na koncu
        if ime_skupine and tabela:
            skupine.append((ime_skupine, tabela))

    return skupine


@app.route("/", methods=["GET", "POST"])
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    tekme = pridobi_tekme_iz_jsona()
    povzetek_ustvarjen = False
    output = ""
    if request.method == "POST":
        if "shrani_tab" in request.form:
            session["zadnji_tab"] = request.form.get("izbran_tab", "AH")
        if "ustvari_povzetek" in request.form:
            tip = request.form.get("izbran_tab", "AH")
            # Zaženi scraper in generate_summary, ujemi izpis
            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                scraper.main()
            # Zaženi generate_summary.py kot subprocess in ujemi output
            proc = subprocess.run(
                ["python", "generate_summary.py", tip],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )

            povzetek_ustvarjen = True
            output = f.getvalue() + "\n" + proc.stdout + proc.stderr
            session["povzetek_ustvarjen"] = povzetek_ustvarjen

        elif "pocisti_output" in request.form:
            # povzetek_ustvarjen = False
            output = ""
        elif "dodaj_tekmo" in request.form:
            info = request.form.get("info")
            stevilo = request.form.get("id_tekmovanja")
            type = request.form.get("type")
            if info and stevilo.isdigit():
                url = f"https://www.ianseo.net/TourData/2025/{stevilo}/IC.php"
                disabled = not bool(request.form.get("active"))  # Če kljukica ni obkljukana → disabled=True
                dodaj_tekmo({"info": info, "url": url, "type": type, "disabled": disabled})
                return redirect(url_for("index"))
        elif "izbrisi_tekmo" in request.form:
            izbrisi_info = request.form.get("izbrisi_tekmo")
            if izbrisi_info:
                tekme = [t for t in tekme if t['info'] != izbrisi_info]
                with open(COMPETITIONS_PATH, "w", encoding="utf-8") as f:
                    json.dump(tekme, f, ensure_ascii=False, indent=2)
            # Po brisanju osveži seznam, da je ažuren:
            tekme = pridobi_tekme_iz_jsona()
        elif "uredi_tekmo" in request.form:
            old_info = request.form.get("old_info")
            new_info = request.form.get("info")
            new_type = request.form.get("type")
            new_id = request.form.get("id_tekmovanja")
            new_url = f"https://www.ianseo.net/TourData/2025/{new_id}/IC.php"
            disabled = not bool(request.form.get("active"))
            for tekma in tekme:
                if tekma["info"] == old_info:
                    tekma["info"] = new_info
                    tekma["url"] = new_url
                    tekma["type"] = new_type
                    tekma["disabled"] = disabled
                    tekma["added_by"] = session.get("username", "-")
                    break

            with open(COMPETITIONS_PATH, "w", encoding="utf-8") as f:
                json.dump(tekme, f, ensure_ascii=False, indent=2)
            tekme = pridobi_tekme_iz_jsona()
    izbran_tip = session.get("zadnji_tab", "AH")
    return render_template("index.html", tekme=tekme, povzetek_ustvarjen=povzetek_ustvarjen, output=output, izbran_tip=izbran_tip)


@app.route("/summary")
def summary():
    if "username" not in session:
        return redirect(url_for("login"))
    tip = request.args.get("tip", "")  # npr. "3D"
    if tip:
        filename = f"povzetek_{tip}.csv"
    else:
        filename = "povzetek.csv"

    skupine = preberi_povzetek_csv(filename)
    naslov = POKALSKI_NASLOVI.get(tip, tip)
    return render_template("summary.html", skupine=skupine, izbran_tip=tip, naslov=naslov)


@app.route("/settings", methods=["GET"])
def settings():
    logging.debug("--- settings ---")
    if "username" not in session:
        return redirect(url_for("login"))

    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        kategorije = json.load(f)

    kol_vrstic = max(len(v) for v in kategorije.values())

    try:
        with open("excluded_categories.json", "r", encoding="utf-8") as f:
            izloceni = json.load(f)
    except FileNotFoundError:
        izloceni = []

    # 🔽 Dodaj normalizacijo klubov
    normalizacija_klubov = nalozi_normalizacijo_datoteko().items()
    normalizacija_tekmovalcev = nalozi_popravke_tekmovalcev_datoteko().items()

    return render_template(
        "settings.html",
        kategorije=kategorije,
        izloceni=izloceni,
        min_rezultat=MIN_REZULTAT_ZA_TOCKE,
        kol_vrstic=kol_vrstic,
        normalizacija_klubov=normalizacija_klubov,
        normalizacija_tekmovalcev=normalizacija_tekmovalcev
    )


@app.route("/shrani_izlocene_kategorije", methods=["POST"])
def shrani_izlocene_kategorije():
    vse_kombinacije = set()
    with open(CATEGORIES_PATH, encoding="utf-8") as f:
        kategorije = json.load(f)
    for stil, seznami in kategorije.items():
        for kategorija in seznami:
            vse_kombinacije.add(f"{stil}::{kategorija}")

    izbrane = set(request.form.getlist("excluded"))
    izloceni = list(vse_kombinacije - izbrane)  # Shrani tiste, ki niso izbrane
    with open(EXCLUDED_CATEGORIES_PATH, "w", encoding="utf-8") as f:
        json.dump(izloceni, f, ensure_ascii=False, indent=2)
    return redirect(url_for("settings"))


@app.route("/shrani_normalizacijo_klubov", methods=["POST"])
def shrani_normalizacijo_klubov():
    trenutna = nalozi_normalizacijo_datoteko()  # npr. dict: {"R01": "001 - Maribor", ...}

    # 1. Če gre za brisanje
    oznaka_za_brisanje = request.form.get("delete")
    if oznaka_za_brisanje:
        trenutna.pop(oznaka_za_brisanje, None)

    # 2. Če gre za urejanje ali dodajanje
    elif "uredi_klub" in request.form:
        oznaka_stara = request.form.get("oznaka_stara", "").strip()
        oznaka = request.form.get("oznaka", "").strip()
        pravilno = request.form.get("pravilno", "").strip()

        if oznaka and pravilno:
            if oznaka_stara and oznaka_stara != oznaka:
                trenutna.pop(oznaka_stara, None)
            trenutna[oznaka] = pravilno

    # 4. Shrani v CSV
    with open("normalizacija_klubov.csv", "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["stara_oznaka", "pravilno_ime"])
        for oznaka, pravilno in sorted(trenutna.items()):
            writer.writerow([oznaka, pravilno])

    flash("✅ Spremembe shranjene.")
    return redirect(url_for("settings"))


@app.route("/shrani_normalizacijo_tekmovalcev", methods=["POST"])
def shrani_normalizacijo_tekmovalcev():
    trenutna = nalozi_popravke_tekmovalcev_datoteko()  # {"VARDIĆ Branko": "VARDIČ Branko", ...}

    # 1. Če gre za brisanje
    napacno_za_brisanje = request.form.get("delete")
    if napacno_za_brisanje:
        trenutna.pop(napacno_za_brisanje, None)

    # 2. Če gre za urejanje ali dodajanje
    elif "uredi_tekmovalca" in request.form:
        oznaka_stara = request.form.get("oznaka_stara", "").strip()
        oznaka = request.form.get("oznaka", "").strip()
        pravilno = request.form.get("pravilno", "").strip()

        if oznaka and pravilno:
            if oznaka_stara and oznaka_stara != oznaka:
                trenutna.pop(oznaka_stara, None)
            trenutna[oznaka] = pravilno

    # 3. Shrani v CSV
    with open("popravki_imen.csv", "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["napačno", "pravilno"])
        for napacno, pravilno in sorted(trenutna.items()):
            writer.writerow([napacno, pravilno])

    flash("✅ Spremembe shranjene (tekmovalci).")
    return redirect(url_for("settings"))


@app.route("/download_summary")
def download_summary():
    if "username" not in session:
        return redirect(url_for("login"))

    tip = request.args.get("tip")  # pridobi tip iz URL-ja

    if not tip:
        return "Tip tekme ni podan.", 400

    filename = f"povzetek_{tip}.csv"

    try:
        return send_file(filename, as_attachment=True, mimetype="text/csv")
    except FileNotFoundError:
        return f"Datoteka {filename} ni bila najdena.", 404


def get_base64_image(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')


# Recimo, df je tvoj DataFrame
def odstrani_stevilko(text):
    # Razdeli niz na dva dela po prvem " - "
    # if not isinstance(text, str):
    #    text = str(text)
    deli = text.split(" - ", 1)
    if len(deli) == 2:
        return deli[1].strip()  # vrni del za pomišljajem, brez presledkov
    else:
        return text  # če ni pomišljaja, vrni celoten niz


@app.route('/pdf')
def generate_pdf():
    # Preberi izbran tab iz GET parametrov
    izbran_tab = request.args.get('izbran_tab', default="AH")
    # print(izbran_tab)
    naslov = POKALSKI_NASLOVI.get(izbran_tab, "-")
    # Preberi CSV
    csv_filename = f'povzetek_klubi_{izbran_tab}.csv'
    try:
        with open(csv_filename, encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return f"Povzetek za tip {izbran_tab} ne obstaja."

    start_idx = next((i for i, l in enumerate(lines) if l.strip().startswith("Uvrstitev")), None)
    if start_idx is None:
        return "CSV nima ustrezne glave."

    csv_data = ''.join(lines[start_idx:])
    df = pd.read_csv(io.StringIO(csv_data))
    # Skrij stolpec "Število tekmovalcev", če obstaja
    if 'Število tekmovalcev' in df.columns:
        df = df.drop(columns=['Število tekmovalcev'])

    if 'Točke' in df.columns:
        df['Točke'] = df['Točke'].apply(lambda x: f'<span style="color:red;">{x}</span>')

    df.columns = [
        f'<span style="color:red;">{col}</span>' if col == 'Točke' else col
        for col in df.columns
    ]

    df['Klub'] = df['Klub'].apply(odstrani_stevilko)

    # Pretvori celoten DataFrame v HTML tabelo brez indeksa
    table_html = df.to_html(index=False, classes='table table-striped', border=0, escape=False)
    # Logo v base64 za prikaz v HTML
    logo_path = os.path.join(app.root_path, 'static', 'images', 'logo.png')
    logo_base64 = get_base64_image(logo_path)

    # Render HTML template in pošlji v pdfkit za PDF generacijo
    rendered = render_template('report_klubi.html',
                               naslov=naslov,
                               table_html=table_html,
                               izbran_tip=izbran_tab,
                               logo_base64=logo_base64)
    # Nastavi pot do wkhtmltopdf.exe - popravi, če ni v PATH
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
    pdf = pdfkit.from_string(rendered, False, configuration=config)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=povzetek_{izbran_tab}.pdf'
    # response.headers['Content-Disposition'] = 'attachment; filename=povzetek.pdf'
    return response


@app.route('/pdf_posamezno')
def generate_pdf_posamezno():
    izbran_tab = request.args.get('izbran_tab', default="AH")
    naslov = POKALSKI_NASLOVI.get(izbran_tab, "-")

    # Naloži CSV povzetek po posameznikih
    csv_filename = f'povzetek_{izbran_tab}.csv'  # pazljivo, naj bo ta CSV pravilno generiran
    try:
        with open(csv_filename, encoding='utf-8') as f:
            lines = [line.strip().split(",") for line in f if line.strip()]
    except FileNotFoundError:
        return f"Povzetek za tip {izbran_tab} ne obstaja."

    # Skupine so ločene z vrstico, kjer je vsa polja prazna ali prva celica vsebuje naziv skupine
    skupine = []
    trenutna_skupina = None

    for row in lines:
        if len(row) == 1 and row[0].strip():  # Nova skupina
            if trenutna_skupina:
                skupine.append(trenutna_skupina)
            trenutna_skupina = [row[0], []]  # [ime_skupine, tabela]
        elif trenutna_skupina:
            trenutna_skupina[1].append(row)

    if trenutna_skupina:
        skupine.append(trenutna_skupina)

    # Pretvori skupine v format za render (ime_skupine, tabela)
    # skupine_render = []
    # for ime, tabela in skupine:
    #    if not tabela:
    #        continue
    #    skupine_render.append((ime, tabela))
    skupine_render = []
    for ime, tabela in skupine:
        if not tabela:
            continue
        # Poišči stolpec "Klub" v prvi vrstici (glavi)
        try:
            klub_idx = tabela[0].index("Klub")
        except ValueError:
            klub_idx = -1

        if klub_idx != -1:
            # Odstrani številke iz vsake vrstice v stolpcu "Klub"
            for vrstica in tabela[1:]:
                if len(vrstica) > klub_idx:
                    vrstica[klub_idx] = odstrani_stevilko(vrstica[klub_idx])

        skupine_render.append((ime, tabela))
    # Logo v base64 za prikaz v HTML
    logo_path = os.path.join(app.root_path, 'static', 'images', 'logo.png')
    logo_base64 = get_base64_image(logo_path)

    # Renderiraj HTML predlogo za PDF
    rendered = render_template(
        "report.html",
        naslov=naslov,
        skupine=skupine_render,
        izbran_tip=izbran_tab,
        logo_base64=logo_base64
    )

    header_html = render_template("pdf_header.html", logo_base64=logo_base64, naslov=naslov)
    header_file_path = os.path.join(app.root_path, "temp_header.html")
    with open(header_file_path, "w", encoding="utf-8") as f:
        f.write(header_html)

    options = {
        'page-size': 'A4',
        'orientation': 'Landscape',
        'encoding': "UTF-8",
        'header-html': header_file_path,
        'margin-top': '30mm',  # Dovolj prostora za header
        'header-spacing': '5',
    }
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
    # pdf = pdfkit.from_string(rendered, False, configuration=config)
    pdf = pdfkit.from_string(rendered, False, options=options, configuration=config)

    response = make_response(pdf)
    filename = f"povzetek_posamezno_{izbran_tab}.pdf"
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'

    return response


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        users = load_users()
        user = next((u for u in users if u["username"] == username and u["password"] == password), None)
        logging.log(level=logging.DEBUG, msg="--- login --- " + username)
        if user:
            session["logged_in"] = True
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("index"))
        else:
            flash("Napačno uporabniško ime ali geslo.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')


if __name__ == "__main__":
    app.run(debug=True, port=8888)
