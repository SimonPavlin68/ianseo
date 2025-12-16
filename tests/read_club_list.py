import requests
import pandas as pd
from io import BytesIO

url = "https://slo.service.ianseo.net/General/PrintOds.php?DocType=ClubList"
headers = {"User-Agent": "Mozilla/5.0"}

r = requests.get(url, headers=headers)
r.raise_for_status()

df = pd.read_excel(BytesIO(r.content))

# če je Reference prazna, vzemi Club Name
df["Short"] = df["Reference"].fillna(df["Club Name"])

for _, row in df.iterrows():
    print(f"{int(row['Club Code'])} - {row['Short']}")
