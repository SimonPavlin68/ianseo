import pandas as pd

import pandas as pd

import pandas as pd

import pandas as pd

import pandas as pd

import pandas as pd

import pandas as pd


def main():
    input_file = '../rezultati_filtrirani.csv'
    output_file = 'statistika_lk_sencur_po_tipu.csv'

    # 1. Naloži podatke
    df = pd.read_csv(input_file)

    # 2. Filtriraj samo LK Šenčur
    lk = df[df['Klub'].str.contains('Šenčur', case=False, na=False)]

    # 3. Pripravi prazno listo za rezultate
    rezultati = []

    # 4. Obdelaj vsak Tip posebej
    for tip, grupa in lk.groupby('Tip'):
        # Odstrani vse nove vrstice (vključno z '\r' in '\n')
        grupa['Tekmovanje'] = grupa['Tekmovanje'].str.replace(r'[\r\n]+', ' ', regex=True).str.strip()

        # Izračunaj število mest
        prvi_tekmovalci = grupa[grupa['Mesto'] == 1][
            ['Tekmovalec', 'Tekmovanje']].values.tolist()  # Seznam (Tekmovalec, Tekmovanje)

        # Dodaj statistiko
        rezultati.append({
            'Tip': tip,
            '1_mesto': (grupa['Mesto'] == 1).sum(),
            '2_mesto': (grupa['Mesto'] == 2).sum(),
            '3_mesto': (grupa['Mesto'] == 3).sum(),
            'Skupaj_nastopov': len(grupa)
        })

        # Izpis prvih mest (prvih tekmovalcev in tekmovanj) za vsak tip
        print(f"\nPrvi tekmovalci za Tip: {tip}")
        if not prvi_tekmovalci:  # Preveri, če so zmagovalci
            print(" - Ni prvih mest")
        else:
            for tekmovalec, tekmovanje in prvi_tekmovalci:
                print(f" - {tekmovalec} - {tekmovanje}")

    # 5. Pretvori v DataFrame
    stats_df = pd.DataFrame(rezultati).sort_values('Tip')

    # 6. Izpis statistike
    print('\nStatistika LK Šenčur po tipu\n')
    print(stats_df.to_string(index=False))

    # 7. Shrani v CSV
    stats_df.to_csv(output_file, index=False)


if __name__ == '__main__':
    main()
