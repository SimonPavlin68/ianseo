import requests
from bs4 import BeautifulSoup
import csv


def get_club_details(club_url):
    # Pošljemo GET zahtevo na stran z detajli kluba
    response = requests.get(club_url)

    # Preverimo, ali je stran uspešno naložena
    if response.status_code != 200:
        print(f"Napaka pri nalaganju strani: {club_url} - Status: {response.status_code}")
        return None

    # Pridobimo HTML vsebino
    soup = BeautifulSoup(response.text, 'html.parser')

    # Izpišemo nekaj prvega dela HTML-ja za pregled
    print(f"HTML za {club_url}:")
    print(soup.prettify()[:1000])  # Prikaz prvega dela HTML-ja

    # Pridobimo podatke iz tabele z informacijami o klubu
    club_info = {}
    club_info['Club Detail URL'] = club_url

    # Iskanje vseh vrstic (tr) v tabeli, ki vsebujejo informacije o klubu
    rows = soup.find_all('tr')

    # Debugging: Preverimo, koliko vrstic smo našli
    print(f"Število vrstic v HTML-ju: {len(rows)}")

    for row in rows:
        # Poiščemo vse glave (th) in podatke (td)
        th = row.find('th')
        td = row.find('td')

        # Če so prisotni tako th kot td
        if th and td:
            header_text = th.text.strip()
            data_text = td.text.strip()
            print(f"Najdeno - {header_text}: {data_text}")

            # Zdaj primerjamo za različne ključne besede v slovenščini
            if header_text == 'Šifra kluba':
                club_info['Club Code'] = data_text
            elif header_text == 'Ime kluba':
                club_info['Club Name'] = data_text
            elif header_text == 'Kratko ime kluba':
                club_info['Club Short Name'] = data_text
            elif header_text == 'Aktiven':
                club_info['Active'] = data_text
            elif header_text == 'Klub registriran od':
                club_info['Registered Since'] = data_text
            elif header_text == 'Zveza':
                # Federacija je lahko povezava, preverimo, če je
                federation_link = td.find('a')
                if federation_link:
                    club_info['Federation'] = federation_link.text.strip()
                else:
                    club_info['Federation'] = data_text
            elif header_text == 'Kontakti kluba':
                # Email in telefon
                email_tag = td.find('a', href=True)
                if email_tag:
                    club_info['Email'] = email_tag['href'].replace('mailto:', '').strip()
                phone = td.find(text='Telefon (zasebno):')
                if phone:
                    club_info['Phone'] = phone.find_next('td').text.strip()
                else:
                    club_info['Phone'] = None
            elif header_text == 'Naslov kluba':
                club_info['Address'] = data_text
            elif header_text == 'Klubske opombe':
                club_info['Notes'] = data_text

    # Če ni bilo najdenih ključnih podatkov, vrnemo None
    if not club_info:
        print(f"Ni bilo podatkov za: {club_url}")
        return None

    # Debugging: Prikaz podatkov pred zapisom
    print("Podatki za zapis v CSV:")
    for key, value in club_info.items():
        print(f"{key}: {value}")

    return club_info


def main():
    # Preberi seznam klubov iz CSV
    with open('clubs_basic_info.csv', mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        clubs = [row for row in reader]

    # Odpri CSV za zapis
    with open('clubs_full_info.csv', mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ['Club Code', 'Club Name', 'Club Short Name', 'Active', 'Registered Since', 'Federation', 'Email',
                      'Phone', 'Address', 'Notes', 'Club Detail URL']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Zapišemo glavo CSV-ja
        writer.writeheader()

        # Debugging: izpis glave CSV-ja
        print(f"Zapisujemo v CSV datoteko z naslednjimi stolpci: {fieldnames}")

        for club in clubs:
            club_url = club['Club Detail URL']
            club_url_with_archers = f"{club_url}&ShowArchers=1"
            print(f"Obdelujemo klub: {club['Club Name']} - URL: {club_url_with_archers}")
            club_details = get_club_details(club_url_with_archers)

            # Debugging: Preverimo, ali so podatki za zapis
            if club_details:
                print("Podatki pripravljeni za zapis:")
                print(club_details)
                writer.writerow(club_details)
                print(f"Podatki za {club['Club Name']} zapisani.")
            else:
                print(f"Ni bilo podatkov za klub {club['Club Name']}.")


if __name__ == "__main__":
    main()
