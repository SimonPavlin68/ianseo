import csv

with open("clubs_full_info.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(f"{row['Club Code']} - {row['Club Short Name']}")
