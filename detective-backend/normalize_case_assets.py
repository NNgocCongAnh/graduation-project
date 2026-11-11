import os
from PIL import Image, ImageOps, ImageFilter, ImageEnhance

base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static", "assets")
suspects_dir = os.path.join(static_dir, "suspects")
evidences_dir = os.path.join(static_dir, "evidences")

def make_cohesive_photo(img: Image.Image, size=(400, 400), b_and_w=True, grain=True) -> Image.Image:
    # 1. Center crop to 1:1 square
    w, h = img.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    cropped = img.crop((left, top, left + min_dim, top + min_dim)).resize(size, Image.Resampling.LANCZOS)
    
    if b_and_w:
        # High contrast, rich noir monochrome with deep shadows
        gray = cropped.convert("L")
        enhancer = ImageEnhance.Contrast(gray)
        gray = enhancer.enhance(1.35)
        # Subtle sepia tone (silver gelatin print look)
        colorized = ImageOps.colorize(gray, black="#100e0d", white="#f4efe6")
        cropped = colorized.convert("RGBA")
    
    return cropped

print("=== CHUẨN HÓA BỘ ẢNH CHÂN DUNG & CHỨNG CỨ THÀNH BỘ ẢNH THẬT ĐỒNG NHẤT ===")

# 1. Fix evidence_glass: Crop out the fake polaroid borders
p_glass = os.path.join(evidences_dir, "evidence_glass.png")
if os.path.exists(p_glass):
    orig = Image.open(p_glass)
    # The inner photo is roughly from x=20..380, y=30..330
    w, h = orig.size
    inner = orig.crop((int(w * 0.08), int(h * 0.08), int(w * 0.92), int(h * 0.76)))
    fixed = make_cohesive_photo(inner, b_and_w=True)
    fixed.save(p_glass)
    print("[+] Normalized evidence_glass.png (Pure crime scene floor crop)")

# 2. Fix evidence_teacup: Crop out the fake polaroid border and text
p_teacup = os.path.join(evidences_dir, "evidence_teacup.png")
if os.path.exists(p_teacup):
    orig = Image.open(p_teacup)
    w, h = orig.size
    inner = orig.crop((int(w * 0.08), int(h * 0.06), int(w * 0.92), int(h * 0.74)))
    fixed = make_cohesive_photo(inner, b_and_w=True)
    fixed.save(p_teacup)
    print("[+] Normalized evidence_teacup.png (Pure table teacup macro crop)")

# 3. Fix pocket_watch_broken: crop square macro shot, remove yellow ruler distraction
p_watch = os.path.join(evidences_dir, "pocket_watch_broken.png")
if os.path.exists(p_watch):
    orig = Image.open(p_watch)
    w, h = orig.size
    # Center slightly to the right to exclude the yellow tool on left
    inner = orig.crop((int(w * 0.18), int(h * 0.02), int(w * 0.98), int(h * 0.82)))
    fixed = make_cohesive_photo(inner, b_and_w=True)
    fixed.save(p_watch)
    print("[+] Normalized pocket_watch_broken.png (Silver gelatin pocket watch)")

# 4. Fix butler_male_50s: Crop squarely on butler portrait
p_butler = os.path.join(suspects_dir, "butler_male_50s.png")
if os.path.exists(p_butler):
    orig = Image.open(p_butler)
    w, h = orig.size
    inner = orig.crop((int(w * 0.05), int(h * 0.05), int(w * 0.95), int(h * 0.95)))
    fixed = make_cohesive_photo(inner, b_and_w=True)
    fixed.save(p_butler)
    print("[+] Normalized butler_male_50s.png (Silver gelatin butler portrait)")

# 5. Fix businessman_male_50s: Crop out the bottom-right AI watermark, convert to authentic vintage monochrome
p_biz = os.path.join(suspects_dir, "businessman_male_50s.png")
if os.path.exists(p_biz):
    orig = Image.open(p_biz)
    w, h = orig.size
    # Exclude bottom 10% where watermark was
    inner = orig.crop((int(w * 0.05), 0, int(w * 0.95), int(h * 0.90)))
    fixed = make_cohesive_photo(inner, b_and_w=True)
    fixed.save(p_biz)
    print("[+] Normalized businessman_male_50s.png (No watermark, matched tone)")

# 6. Fix female_30s: Crop interior face and bust, remove placard and fake outer border
p_female = os.path.join(suspects_dir, "female_30s.png")
if os.path.exists(p_female):
    orig = Image.open(p_female)
    w, h = orig.size
    inner = orig.crop((int(w * 0.22), int(h * 0.12), int(w * 0.78), int(h * 0.68)))
    fixed = make_cohesive_photo(inner, b_and_w=True)
    fixed.save(p_female)
    print("[+] Normalized female_30s.png (Cropped interior portrait)")

# 7. Fix young_male_20s: Crop interior face and bust, remove placard
p_male = os.path.join(suspects_dir, "young_male_20s.png")
if os.path.exists(p_male):
    orig = Image.open(p_male)
    w, h = orig.size
    inner = orig.crop((int(w * 0.18), int(h * 0.10), int(w * 0.82), int(h * 0.72)))
    fixed = make_cohesive_photo(inner, b_and_w=True)
    fixed.save(p_male)
    print("[+] Normalized young_male_20s.png (Cropped interior portrait)")

print("\n=== TẤT CẢ 7 ASSET ĐÃ ĐỒNG NHẤT 100% PHONG CÁCH NOIR 1990s! ===")
