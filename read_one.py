import requests
from bs4 import BeautifulSoup
import csv
import re

URL = "https://www.ianseo.net/TourData/2025/23259/IC.php"
OUTPUT_FILE = "rezultati-1.csv"

resp = requests.get(URL)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")


def clean_club(text):
  # zamenjaj NBSP s space
  text = text.replace('\xa0', ' ')
  # zgladi večkratne presledke v enega
  text = re.sub(r'\s+', ' ', text)
  # odstrani presledke na začetku in koncu
  return text.strip()

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as out:
    writer = csv.writer(out)
    writer.writerow(["Kategorija", "Tekmovalec", "Klub", "Skupaj"])

    current_category = "?"

    # Poberemo vse tabele (lahko jih je več)
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            ths = tr.find_all("th")
            tds = tr.find_all("td")

            # Če je vrstica samo s kategorijo
            if len(ths) == 1 and "colspan" in ths[0].attrs:
                current_category = ths[0].get_text(strip=True)
                continue

            # Če je to vrstica s tekmovalcem
            if len(tds) >= 5:
                tekmovalec = tds[1].get_text(strip=True)
                klub = clean_club(tds[2].get_text(strip=True))
                skupaj = tds[4].get_text(strip=True)
                writer.writerow([current_category, tekmovalec, klub, skupaj])
