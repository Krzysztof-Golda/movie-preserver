from sympy.physics.units import g
import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
import cv2
import torch
import traceback
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer
from gfpgan import GFPGANer

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

def convert_esrgan_keys(state_dict):
    if 'conv_first.weight' in state_dict:
        return state_dict

    new_state_dict = {}
    for k, v in state_dict.items():
        if not isinstance(k, str):
            new_state_dict[k] = v
            continue

        if k.startswith('model.0.'):
            new_state_dict[k.replace('model.0.', 'conv_first.')] = v
        elif k.startswith('model.1.sub.'):
            parts = k.split('.')
            if len(parts) == 8:
                block_idx, rdb_idx, conv_idx, param_type = parts[3], parts[4].lower(), parts[5], parts[7]
                new_state_dict[f"body.{block_idx}.{rdb_idx}.{conv_idx}.{param_type}"] = v
            elif len(parts) == 5:
                new_state_dict[f"conv_body.{parts[4]}"] = v
        elif k.startswith('model.3.'):
            new_state_dict[k.replace('model.3.', 'conv_up1.')] = v
        elif k.startswith('model.6.'):
            new_state_dict[k.replace('model.6.', 'conv_up2.')] = v
        elif k.startswith("model.8."):
                    new_state_dict[k.replace("model.8.", "conv_hr.")] = v
        elif k.startswith("model.10."):
            new_state_dict[k.replace("model.10.", "conv_last.")] = v
        else:
            new_state_dict[k] = v
    return new_state_dict

def initialize_upscaler(model_path: str, scale: int = 4) -> RealESRGANer:
    device = _get_device()
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=scale)

    loadnet = torch.load(model_path, map_location='cpu')

    if 'params_ema' in loadnet:
        state_dict = loadnet['params_ema']
    elif 'params' in loadnet:
        state_dict = loadnet['params']
    else:
        state_dict = loadnet

    state_dict = convert_esrgan_keys(state_dict)

    original_torch_load = torch.load
    try:
        torch.load = lambda *args, **kwargs: {'params': state_dict}

        upscaler = RealESRGANer(
            scale=scale,
            model_path='None',
            dni_weight=None,
            model=model,
            tile=400,
            tile_pad=10,
            pre_pad=0,
            half=False,
            device=device,
        )

    # model.load_state_dict(state_dict, strict=True)
    finally:
        torch.load = original_torch_load

    return upscaler

def initialize_face_enhancer(gfpgan_model_path: str, bg_upscaler: RealESRGANer) -> GFPGANer:
    face_enhancer = GFPGANer(
        model_path=gfpgan_model_path,
        upscale=bg_upscaler.scale,
        arch='clean',
        channel_multiplier=2,
        bg_upsampler=bg_upscaler,
        device=_get_device()
    )
    return face_enhancer

def upscale_image(upscaler: RealESRGANer, input_image_path: str, output_image_path: str, face_enhancer: GFPGANer | None = None):
    img = cv2.imread(input_image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"[-] Nie można wczytać obrazu: {input_image_path}")
        return

    try:
        if face_enhancer is not None:
            _, _, output_img = face_enhancer.enhance(img, has_aligned=False, only_center_face=False, paste_back=True)
        else:
            output_img, _ = upscaler.enhance(img, outscale=4)

        cv2.imwrite(output_image_path, output_img)
    except Exception as e:
        print(f"[-] Błąd podczas powiększania: {e}")
        print("--- SZCZEGÓŁOWY RAPORT (WYŚLIJ MI TO) ---")
        traceback.print_exc()
        print("-----------------------------------------")
        exit(1)
