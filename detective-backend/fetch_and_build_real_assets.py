import os
import io
import urllib.request
import zipfile
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

base_dir = os.path.dirname(os.path.abspath(__file__))
unity_root = os.path.normpath(os.path.join(base_dir, "..", "Unity", "My project"))
target_dir = os.path.join(unity_root, "Assets", "Textures", "NoirUI")
backend_static_suspects = os.path.join(base_dir, "static", "assets", "suspects")
backend_static_evidences = os.path.join(base_dir, "static", "assets", "evidences")

os.makedirs(target_dir, exist_ok=True)
os.makedirs(backend_static_suspects, exist_ok=True)
os.makedirs(backend_static_evidences, exist_ok=True)

def fetch_ambientcg_color(asset_id: str) -> Image.Image:
    url = f"https://ambientcg.com/get?file={asset_id}_1K-JPG.zip"
    print(f"[*] Downloading CC0 Texture {asset_id} from ambientCG...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40) as resp:
        data = resp.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            if "Color" in name and name.endswith(".jpg"):
                with z.open(name) as f:
                    return Image.open(f).convert("RGBA")
    raise ValueError(f"Could not find Color map in {asset_id}")

print("=== GIAI ĐOẠN 1: TẢI TEXTURE GỐC TỪ AMBIENTCG (CC0 PUBLIC DOMAIN) ===")
cork_tex = fetch_ambientcg_color("Cork001")
wood_frame_tex = fetch_ambientcg_color("Wood016")
wood_desk_tex = fetch_ambientcg_color("Wood039")
paper_kraft_tex = fetch_ambientcg_color("Paper005")
paper_card_tex = fetch_ambientcg_color("Paper001")

# 1. Save Cork Texture (512x512 tileable)
cork_tex_resized = cork_tex.resize((512, 512), Image.Resampling.LANCZOS)
cork_tex_resized.save(os.path.join(target_dir, "cork_seamless.png"))
print("[+] Saved cork_seamless.png (Real PBR Cork001)")

# 2. Save Wood Frame Mahogany
wood_frame_resized = wood_frame_tex.resize((512, 512), Image.Resampling.LANCZOS)
# Tone it slightly warmer mahogany
r, g, b, a = wood_frame_resized.split()
r = r.point(lambda p: min(255, int(p * 1.15)))
g = g.point(lambda p: int(p * 0.90))
b = b.point(lambda p: int(p * 0.75))
mahogany_final = Image.merge("RGBA", (r, g, b, a))
mahogany_final.save(os.path.join(target_dir, "wood_frame_mahogany.png"))
print("[+] Saved wood_frame_mahogany.png (Real PBR Wood016)")

# 3. Save Desk Worn Wood
desk_wood_final = wood_desk_tex.resize((1024, 512), Image.Resampling.LANCZOS)
desk_wood_final.save(os.path.join(target_dir, "desk_surface_wood.png"))
print("[+] Saved desk_surface_wood.png (Real PBR Wood039)")

# 4. Realistic 3D Push-Pin with Optical Specular Highlight
def build_photoreal_pushpin():
    w, h = 128, 128
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Soft realistic shadow
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.ellipse([64, 66, 112, 98], fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=4))
    img.paste(shadow, (0, 0), shadow)

    draw = ImageDraw.Draw(img)
    # Brass needle tip
    draw.polygon([(64, 76), (62, 98), (66, 98)], fill=(195, 175, 115, 255))
    draw.polygon([(63, 76), (63, 98), (65, 98)], fill=(245, 230, 180, 255))

    # Translucent deep red pin head with sphere volume
    cx, cy, r = 60, 52, 28
    for i in range(r, 0, -1):
        ratio = i / r
        # Dark crimson outer rim to bright ruby center
        red = int(255 - 110 * ratio)
        green = int(45 - 35 * ratio)
        blue = int(45 - 35 * ratio)
        draw.ellipse([cx - i, cy - i, cx + i, cy + i], fill=(red, green, blue, 255))

    # Specular hot gleam
    gleam = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(gleam)
    g_draw.ellipse([46, 36, 62, 48], fill=(255, 240, 240, 220))
    g_draw.ellipse([50, 40, 58, 46], fill=(255, 255, 255, 255))
    gleam = gleam.filter(ImageFilter.GaussianBlur(radius=1.2))
    img.paste(gleam, (0, 0), gleam)

    img.save(os.path.join(target_dir, "pushpin_3d.png"))
    print("[+] Saved pushpin_3d.png (Specular 3D Pin)")

