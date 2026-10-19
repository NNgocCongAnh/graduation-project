"""Test script for Local Image Generation using Stable Diffusion 1.5.

Optimized for NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM).
Generates:
1. Suspect Portrait (Polaroid / 1990s Police Interrogation Mugshot).
2. Crime Scene Evidence (Broken Pocket Watch with forensic marker).
"""

import os
import time
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

def run_test():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    print(f"=== TEST LOCAL IMAGE GENERATION (SD 1.5) ===")
    print(f"Device: {device} ({torch.cuda.get_device_name(0) if device == 'cuda' else 'CPU'})")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB\n")

    output_dir = os.path.join(os.path.dirname(__file__), "test_outputs")
    os.makedirs(output_dir, exist_ok=True)

    # 1. Load SD 1.5 pipeline from local HuggingFace cache
    print("⏳ Đang nạp mô hình Stable Diffusion 1.5 (FP16)...")
    load_start = time.time()
    
    model_id = "stable-diffusion-v1-5/stable-diffusion-v1-5"
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=dtype,
        safety_checker=None,
    )
    # Dùng scheduler DPM++ 2M Karras (cho chất lượng sắc nét vượt trội chỉ với 20 steps)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)
    pipe.to(device)

    # Bật xformers / attention slicing chống tràn 4GB VRAM
    pipe.enable_attention_slicing()
    print(f"✅ Đã nạp xong mô hình trong {time.time() - load_start:.2f}s!\n")

    # Negative prompt chung chuẩn để loại bỏ tranh vẽ, 3D CGI và biến dạng khuôn mặt
    negative_prompt = (
        "(deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, "
        "extra limb, missing limb, floating limbs, (mutated hands and fingers:1.4), disconnected limbs, "
        "mutation, mutated, ugly, disgusting, blurry, amputation, (cartoon, anime, 3d render, cgi, illustration:1.3), "
        "oversaturated, bad art, poorly drawn face, poorly drawn eyes"
    )

    # --- TEST 1: CHÂN DUNG NGHI PHẠM (SUSPECT MUGSHOT / POLAROID) ---
    suspect_prompt = (
        "authentic vintage police mugshot photograph of a 55-year-old male butler, Arthur William, "
        "tired stern expression, looking directly into camera, frontal head and shoulders portrait, "
        "wearing a worn black formal butler vest, plain grey interrogation room wall background, "
        "height measurement chart on wall, harsh 1990s flash photography, 35mm analog film grain, "
        "realistic detailed skin texture, raw criminal case file photo"
    )

    print("📸 [Test 1/2] Đang sinh ảnh thẻ nghi phạm (Quản gia William)...")
    start_t = time.time()
    generator = torch.Generator(device=device).manual_seed(2026)
    
    with torch.inference_mode():
        image_suspect = pipe(
            prompt=suspect_prompt,
            negative_prompt=negative_prompt,
            width=512,
            height=512,
            num_inference_steps=20,
            guidance_scale=7.5,
            generator=generator,
        ).images[0]
    
    suspect_path = os.path.join(output_dir, "test_suspect_william.png")
    image_suspect.save(suspect_path)
    print(f"✅ Hoàn thành ảnh nghi phạm trong {time.time() - start_t:.2f}s! Đã lưu: {suspect_path}\n")

    # --- TEST 2: VẬT CHỨNG HIỆN TRƯỜNG (CRIME EVIDENCE) ---
    evidence_prompt = (
        "gritty police forensic evidence photograph, top-down view, "
        "a vintage cracked silver pocket watch lying flat on dark wooden floorboards, "
        "shattered glass face, broken clock hands, yellow plastic police evidence marker numbered '01' beside it, "
        "sharp forensic scale ruler, directional flashlight glare, dark gritty crime scene mood, authentic 35mm investigation photo"
    )

    print("🔍 [Test 2/2] Đang sinh ảnh vật chứng (Đồng hồ bỏ túi bị vỡ)...")
    start_t = time.time()
    generator = torch.Generator(device=device).manual_seed(42)
    
    with torch.inference_mode():
        image_evidence = pipe(
            prompt=evidence_prompt,
            negative_prompt=negative_prompt,
            width=512,
            height=512,
            num_inference_steps=20,
            guidance_scale=7.5,
            generator=generator,
        ).images[0]
    
    evidence_path = os.path.join(output_dir, "test_evidence_watch.png")
    image_evidence.save(evidence_path)
    print(f"✅ Hoàn thành ảnh vật chứng trong {time.time() - start_t:.2f}s! Đã lưu: {evidence_path}\n")

    print(f"🎉 TẤT CẢ ẢNH ĐÃ ĐƯỢC XUẤT THÀNH CÔNG VÀO THƯ MỤC:\n{output_dir}")

if __name__ == "__main__":
    run_test()

