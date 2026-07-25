import os
import yt_dlp
from playwright.sync_api import sync_playwright

def _save_cookies_to_netscape(cookies: list, filename: str):
    """
    Prywatna funkcja: Konwertuje ciasteczka z Playwright na format Netscape (wymagany przez yt-dlp).
    """
    with open(filename, 'w') as f:
        f.write("# Netscape HTTP Cookie File\n")
        for c in cookies:
            domain = c.get('domain', '')
            flag = 'TRUE' if domain.startswith('.') else 'FALSE'
            path = c.get('path', '/')
            secure = 'TRUE' if c.get('secure', False) else 'FALSE'

            # Obsługa czasu wygaśnięcia ciasteczka
            expires = c.get('expires', -1)
            expires_str = str(int(expires)) if expires > 0 else '0'

            name = c.get('name', '')
            value = c.get('value', '')

            f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expires_str}\t{name}\t{value}\n")

def _extract_stream(page_url: str, headless: bool = False):
    """
    Prywatna funkcja: Wchodzi na stronę Vider, przechwytuje link i zapisuje ciasteczka sesji.
    """
    print(f"[*] Rozpoczynam nasłuchiwanie na stronie Vider: {page_url}")
    captured_url = None
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def handle_request(request):
        nonlocal captured_url
        url = request.url
        if ('.mp4' in url or '.m3u8' in url) and 'ad' not in url.lower():
            if not captured_url:
                captured_url = url
                print(f"[+] Przechwycono strumień: {captured_url.split('?')[0]}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)

        context = browser.new_context(
            user_agent=user_agent,
            viewport={'width': 1280, 'height': 720}
        )

        page = context.new_page()
        page.on("request", handle_request)

        try:
            page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

            dimensions = page.viewport_size
            if dimensions:
                page.mouse.click(dimensions['width'] / 2, dimensions['height'] / 2)

            for _ in range(15):  # Zwiększono czas oczekiwania do 15 sekund
                if captured_url:
                    break
                page.wait_for_timeout(1000)

            # KLUCZOWY MOMENT: Zapisujemy autoryzację przed zamknięciem przeglądarki
            cookies = context.cookies()
            _save_cookies_to_netscape(cookies, "vider_cookies.txt")
            print("[+] Ciasteczka sesji zostały pomyślnie zgrane.")

        except Exception as e:
            print(f"[-] Wystąpił błąd podczas automatyzacji Playwright: {e}")
        finally:
            browser.close()

    return captured_url, user_agent

def _download_direct_stream(direct_url: str, filename: str, referer: str, user_agent: str):
    """
    Prywatna funkcja: Pobiera plik, udając przeglądarkę z Playwrighta.
    """
    ydl_opts = {
        'outtmpl': f'{filename}.%(ext)s',
        'cookiefile': 'vider_cookies.txt', # Używamy zrzuconych ciasteczek
        'http_headers': {
            'User-Agent': user_agent,
            'Referer': referer, # Serwer musi wiedzieć, z jakiej strony odtwarzamy wideo
            'Origin': referer.split('/')[0] + '//' + referer.split('/')[2]
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([direct_url])
    finally:
        # Sprzątamy plik z ciasteczkami po udanym (lub nieudanym) pobraniu
        if os.path.exists("vider_cookies.txt"):
            os.remove("vider_cookies.txt")

def download_video(page_url: str, filename: str, headless: bool = False):
    """
    Główna funkcja publiczna. Zawsze używaj headless=False dla Videra.
    """
    raw_stream_url, user_agent = _extract_stream(page_url, headless)

    if raw_stream_url:
        print("\n[*] Rozpoczynam pobieranie fizycznego pliku z pełną autoryzacją...")
        _download_direct_stream(raw_stream_url, filename, referer=page_url, user_agent=user_agent)
    else:
        print("[-] Przerwano proces pobierania z powodu braku strumienia.")