build_photoreal_pushpin()

# 5. Realistic Polaroid Card Paper Body (Real Paper001 texture + subtle age vignette)
def build_photoreal_card():
    w, h = 256, 310
    card_crop = paper_card_tex.crop((0, 0, w, h)).convert("RGBA")
    # Tone to slightly vintage warm off-white ivory
    r, g, b, a = card_crop.split()
    r = r.point(lambda p: min(255, int(p * 0.98)))
    g = g.point(lambda p: min(255, int(p * 0.96)))
    b = b.point(lambda p: min(255, int(p * 0.91)))
    card_base = Image.merge("RGBA", (r, g, b, a))

    draw = ImageDraw.Draw(card_base)
    # Subtle inner bevel border
    draw.rectangle([0, 0, w - 1, h - 1], outline=(195, 190, 178, 255), width=1)
    draw.rectangle([1, 1, w - 2, h - 2], outline=(255, 255, 255, 180), width=1)
    card_base.save(os.path.join(target_dir, "paper_card_bg.png"))
    print("[+] Saved paper_card_bg.png (Real Paper001 Texture)")

build_photoreal_card()

# 6. High-Fidelity Manila Dossier Folder (Constructed with Paper005 Kraft Cardboard)
def build_manila_dossier():
    w, h = 340, 160
    kraft = paper_kraft_tex.crop((50, 50, 50 + w, 50 + h)).convert("RGBA")
    
    # Perspective trapezoid mask
    mask = Image.new("L", (w, h), 0)
    m_draw = ImageDraw.Draw(mask)
    # Slight perspective trapezoid (top narrower than bottom)
    pts = [(16, 8), (w - 16, 8), (w - 4, h - 6), (4, h - 6)]
    m_draw.polygon(pts, fill=255)

    folder = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Drop shadow
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.polygon([(20, 16), (w - 10, 16), (w + 2, h + 2), (10, h + 2)], fill=(0, 0, 0, 170))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=6))
    folder.paste(shadow, (0, 0), shadow)

    folder.paste(kraft, (0, 0), mask)

    draw = ImageDraw.Draw(folder)
    # Highlight rim & folder seam
    draw.line([(16, 8), (w - 16, 8)], fill=(255, 240, 210, 200), width=2)
    draw.line([(16, 8), (4, h - 6)], fill=(120, 95, 60, 180), width=2)
    draw.line([(w - 16, 8), (w - 4, h - 6)], fill=(120, 95, 60, 180), width=2)

    # Red rubber stamp "CONFIDENTIAL"
    stamp = Image.new("RGBA", (140, 48), (0, 0, 0, 0))
    st_draw = ImageDraw.Draw(stamp)
    st_draw.rectangle([2, 2, 136, 44], outline=(180, 32, 32, 220), width=3)
    st_draw.rectangle([6, 6, 132, 40], outline=(180, 32, 32, 160), width=1)
    st_draw.text((18, 14), "CONFIDENTIAL", fill=(185, 35, 35, 230))
    stamp = stamp.rotate(4.5, expand=True, resample=Image.Resampling.BICUBIC)
    folder.paste(stamp, (w - 150, 45), stamp)

    folder.save(os.path.join(target_dir, "manila_dossier_trapezoid.png"))
    print("[+] Saved manila_dossier_trapezoid.png (Real Kraft Texture + Red Stamp)")

build_manila_dossier()

