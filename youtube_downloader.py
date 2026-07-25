import yt_dlp

def youtube_download(url, only_audio):
    print(f"\n[Moduł YT] Rozpoczynam przetwarzanie: {url}")

    download_whole_playlist = False

    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)

            if info and 'entries' in info:
                entries = list(info["entries"])
                title = info.get('title', 'Unknown')
                print(f"WYKRYTO PLAYLISTE: '{title}' (zawiera {len(entries)} elementów).")

                while True:
                    choice = input("> Pobieramy CAŁĄ playlistę? (t - tak / n - nie, tylko pojedynczy film / p - pomiń całkowicie): ").strip().lower()
                    if choice == 't':
                        download_whole_playlist = True
                        break
                    elif choice == 'n':
                        download_whole_playlist = False
                        break
                    elif choice == 'p':
                        print("> Pominięto link.")
                        return

    except Exception as e:
        print("> Ostrzeżenie: Nie udało się przeanalizować linku przed pobraniem (może nie być wspierany). Próbuję pobrać bezpośrednio...")

    ydl_opts = {
        'outtmpl': '%(extractor)s/%(title)s.%(ext)s' if not download_whole_playlist else '%(extractor)s/%(playlist_title)s/%(title)s.%(ext)s',
        'noplaylist': not download_whole_playlist,
        'writethumbnail': True,
        'quiet': False
    }

    if only_audio:
        print("[Moduł YT] Tryb: AUDIO (MP3)")
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [
        {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        },
        {
            'key': 'EmbedThumbnail',
        },
        {
            'key': 'FFmpegMetadata',
        }]
    else:
        print("[Moduł YT] Tryb: WIDEO")
        ydl_opts['format'] = 'best'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            print(f"[+] Sukces: Pobrano plik z {url}")
        except Exception as e:
            print(f"[-] Błąd pobierania w module YT: {e}")
