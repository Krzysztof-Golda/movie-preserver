from matplotlib.pylab import extract
import gfpgan
import ffmpeg
import upscaler
import os
import shutil
import subprocess
from upscaler import initialize_upscaler, upscale_image, initialize_face_enhancer

INPUT_DIR = "filmy_do_poprawy"
OUTPUT_DIR = "gotowe_filmy"
TEMP_IN = "temp_frames_in"
TEMP_OUT = "temp_frames_out"
MODELS_DIR = "models"

MODEL_PATH = f"{MODELS_DIR}/4x-UltraSharp.pth"
GFPGAN_PATH = f"{MODELS_DIR}/GFPGANv1.4.pth"
SCALE = 4 # Ustawienie 2 -> 1400p, 4 -> 4K

def ensure_dirs():
    """Check if all directories exists."""
    for d in [INPUT_DIR, OUTPUT_DIR, TEMP_IN, TEMP_OUT]:
        os.makedirs(d, exist_ok=True)

def clear_temp_dirs():
    """Clean temporary folders after work done."""
    for d in [TEMP_IN, TEMP_OUT]:
        for filename in os.listdir(d):
            filepath = os.path.join(d, filename)
            if os.path.isfile(filepath):
                os.remove(filepath)

def get_video_fps(video_path: str) -> str:
    """Get original number of FPS from video."""
    cmd = [
        'ffprobe', '-v', 'error', '-select_streams', 'v',
        '-show_entries', 'stream=r_frame_rate',
        '-of', 'default=noprint_wrappers=1:nokey=1', video_path
    ]
    output = subprocess.check_output(cmd).decode('utf-8').strip()
    return output

def run_batch_upscaling():
    ensure_dirs()

    # Szukanie plików w INPUT_DIR
    valid_extensions = ('.mp4', '.mvk', '.avi', '.mov')
    videos = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(valid_extensions)]

    if not videos:
        print(f"\n[-] Folder '{INPUT_DIR}' jest pusty. Wrzuć tam jakieś filmy i spróbuj ponownie!")
        return

    print(f"\n[*] Znaleziono {len(videos)} film(ów) do przetworzenia.")

    #Inicjacja modeli AI
    print("[*] Ładowanie modeli AI do pamięci")
    upscaler = initialize_upscaler(model_path=MODEL_PATH, scale=SCALE)

    face_enhancer = None
    if os.path.exists(GFPGAN_PATH):
        print("[*] Wczytano moduł GFPGAN.")
        face_enhancer = initialize_face_enhancer(GFPGAN_PATH, upscaler)
    else:
        print("[-] Nie znaleziono modelu GFPGAN, twarze nie będą rekonstruowane.")

    # Pętla dla każdego filmu
    for idx, video_name in enumerate(videos, 1):
        input_video_path = os.path.join(INPUT_DIR, video_name)
        output_video_path = os.path.join(OUTPUT_DIR, f"UPSCALED_{video_name}")

        print(f"\n"+"-"*40)
        print(f"🎬 PRZETWARZANIE WIDEO {idx}/{len(videos)}: {video_name}")
        print("-"*40)

        clear_temp_dirs()
        fps = get_video_fps(input_video_path)

        # ETAP 1 - Wyciąganie klatek
        print("[1/3] Rozpakowywanie wideo na klatki...")
        extract_cmd = [
            'ffmpeg', '-i', input_video_path,
            '-qscale:v', '1', '-qmin', '1',
            os.path.join(TEMP_IN, 'frame_%08d.jpg')
        ]
        subprocess.run(extract_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        frames = sorted(os.listdir(TEMP_IN))
        total_frames = len(frames)
        print(f"      Wyciągnięto {total_frames} klatek. FPS: {fps}")

        # ETAP 2 - Upscaling klatek
        print("[2/3] AI: Upcaling klatek")
        for i, frame_name in enumerate(frames, 1):
            in_frame = os.path.join(TEMP_IN, frame_name)
            out_frame = os.path.join(TEMP_OUT, frame_name)

            upscale_image(upscaler, in_frame, out_frame, face_enhancer)

            if i % 50 == 0 or i == total_frames:
                print(f"      Postęp: {i}/{total_frames} ({(i/total_frames)*100:.1f}%)")

        # ETAP 3 - Składanie wideo w całość
        print("[3/3] Kompresja z powrotem do pliku wideo i synchronizacja audio...")
        merge_cmd = [
            'ffmpeg', '-y',
            '-framerate', fps,
            '-i', os.path.join(TEMP_OUT, 'frame_%08d.jpg'), # Wczytaj powiększone klatki
            '-i', input_video_path,                         # Wczytaj oryginał po dźwięk
            '-map', '0:v:0',                                # Weź obraz z klatek
            '-map', '1:a:0?',                               # Weź pierwszy kanał audio z oryginału (jeśli istnieje)
            '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', # Znakomita jakość obrazu H.264
            '-c:a', 'copy',                                 # Kopiuj audio bezstratnie 1:1
            output_video_path
        ]
        subprocess.run(merge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print(f"[+] ZAKOŃCZONO! Film zapisany jako: {output_video_path}")
        clear_temp_dirs()

    print("\n[+] Przetwarzanie folderu pomyślnie")


# Blok testowy
# if __name__ == "__main__":
    # Upewnij się, że masz plik testowy i pobrany model RealESRGAN_x4plus.pth
    # process_video("test-1.mp4", "gotowy_4k.mp4", "models/4x-UltraSharp.pth")
