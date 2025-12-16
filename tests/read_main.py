import os
import subprocess

def run_first_script():
    print("Začenjam prvo skripto - pridobivanje osnovnih podatkov...")
    # Zaženemo prvo skripto, ki pridobi osnovne podatke
    subprocess.run(['python', 'read_clubs.py'])

def run_second_script():
    print("Začenjam drugo skripto - pridobivanje podrobnosti o klubih...")
    # Zaženemo drugo skripto, ki pridobi podrobnosti za vsak klub
    subprocess.run(['python', 'read_club_details.py'])

def main():
    # Preverimo, ali že obstaja CSV datoteka z osnovnimi podatki
    if not os.path.exists('clubs_basic_info.csv'):
        print("CSV datoteka z osnovnimi podatki ne obstaja. Začnemo s prvo skripto...")
        run_first_script()  # Prvi del - pridobivanje osnovnih podatkov

    # Ko imamo osnovne podatke, zaženemo drugo skripto za podrobnosti
    run_second_script()  # Drugi del - pridobivanje podrobnosti za vsak klub

if __name__ == "__main__":
    main()
