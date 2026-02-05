# 1️⃣ obstoječe funkcije: parse_competition_info, count_and_date, process_competitions

# 2️⃣ zagon obdelave tekme
if __name__ == "__main__":
    process_competitions(
        "tekme.json",
        "udelezba.json"
    )

    # 3️⃣ graf udeležbe
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
    labels = [d["Tekmovanje"].split("\n")[0] for d in data]

    # nariši graf
    plt.figure(figsize=(12,6))
    plt.plot(x, y, marker="o", linestyle="-", color="dodgerblue")
    plt.title("Udeležba na tekmah po datumu")
    plt.xlabel("Datum")
    plt.ylabel("Število tekmovalcev")
    plt.grid(True)

    for i, val in enumerate(y):
        plt.text(x[i], val+2, str(val), ha='center', fontsize=8)

    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig("output/udelezba_graf.png")
    plt.show()
