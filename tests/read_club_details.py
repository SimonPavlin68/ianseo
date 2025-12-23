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

    # Debugging: Izpišemo nekaj prvega dela HTML-ja za pregled
    print(f"HTML za {club_url}:")
    print(soup.prettify()[:1000])  # Prikaz prvega dela HTML-ja

    # Inicializiramo prazni slovar za podatke o klubu
    club_info = {}
    club_info['Club Detail URL'] = club_url

    # Poiščemo vrstice (tr) z informacijami o klubu
    try:
        rows = soup.find_all('tr')

        for row in rows:
            th = row.find('th')
            td = row.find('td')

            if th and td:
                header_text = th.text.strip()
                data_text = td.text.strip()

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
                    federation_link = td.find('a')
                    if federation_link:
                        club_info['Federation'] = federation_link.text.strip()
                    else:
                        club_info['Federation'] = data_text
                elif header_text == 'Kontakti kluba':
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

    except Exception as e:
        print(f"Napaka pri obdelavi podatkov o klubu: {e}")
        return None

    # Če ni bilo najdenih ključnih podatkov o klubu, vrnemo None
    if not club_info.get('Club Name'):
        print(f"Ni bilo podatkov za klub: {club_url}")
        return None

    # Debugging: Prikaz podatkov o klubu pred zapisom
    print("Podatki o klubu:")
    for key, value in club_info.items():
        print(f"{key}: {value}")

    # Poiščemo podatke o tekmovalcih
    archers = []
    try:
        # Poiščemo <td colspan="2">, ki vsebuje notranjo tabelo s tekmovalci
        archers_section = None

        # Preverimo vsak <td colspan="2">, dokler ne najdemo tistega z notranjo tabelo
        for td in soup.find_all('td', {'colspan': '2'}):
            if td.find('table', {'class': 'FullSize'}):  # Preverimo, če vsebuje tabelo s tekmovalci
                archers_section = td
                break  # Ko najdemo ustrezno sekcijo, prekinemo iskanje

        if archers_section:
            print("Sekcija za tekmovalce najdena.")  # Debugging
            # Znotraj tega <td> poiščemo notranjo tabelo s tekmovalci
            archers_table = archers_section.find('table', {'class': 'FullSize'})

            if archers_table:
                rows = archers_table.find_all('tr')  # Poiščemo vse vrstice v tej notranji tabeli
                print(f"Število vrstic v tabeli s tekmovalci: {len(rows)}")  # Debugging
                for row in rows:
                    cols = row.find_all('td')  # Poiščemo vse celice v vrstici
                    if len(cols) > 1:  # Preverimo, ali imamo vsaj dve celici
                        name = cols[1].get_text(strip=True)  # Ime tekmovalca (prvi <td>)
                        license_number = cols[0].get_text(strip=True)  # Številka licence (drugi <td>)
                        print(f"Tekmovalec: {name}, Licenca: {license_number}")  # Debugging
                        archers.append({'Name': name, 'License': license_number})

        # Če ni bilo tekmovalcev, izpišemo opozorilo
        if not archers:
            print("Ni bilo najdenih tekmovalcev.")  # Debugging
    except Exception as e:
        print(f"Napaka pri iskanju tekmovalcev: {e}")

    # Shranjevanje podatkov o klubu in tekmovalcih v CSV
    if archers:
        club_name = club_info.get('Club Short Name', 'Unknown_Club')
        filename = f"{club_name.replace(' ', '_')}.csv"

        # Debugging: Preverimo, ali imamo podatke o tekmovalcih pred zapisom v CSV
        print(f"Shranjevanje podatkov o tekmovalcih v datoteko {filename}")

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Name', 'License']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()  # Zapišemo glavo CSV-ja
            for archer in archers:
                writer.writerow(archer)  # Zapišemo vsak podatek o tekmovalcu

        print(f"Podatki za {club_name} so bili shranjeni v datoteko {filename}")
    else:
        print("Ni bilo podatkov za tekmovalce.")

    return club_info


def get_club_details1(club_url):
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

    # Inicializiramo prazni slovar za podatke o klubu
    club_info = {}
    club_info['Club Detail URL'] = club_url

    # Poiščemo vrstice (tr) z informacijami o klubu
    try:
        rows = soup.find_all('tr')

        for row in rows:
            th = row.find('th')
            td = row.find('td')

            if th and td:
                header_text = th.text.strip()
                data_text = td.text.strip()

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
                    federation_link = td.find('a')
                    if federation_link:
                        club_info['Federation'] = federation_link.text.strip()
                    else:
                        club_info['Federation'] = data_text
                elif header_text == 'Kontakti kluba':
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

    except Exception as e:
        print(f"Napaka pri obdelavi podatkov o klubu: {e}")
        return None

    # Če ni bilo najdenih ključnih podatkov o klubu, vrnemo None
    if not club_info.get('Club Name'):
        print(f"Ni bilo podatkov za klub: {club_url}")
        return None

    # Debugging: Prikaz podatkov o klubu pred zapisom
    print("Podatki o klubu:")
    for key, value in club_info.items():
        print(f"{key}: {value}")

    # Poiščemo podatke o tekmovalcih (to je ločeno iskanje)
    archers = []
    try:
        # Poiščemo zunanji <td colspan="2">, ki vsebuje notranjo tabelo s tekmovalci
        archers_section = soup.find('td', {'colspan': '2'})

        if archers_section:
            # Znotraj tega <td> poiščemo notranjo tabelo s tekmovalci
            archers_table = archers_section.find('table', {'class': 'FullSize'})

            if archers_table:
                rows = archers_table.find_all('tr')  # Poišči vse vrstice v tej notranji tabeli
                print(f"Število vrstic v tabeli s tekmovalci: {len(rows)}")  # Debugging
                for row in rows:
                    cols = row.find_all('td')  # Poišči vse celice v vrstici
                    if len(cols) > 0:
                        name = cols[0].get_text(strip=True)  # Ime tekmovalca (prvi <td>)
                        license_number = cols[1].get_text(strip=True)  # Številka licence (drugi <td>)
                        print(f"Tekmovalec: {name}, Licenca: {license_number}")  # Debugging
                        archers.append({'Name': name, 'License': license_number})

        # Če ni bilo tekmovalcev, izpišemo opozorilo
        if not archers:
            print("Ni bilo najdenih tekmovalcev.")
    except Exception as e:
        print(f"Napaka pri iskanju tekmovalcev: {e}")

    # Shranjevanje podatkov o klubu in tekmovalcih v CSV
    if archers:
        club_name = club_info.get('Club Name', 'Unknown_Club')
        filename = f"{club_name.replace(' ', '_')}.csv"

        # Debugging: Preverimo, ali imamo podatke o tekmovalcih pred zapisom v CSV
        print(f"Shranjevanje podatkov o tekmovalcih v datoteko {filename}")

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Name', 'License']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()  # Zapišemo glavo CSV-ja
            for archer in archers:
                writer.writerow(archer)  # Zapišemo vsak podatek o tekmovalcu

        print(f"Podatki za {club_name} so bili shranjeni v datoteko {filename}")
    else:
        print("Ni bilo podatkov za tekmovalce.")

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
