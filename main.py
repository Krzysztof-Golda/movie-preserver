import os

from youtube_downloader import youtube_download
from hls_downloader import download_other_players
from vider_downloader import download_video

def load_links(file_name='urls.txt'):
    if not os.path.exists(file_name):
        print(f"Błąd: Nie znaleziono pliku: {file_name} w folderze programu")
        return

    with open(file_name, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file if line.strip() and not line.startswith('#')]

if __name__ == "__main__":
    print("=== MODULARNY DOWNLOADER WIDEO/AUDIO ===")
    print("1. Standardowe linki (YouTube, Vimeo itp.) -> Pobierz jako WIDEO")
    print("2. Standardowe linki (YouTube, Vimeo itp.) -> Pobierz jako AUDIO (MP3)")
    print("3. Trudne odtwarzacze (np. LuluStream)   -> Przechwytuj i pobierz WIDEO")
    print("4. Vider -> Przechwytuj i pobierz WIDEO")
    print("Q. Wyjdź z aplikacji")

    choice = input("\nWybierz tryb pracy (1/2/3/4) lub q, aby wyjść: ").strip()

    linki = load_links('urls.txt')

    if not linki:
        print("Brak linków w pliku do przetworzenia. Kończę działanie.")
        exit()

    print(f"\nZnaleziono {len(linki)} linków w pliku. Rozpoczynamy pracę...")

    num = 1
    for link in linki:
        if choice == '1':
            youtube_download(link, only_audio=False)
        elif choice == '2':
            youtube_download(link, only_audio=True)
        elif choice == '3':
            download_other_players(link, f'film_{num}')
        elif choice == '4':
            download_video(link, f'vider_film_{num}', headless=False)
            num += 1
        elif choice == 'q':
            print("Zakończono działanie programu.")
            break
        else:
            print("Nieznana opcja. Uruchom program ponownie.")
            break

    print("\n=== Zakończono przetwarzanie wszystkich linków ===")