# 7. High-Fidelity Arrest Warrant Folder (Crimson + Brass Tabs + Red Wax Seal Stamp)
def build_arrest_warrant():
    w, h = 360, 160
    folder = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    # Shadow
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.polygon([(18, 16), (w - 8, 16), (w + 4, h + 4), (10, h + 4)], fill=(0, 0, 0, 180))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=6))
    folder.paste(shadow, (0, 0), shadow)

    # Crimson body from kraft texture tinted deep red
    crimson_tex = paper_kraft_tex.crop((10, 10, 10 + w, 10 + h)).convert("RGBA")
    r, g, b, a = crimson_tex.split()
    r = r.point(lambda p: min(255, int(p * 0.95)))
    g = g.point(lambda p: int(p * 0.22))
    b = b.point(lambda p: int(p * 0.22))
    crimson_tinted = Image.merge("RGBA", (r, g, b, a))

    mask = Image.new("L", (w, h), 0)
    m_draw = ImageDraw.Draw(mask)
    pts = [(16, 8), (w - 16, 8), (w - 4, h - 6), (4, h - 6)]
    m_draw.polygon(pts, fill=255)
    folder.paste(crimson_tinted, (0, 0), mask)

    draw = ImageDraw.Draw(folder)
    # Folder edge bevels
    draw.line([(16, 8), (w - 16, 8)], fill=(220, 80, 80, 220), width=2)
    # Left kraft spine band
    draw.polygon([(26, 8), (48, 8), (38, h - 6), (16, h - 6)], fill=(185, 150, 105, 230))
    # Brass corner brackets
    draw.polygon([(16, 8), (42, 8), (16, 32)], fill=(205, 170, 75, 255))
    draw.polygon([(w - 16, 8), (w - 42, 8), (w - 16, 32)], fill=(205, 170, 75, 255))

    # Round Red Warrant Stamp
    stamp = Image.new("RGBA", (110, 110), (0, 0, 0, 0))
    st_draw = ImageDraw.Draw(stamp)
    st_draw.ellipse([4, 4, 104, 104], outline=(220, 45, 45, 220), width=3)
    st_draw.ellipse([10, 10, 98, 98], outline=(220, 45, 45, 180), width=1)
    st_draw.text((22, 45), "WARRANT", fill=(225, 50, 50, 230))
    stamp = stamp.rotate(-8, expand=True, resample=Image.Resampling.BICUBIC)
    folder.paste(stamp, (w - 110, 30), stamp)

    folder.save(os.path.join(target_dir, "arrest_warrant_trapezoid.png"))
    print("[+] Saved arrest_warrant_trapezoid.png (Crimson Leatherette + Brass Tabs)")

build_arrest_warrant()

# 8. High-Fidelity Coroner Autopsy Folder (Slate Blue + White Medical Cross Seal)
def build_coroner_folder():
    w, h = 340, 160
    folder = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    # Shadow
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.polygon([(18, 16), (w - 8, 16), (w + 4, h + 4), (10, h + 4)], fill=(0, 0, 0, 170))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=6))
    folder.paste(shadow, (0, 0), shadow)

    # Slate Blue Tint from Kraft
    slate_tex = paper_kraft_tex.crop((20, 20, 20 + w, 20 + h)).convert("RGBA")
    r, g, b, a = slate_tex.split()
    r = r.point(lambda p: int(p * 0.35))
    g = g.point(lambda p: int(p * 0.48))
    b = b.point(lambda p: min(255, int(p * 0.65)))
    slate_tinted = Image.merge("RGBA", (r, g, b, a))

    mask = Image.new("L", (w, h), 0)
    m_draw = ImageDraw.Draw(mask)
    pts = [(16, 8), (w - 16, 8), (w - 4, h - 6), (4, h - 6)]
    m_draw.polygon(pts, fill=255)
    folder.paste(slate_tinted, (0, 0), mask)

    draw = ImageDraw.Draw(folder)
    draw.line([(16, 8), (w - 16, 8)], fill=(130, 175, 215, 220), width=2)
    # Spine strip
    draw.polygon([(24, 8), (42, 8), (34, h - 6), (16, h - 6)], fill=(35, 52, 68, 240))

    # Red/White Coroner Seal
    seal = Image.new("RGBA", (90, 90), (0, 0, 0, 0))
    se_draw = ImageDraw.Draw(seal)
    se_draw.ellipse([4, 4, 84, 84], outline=(200, 50, 50, 230), width=3)
    se_draw.text((16, 36), "AUTOPSY", fill=(215, 55, 55, 230))
    seal = seal.rotate(6, expand=True, resample=Image.Resampling.BICUBIC)
    folder.paste(seal, (w - 100, 35), seal)

    folder.save(os.path.join(target_dir, "coroner_autopsy_folder.png"))
    print("[+] Saved coroner_autopsy_folder.png (Slate Medical Folder)")

build_coroner_folder()

