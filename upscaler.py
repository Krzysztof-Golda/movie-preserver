import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
import cv2
import torch
import traceback
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

def _get_device() -> str:
    if torch.backends.mps.is_available():
        print("[+] Wykryto Apple Silicon. Używam akceleracji MPS (Metal).")
        return 'mps'
    elif torch.cuda.is_available():
        print("[+] Wykryto kartę Nvidia. Używam akceleracji CUDA.")
        return 'cuda'
    else:
        print("[-] Brak akceleracji sprzętowej. Używam wolnego procesora (CPU).")
        return 'cpu'

def initialize_upscaler(model_path: str, scale: int = 4) -> RealESRGANer:
    device = _get_device()
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=scale)
    upscaler = RealESRGANer(
        scale=scale,
        model_path=model_path,
        dni_weight=None,
        model=model,
        tile=400,
        tile_pad=10,
        pre_pad=0,
        half=False,
        device=device,
    )

    return upscaler

def upscale_image(upscaler: RealESRGANer, input_image_path: str, output_image_path: str):
    img = cv2.imread(input_image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"[-] Nie można wczytać obrazu: {input_image_path}")
        return

    try:
        output_img, _ = upscaler.enhance(img, outscale=4)
        cv2.imwrite(output_image_path, output_img)
    except Exception as e:
        print(f"[-] Błąd podczas powiększania: {e}")
        print("--- SZCZEGÓŁOWY RAPORT (WYŚLIJ MI TO) ---")
        traceback.print_exc()
        print("-----------------------------------------")
        exit(1)
