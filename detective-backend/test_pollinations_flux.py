"""Test script for Cloud-based FLUX Image Generation via Pollinations.ai (100% Free, No API Key).

Fetches:
1. Suspect Portrait: Butler William (55yo, 1990s detective interrogation style).
2. Evidence Item: Broken Silver Pocket Watch on crime scene parquet floor.
"""

import os
import time
import urllib.parse
import urllib.request

def fetch_pollinations_image(prompt: str, output_path: str, model: str = "flux", width: int = 768, height: int = 768, seed: int = 42):
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model={model}&seed={seed}&nologo=true"
    
    print(f"🌐 Đang gọi Cloud FLUX API: {prompt[:70]}...")
    start_time = time.time()
    
    # Request headers to look like standard client
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DetectiveGameEngine/1.0"}
    )
    
    with urllib.request.urlopen(req, timeout=60) as response:
        content = response.read()
        with open(output_path, "wb") as f:
            f.write(content)
            
    elapsed = time.time() - start_time
    print(f"✅ Hoàn thành trong {elapsed:.2f} giây! Đã lưu: {output_path} ({len(content) / 1024:.1f} KB)\n")
    return elapsed

def main():
    output_dir = os.path.join(os.path.dirname(__file__), "test_outputs_cloud")
    os.makedirs(output_dir, exist_ok=True)
    
    print("=== TEST CLOUD IMAGE GENERATION (FLUX.1 via Pollinations AI - 100% Free) ===\n")
    
    # Test 1: Chân dung nghi phạm
    suspect_prompt = (
        "vintage 1990s authentic police mugshot photo of a 55-year-old male butler named William, "
        "stern tired facial expression, looking straight into camera, frontal head and shoulders portrait, "
        "wearing a worn formal black waistcoat and crisp white shirt, grey police interrogation room wall background, "
        "harsh flash photography, 35mm film grain, hyperrealistic skin details, raw case file photo"
    )
    suspect_path = os.path.join(output_dir, "cloud_flux_suspect_william.png")
    fetch_pollinations_image(suspect_prompt, suspect_path, model="flux", seed=101)
    
    # Test 2: Vật chứng hiện trường
    evidence_prompt = (
        "top-down flat lay forensic police crime scene photograph, "
        "an antique silver pocket watch lying flat on a dark scratched vintage wooden floor, "
        "the glass face is cracked with hands clearly frozen at exactly 9:40, "
        "beside the watch is a crisp yellow plastic police evidence marker tent with bold black number '01', "
        "harsh crime scene flashlight beam, forensic evidence scale ruler beside it, highly detailed, authentic 35mm photo"
    )
    evidence_path = os.path.join(output_dir, "cloud_flux_evidence_watch.png")
    fetch_pollinations_image(evidence_prompt, evidence_path, model="flux", seed=202)
    
    print(f"🎉 TẤT CẢ ẢNH ĐÃ ĐƯỢC TẢI VỀ THÀNH CÔNG TẠI:\n{output_dir}")

if __name__ == "__main__":
    main()

