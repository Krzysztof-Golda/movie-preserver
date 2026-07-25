import ffmpeg
import upscaler
import os
import shutil
import subprocess
from upscaler import initialize_upscaler, upscale_image

def get_video_fps(video_path: str) -> str:
    cmd = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=r_frame_rate',
        '-of', 'default=noprint_wrappers=1:nokey=1', video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()

def process_video(input_video: str, output_video: str, model_path: str):
    """Main pipeline for video processing 720p -> 4K"""

    print(f"\n=== ROZPOCZYNAM UPSCALING DO 4K ===")
    print(f"Plik wejściowy: {input_video}")

    temp_dir = "temp_workspace"
    frames_in_dir = os.path.join(temp_dir, "frames_in")
    frames_out_dir = os.path.join(temp_dir, "frames_out")
    audio_path = os.path.join(temp_dir, "audio.aac")

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(frames_in_dir, exist_ok=True)
    os.makedirs(frames_out_dir,exist_ok=True)

    try:
        # Pobieranie FPS
        fps = get_video_fps(input_video)
        print(f"[*] Wykryto klatkaż oryginału: {fps}")

        # Ekstrakcja audio
        print("[*] Wyodrębnianie ścieżki dźwiękowej...")
        subprocess.run(['ffmpeg', '-y', '-i', input_video, '-vn', '-acodec', 'copy', audio_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Ekstrakcja klatek
        print("[*] Rozbijanie filmu na klatki PNG...")
        subprocess.run(['ffmpeg', '-y', '-i', input_video, f"{frames_in_dir}/frame_%08d.png"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Inicjacja AI upscaling
        print("[*] Inicjalizacja modelu AI na procesorze graficznym...")
        upscaler = initialize_upscaler(model_path=model_path, scale=4)

        frames = sorted(os.listdir(frames_in_dir))
        total_frames = len(frames)
        print(f"[*] Rozpoczynam powiększanie {total_frames} klatek...")

        for idx, frame_name in enumerate(frames, 1):
            in_path = os.path.join(frames_in_dir, frame_name)
            out_path = os.path.join(frames_out_dir, frame_name)

            upscale_image(upscaler, in_path, out_path)

            # Postęp w konsoli
            if idx % 50 == 0 or idx == total_frames:
                print(f"--- Przetworzono: {idx} / {total_frames} klatek ({(idx/total_frames)*100:.1f}%) ---")

        # Renderowanie gotowego pliky 4K
        print("[*] Składanie wideo 4K w formacie H.265 (HEVC)...")

        ffmpeg_cmd = [
            'ffmpeg', '-y', '-framerate', fps,
            '-i', f"{frames_out_dir}/frame_%08d.png",
            '-i', audio_path,
            '-c:v', 'hevc_videotoolbox', '-q:v', '65', # 65 to bardzo wysoka jakość w enkoderze Apple
            '-c:a', 'copy',
            output_video
        ]

        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"\n[+] SUKCES! Gotowy film 4K zapisano jako: {output_video}")

    except Exception as e:
        print(f"\n[-] WYSTĄPIŁ BŁĄD KRYTYCZNY W POTOKU: {e}")

    finally:
        # Czyszczenie dysku z tymczasowych obrazków
        print("[*] Czyszczenie plików tymczasowych")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


# Blok testowy
if __name__ == "__main__":
    # Upewnij się, że masz plik testowy i pobrany model RealESRGAN_x4plus.pth
    process_video("test-1.mp4", "gotowy_4k.mp4", "models/RealESRGAN_x4plus.pth")
