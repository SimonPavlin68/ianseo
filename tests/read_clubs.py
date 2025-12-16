import requests
from bs4 import BeautifulSoup
import csv
import html

# URL seznama klubov
base_url = "https://slo.service.ianseo.net"
url = f"{base_url}/General/ClubList.php?Level=2"

# Pošljemo HTTP GET zahtevo na URL
response = requests.get(url)

# Preverimo, če je zahteva uspela (status koda 200)
if response.status_code == 200:
    # Parsiramo HTML vsebino
    soup = BeautifulSoup(response.text, 'html.parser')

    # Poiščemo vse vrstice tabele, ki vsebujejo seznam klubov
    rows = soup.find_all('tr')[3:-1]  # Preskočimo prve 3 vrstice (glava tabele) in zadnjo (linki za filtriranje)


    # Funkcija za čiščenje besedila in odstranjevanje HTML entitet
    def clean_text(text):
        # Pretvorimo HTML entitete, kot so &nbsp; v normalne presledke
        text = html.unescape(text.strip())  # unescape bo zamenjal &nbsp; z običajnim presledkom
        # Zamenjamo <br> z običajnim presledkom
        text = text.replace('<br>', ' ').replace('&nbsp;', ' ')
        # Zamenjamo vse podvojene presledke z enim presledkom
        text = ' '.join(text.split())
        return text.strip()


    # Seznam za shranjevanje podatkov o klubih
    clubs = []

    # Iteriramo čez vrstice in pridobimo ime kluba, e-mail in povezavo do podrobnosti
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 4:  # Preverimo, ali so vse celice prisotne
            club_code = clean_text(cells[0].text)  # Zamenjamo &nbsp; s presledkom
            club_name = clean_text(cells[1].text)  # Zamenjamo &nbsp; s presledkom
            club_email_tag = cells[3].find('a')
            club_email = club_email_tag['href'].replace('mailto:', '') if club_email_tag else 'N/A'

            # URL za podrobnosti o klubu
            club_detail_url = cells[1].find('a')['href']
            full_club_url = f"{base_url}{club_detail_url}"

            # Dodajanje osnovnih podatkov o klubu v seznam
            clubs.append([club_code, club_name, club_email, full_club_url])

    # Shranimo osnovne podatke v CSV
    with open('clubs_basic_info.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Club Code', 'Club Name', 'Club Email', 'Club Detail URL'])
        writer.writerows(clubs)

    print("Podatki o klubih so bili shranjeni v 'clubs_basic_info.csv'.")
else:
    print("Napaka pri pridobivanju seznamov klubov:", response.status_code)
