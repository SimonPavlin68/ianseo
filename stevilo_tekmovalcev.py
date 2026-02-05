import json
import requests
from bs4 import BeautifulSoup


# ============================================================
# 1. PARSER INFORMACIJ O TEKMI  (tvoja logika)
# ============================================================

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
    deli_teksta = [
        BeautifulSoup(s, "html.parser").get_text(strip=True)
        for s in deli_teksta if s.strip()
    ]

    klub = deli_teksta[0] if len(deli_teksta) > 0 else ""
    lokacija = ""
    datum = ""

    if len(deli_teksta) > 1:
        raw = deli_teksta[1]
        parts = raw.rsplit(",", 1)

        if len(parts) == 2:
            lokacija = parts[0].strip()
            datum_raw = parts[1].strip()

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
        else:
            lokacija = raw

        # Tvoji popravki lokacij
        if "Slovenia" in lokacija:
            lokacija = lokacija.replace("Slovenia", "").strip()

        if "Postojna" in lokacija:
            lokacija = "Postojna"

        if lokacija == "Športna dvorana Kamnik":
            lokacija = "Kamnik"

        if lokacija == "Telovadnica srednje šole Lendava":
            lokacija = "Lendava"

    return ime_tekme, klub, lokacija, datum


# ============================================================
# 2. ŠTETJE TEKMOVALCEV + DATUM
# ============================================================

def count_and_date(url):
    resp = requests.get(url)
    resp.raise_for_status()

    html = resp.text

    ime_tekme, klub, lokacija, datum = parse_competition_info(html)

    soup = BeautifulSoup(html, "html.parser")

    count = 0
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")

            if len(tds) >= 5:
                first = tds[0].get_text(strip=True)
                if first.isdigit():
                    count += 1

    return {
        "Tekmovanje": ime_tekme,
        "Klub": klub,
        "Lokacija": lokacija,
        "Datum": datum,
        "Stevilo": count,
        "Url": url
    }


# ============================================================
# 3. OBDELAVA SEZNAMA TEKEM
# ============================================================

def process_competitions(json_in, json_out):
    with open(json_in, "r", encoding="utf-8") as f:
        competitions = json.load(f)

    results = []

    for comp in competitions:
        url = comp["url"]
        info = comp.get("info", "")

        print(f"🔎 {info}")

        try:
            r = count_and_date(url)
            results.append(r)

            print(f"   ✅ {r['Stevilo']} tekmovalcev | {r['Datum']}")

        except Exception as e:
            print(f"   ❌ napaka: {e}")

            results.append({
                "Tekmovanje": info,
                "Stevilo": 0,
                "Datum": "",
                "Url": url,
                "Napaka": str(e)
            })

    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


# ============================================================
# 4. ZAGON
# ============================================================

# 1️⃣ obstoječe funkcije: parse_competition_info, count_and_date, process_competitions

# 2️⃣ zagon obdelave tekme
if __name__ == "__main__":
    #process_competitions(
    #    "tekme.json",
    #    "udelezba.json"
    #)

    import matplotlib.pyplot as plt
    from datetime import datetime
    import json

    # --- preberi JSON ---
    with open("udelezba.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # filtriraj samo tiste z datumom
    data = [d for d in data if d.get("Datum")]

    # pretvori datume
    for d in data:
        d["DatumObj"] = datetime.strptime(d["Datum"], "%d.%m.%Y")

    # sortiraj po datumu
    data.sort(key=lambda x: x["DatumObj"])

    # X in Y
    x = [d["DatumObj"] for d in data]
    y = [d["Stevilo"] for d in data]
    labels = [d["Tekmovanje"].split("\n")[0] for d in data]  # ime tekme
    locations = [d.get("Lokacija", "") for d in data]  # kraj tekme

    # --- povprečje ---
    avg = sum(y) / len(y) if y else 0

    # nariši graf
    plt.figure(figsize=(12, 6))
    plt.plot(x, y, marker="o", linestyle="-", color="dodgerblue", label="Število tekmovalcev")

    # vodoravna črta povprečja
    plt.axhline(y=avg, color="red", linestyle="--", label=f"Povprečno: {avg:.1f}")

    # oznake nad markerji
    for i, val in enumerate(y):
        plt.text(x[i], val + 2, f"{val} ({locations[i]})", ha='center', fontsize=8)

    plt.title("Udeležba na tekmah po datumu")
    plt.xlabel("Datum")
    plt.ylabel("Število tekmovalcev")
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=30)
    plt.tight_layout()

    plt.savefig("udelezba_graf.png")
    plt.show()

