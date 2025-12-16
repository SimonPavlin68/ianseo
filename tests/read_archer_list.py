import pandas as pd

url = "https://slo.service.ianseo.net/General/ArcherList.php"

# preberi vse tabele na strani
tables = pd.read_html(url)

# ponavadi je prva prava
df = tables[0]

print(df.columns)
print(df.head())