# 9. Realistic Banker's Lamp (Glass Hood + Brass Neck + Base + Highlight)
def build_photoreal_bankers_lamp():
    w, h = 180, 280
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    # Soft Base Shadow
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.ellipse([30, 245, 150, 275], fill=(0, 0, 0, 180))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=5))
    img.paste(shadow, (0, 0), shadow)

    draw = ImageDraw.Draw(img)

    # Brass Stepped Circular Base
    draw.ellipse([36, 242, 144, 266], fill=(160, 128, 55, 255), outline=(100, 75, 28, 255), width=2)
    draw.ellipse([48, 234, 132, 252], fill=(195, 155, 72, 255), outline=(135, 105, 42, 255), width=1)
    draw.ellipse([62, 226, 118, 240], fill=(225, 185, 95, 255))

    # Curved Brass Stem / Gooseneck
    draw.line([(90, 230), (90, 85)], fill=(175, 135, 60, 255), width=10)
    draw.line([(88, 230), (88, 85)], fill=(235, 195, 110, 255), width=3) # Highlight spine
    # Pivot joint knuckle
    draw.ellipse([82, 80, 98, 96], fill=(195, 155, 72, 255), outline=(120, 90, 35, 255), width=2)

    # Emerald Green Glass Hood (Shade)
    shade_box = [15, 32, 165, 82]
    draw.rounded_rectangle(shade_box, radius=18, fill=(14, 92, 46, 255), outline=(8, 55, 26, 255), width=2)

    # Glass Specular Surface Gradient Reflection
    glint = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glint)
    g_draw.rounded_rectangle([25, 38, 155, 54], radius=8, fill=(35, 185, 95, 180))
    g_draw.ellipse([45, 40, 135, 48], fill=(180, 255, 215, 220))
    glint = glint.filter(ImageFilter.GaussianBlur(radius=1.5))
    img.paste(glint, (0, 0), glint)

    # Inner Gold Reflector Lip peek
    draw.line([(24, 80), (156, 80)], fill=(225, 185, 95, 255), width=3)

    # Brass Pull-Chain with beads & teardrop fob
    for y in range(85, 138, 6):
        draw.ellipse([114, y, 118, y + 4], fill=(215, 175, 85, 255))
    draw.ellipse([112, 138, 120, 148], fill=(235, 195, 95, 255), outline=(130, 95, 35, 255), width=1)

    img.save(os.path.join(target_dir, "bankers_lamp_prop.png"))
    print("[+] Saved bankers_lamp_prop.png (Glass Shader & Brass Stem)")

build_photoreal_bankers_lamp()

# 10. Realistic 90s Police Radio (Motorola Style with rubber grip, grooved speaker, backlit LCD)
def build_photoreal_radio():
    w, h = 280, 150
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    # Shadow
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([6, 8, w - 6, h - 4], radius=10, fill=(0, 0, 0, 170))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=5))
    img.paste(shadow, (0, 0), shadow)

    draw = ImageDraw.Draw(img)
    # Textured matte polymer chassis
    draw.rounded_rectangle([4, 12, w - 8, h - 8], radius=8, fill=(28, 32, 36, 255), outline=(48, 54, 60, 255), width=2)

    # Ribbed rubber side grip
    for i in range(5):
        draw.line([8, 28 + i * 18, 8, 38 + i * 18], fill=(14, 16, 18, 255), width=3)
        draw.line([w - 12, 28 + i * 18, w - 12, 38 + i * 18], fill=(14, 16, 18, 255), width=3)

    # Top stubby antenna & brass knurled volume dial
    draw.rounded_rectangle([24, 2, 42, 14], radius=3, fill=(18, 20, 22, 255))
    draw.rounded_rectangle([w - 62, 4, w - 38, 14], radius=3, fill=(185, 155, 80, 255), outline=(110, 85, 35, 255), width=1)

    # Recessed Backlit Matrix LCD Screen (Phosphor Green)
    draw.rounded_rectangle([24, 24, w - 24, 68], radius=4, fill=(12, 38, 20, 255), outline=(6, 22, 10, 255), width=2)
    # LCD Subtle glow
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow)
    g_draw.rounded_rectangle([28, 28, w - 28, 64], radius=3, fill=(45, 165, 75, 45))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=2))
    img.paste(glow, (0, 0), glow)

    # Heavy speaker grille slats
    for j in range(4):
        draw.rounded_rectangle([38, 80 + j * 12, w - 38, 86 + j * 12], radius=2, fill=(14, 16, 18, 255))

    img.save(os.path.join(target_dir, "police_radio_90s.png"))
    print("[+] Saved police_radio_90s.png (Tactical 90s Walkie-Talkie)")

build_photoreal_radio()

print("\n=== HOÀN TẤT: BỘ ASSET NOIR THỰC TẾ ĐÃ ĐƯỢC TỔNG HỢP VÀ GHI ĐÈ VÀO UNITY! ===")

