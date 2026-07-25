from playwright.sync_api import sync_playwright
import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget
import os

def save_cookies_netscape(cookies, file_name="cookies_playwright.txt"):
    """Konwetuje ciasteczka z Playwright na standardowy format Netscape dla yt-dlp."""
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write('# Netscape HTTP Cookie File\n')
        for c in cookies:
            domain = c.get('domain', '')
            initial_dot = 'TRUE' if domain.startswith('.') else 'FALSE'
            path = c.get('path', '/')
            secure = 'TRUE' if c.get('secure', False) else 'FALSE'

            expires = c.get('expires', 0)
            if expires < 0:
                expires = 0
            else:
                expires = int(expires)

            name = c.get('name', '')
            value = c.get('value', '')
            file.write(f"{domain}\t{initial_dot}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")

def download_other_players(page_url, file_name: str):
    print(f"\n[Moduł HLS] Przechwytywanie strumienia ze strony: {page_url}")
    m3u8_founded = None
    quest_headers = {}

    def quest_process(request):
        nonlocal m3u8_founded, quest_headers
        if ".m3u8" in request.url and not m3u8_founded:
            print(f"[+] Przechwycono strumień m3u8!")
            m3u8_founded = request.url
            quest_headers = request.headers


    with sync_playwright() as p:
        print("[*] Otwieranie przeglądarki... (ZAMKNIJ REKLAMY I KLIKNIJ PLAY, JEŚLI TRZEBA)")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.on("request", quest_process)

        try:
            page.goto(page_url)
        except Exception as e:
            print(f"[-] Błąd ładowania strony: {e}")

        for _ in range(60):
            if m3u8_founded:
                break
            page.wait_for_timeout(1000)

        if not m3u8_founded:
            print("[-] Nie udało się przechwycić strumienia w ciągu 60 sekund. Pomijam.")
            browser.close()
            return

        cookies = context.cookies()
        save_cookies_netscape(cookies, 'cookies_playwrith.txt')
        browser.close()

    print("[*] Rozpoczynam pobieranie przechwyconego strumienia...")
    headers_to_pass = {
        'User-Agent': quest_headers.get('user-agent', ''),
        'Referer': quest_headers.get('referer', page_url),
    }
    if 'origin' in quest_headers:
        headers_to_pass['Origin'] = quest_headers['origin']

    ydl_opts = {
        # 'outtmpl': '%(title)s-2.%(ext)s',
        'outtmpl': f"{file_name}.%(ext)s",
        'cookiefile': 'cookies_playwright.txt',
        'impersonate': ImpersonateTarget(client='chrome'),
        'http_headers': headers_to_pass
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([m3u8_founded])
            print("[+] Sukces: Pobrane wideo z zewnętrznego odtwarzacza!")
        except Exception as e:
            print(f"[-] Błąd yt-dlp podczas pobierania ukrytego strumienia: {e}")

    if os.path.exists("cookies_playwright.txt"):
        os.remove("cookies_playwright.txt")
