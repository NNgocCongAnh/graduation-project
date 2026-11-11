import os
import math
import random
from PIL import Image, ImageDraw, ImageFilter

script_dir = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.normpath(os.path.join(script_dir, "..", "Textures", "NoirUI"))
os.makedirs(out_dir, exist_ok=True)
random.seed(1337)

def create_true_perspective_trapezoid_dossier():
    """
    Creates a photorealistic Manila Dossier Folder lying flat in 2.5D perspective.
    Features:
    - 75% Top-to-Bottom perspective trapezoid convergence
    - Visible bottom paper bundle rim (creamy forensic sheets)
    - Distressed kraft paper fiber noise
    - Metal paperclip & index tab
    - Deep ambient drop shadow on desk
    """
    w, h = 420, 220
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    
    # 1. Soft Desk Drop Shadow
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    # Shadow polygon following trapezoid cast
    shadow_poly = [
        (45, 30),
        (w - 35, 30),
        (w - 8, h - 8),
        (18, h - 8)
    ]
    s_draw.polygon(shadow_poly, fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=8))
    img.paste(shadow, (4, 8), shadow)
    
    # 2. Page Stack / Fore-edge Rim (Interior papers visible underneath cover)
    pages_poly = [
        (25, h - 38),
        (w - 25, h - 38),
        (w - 20, h - 22),
        (30, h - 22)
    ]
    draw = ImageDraw.Draw(img)
    draw.polygon(pages_poly, fill=(232, 224, 204, 255))
    # Striated page lines
    for ly in range(h - 36, h - 22, 3):
        draw.line([(28, ly), (w - 22, ly)], fill=(195, 185, 165, 200), width=1)
    
    # 3. Top Tab
    tab_poly = [
        (240, 14),
        (340, 14),
        (350, 28),
        (230, 28)
    ]
    draw.polygon(tab_poly, fill=(196, 158, 108, 255), outline=(150, 115, 75, 255), width=2)
    
    # 4. Main Manila Cover (Perspective Trapezoid)
    # Top edge is narrower than bottom edge
    cover_poly = [
        (56, 26),        # Top-left
        (w - 56, 26),    # Top-right
        (w - 24, h - 36),# Bottom-right
        (24, h - 36)     # Bottom-left
    ]
    # Draw base kraft folder
    draw.polygon(cover_poly, fill=(210, 172, 118, 255), outline=(160, 125, 80, 255), width=2)
    
    # Paper fiber texture & shading gradient
    cover_mask = Image.new("L", (w, h), 0)
    cm_draw = ImageDraw.Draw(cover_mask)
    cm_draw.polygon(cover_poly, fill=255)
    
    cover_tex = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ct_pix = cover_tex.load()
    for y in range(24, h - 34):
        for x in range(20, w - 20):
            if cover_mask.getpixel((x, y)) > 0:
                # Vertical perspective shading: top is slightly darker (ambient falloff)
                v_grad = int(12 * (y / h))
                noise = random.randint(-8, 8)
                r = min(255, max(0, 208 + v_grad + noise))
                g = min(255, max(0, 170 + v_grad + noise))
                b = min(255, max(0, 116 + v_grad + noise))
                ct_pix[x, y] = (r, g, b, 255)
    img.paste(cover_tex, (0, 0), cover_mask)
    
    # 5. Spine Crease on Left
    draw.line([(56, 26), (24, h - 36)], fill=(140, 105, 65, 255), width=3)
    draw.line([(60, 26), (28, h - 36)], fill=(235, 200, 150, 160), width=2)
    
    # 6. Brass Paperclip on top-left
    clip = Image.new("RGBA", (40, 50), (0, 0, 0, 0))
    cl_draw = ImageDraw.Draw(clip)
    cl_draw.rounded_rectangle([6, 2, 22, 44], radius=6, outline=(215, 185, 95, 255), width=3)
    cl_draw.line([(10, 16), (10, 36)], fill=(160, 130, 60, 255), width=2)
    clip = clip.rotate(-12, expand=True)
    img.paste(clip, (75, 12), clip)
    
    # 7. Red Rubber Stamp "CONFIDENTIAL // CASE DOSSIER" (Skewed in perspective)
    stamp = Image.new("RGBA", (180, 70), (0, 0, 0, 0))
    st_draw = ImageDraw.Draw(stamp)
    st_draw.rounded_rectangle([4, 4, 174, 64], radius=4, outline=(195, 35, 35, 220), width=3)
    st_draw.rectangle([8, 8, 170, 60], outline=(195, 35, 35, 150), width=1)
    st_draw.text((14, 16), "CONFIDENTIAL", fill=(195, 35, 35, 240))
    st_draw.text((16, 38), "CASE #2026-001", fill=(195, 35, 35, 210))
    stamp = stamp.rotate(6, expand=True, resample=Image.BICUBIC)
    img.paste(stamp, (180, 75), stamp)
    
    out_path = os.path.join(out_dir, "manila_dossier_trapezoid.png")
    img.save(out_path)
    print(f"[+] Successfully generated: {out_path}")


def create_true_perspective_trapezoid_warrant():
    """
    Creates a photorealistic Crimson Docket Binder (Arrest Warrant) in 2.5D perspective.
    Features:
    - True perspective trapezoid cover (72% top width vs bottom width)
    - Heavy leather binder thickness rim with exposed warrant sheets
    - Embossed gold foil corner metal brackets
    - Gold double-ruled perspective border
    - Official Police Department Red/Gold Seal
    - Deep realistic contact shadow on mahogany desk
    """
    w, h = 440, 220
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    
    # 1. Heavy Contact & Drop Shadow
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    shadow_poly = [
        (52, 28),
        (w - 40, 28),
        (w - 10, h - 8),
        (20, h - 8)
    ]
    s_draw.polygon(shadow_poly, fill=(0, 0, 0, 180))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=9))
    img.paste(shadow, (6, 10), shadow)
    
    # 2. Bottom Document Bundle Thickness (Cream/parchment pages showing)
    pages_poly = [
        (26, h - 38),
        (w - 26, h - 38),
        (w - 20, h - 20),
        (32, h - 20)
    ]
    draw = ImageDraw.Draw(img)
    draw.polygon(pages_poly, fill=(240, 235, 220, 255))
    # Striated document edges
    for ly in range(h - 36, h - 20, 3):
        draw.line([(30, ly), (w - 22, ly)], fill=(205, 195, 175, 220), width=1)
    
    # 3. Main Binder Cover (Deep Crimson Textured Leather in Perspective)
    cover_poly = [
        (58, 24),        # Top-left
        (w - 58, 24),    # Top-right
        (w - 24, h - 36),# Bottom-right
        (24, h - 36)     # Bottom-left
    ]
    draw.polygon(cover_poly, fill=(125, 20, 20, 255), outline=(75, 10, 10, 255), width=2)
    
    # Leather grain texture & lighting gradient
    cover_mask = Image.new("L", (w, h), 0)
    cm_draw = ImageDraw.Draw(cover_mask)
    cm_draw.polygon(cover_poly, fill=255)
    
    cover_tex = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ct_pix = cover_tex.load()
    for y in range(22, h - 34):
        for x in range(20, w - 20):
            if cover_mask.getpixel((x, y)) > 0:
                v_shading = int(14 * (y / h))
                noise = random.randint(-7, 7)
                r = min(255, max(0, 126 + v_shading + noise))
                g = min(255, max(0, 22 + v_shading//2 + noise//2))
                b = min(255, max(0, 22 + v_shading//2 + noise//2))
                ct_pix[x, y] = (r, g, b, 255)
    img.paste(cover_tex, (0, 0), cover_mask)
    
    # 4. Gold Embossed Perspective Border Line
    gold_poly = [
        (68, 34),
        (w - 68, 34),
        (w - 36, h - 46),
        (36, h - 46)
    ]
    draw.polygon(gold_poly, outline=(215, 175, 80, 200), width=2)
    
    # 5. Reinforced Brass/Gold Metal Corner Protectors (4 corners)
    # Top-Left Metal Corner
    draw.polygon([(58, 24), (88, 24), (58, 54)], fill=(225, 185, 85, 255), outline=(160, 125, 45, 255), width=1)
    # Top-Right Metal Corner
    draw.polygon([(w - 58, 24), (w - 88, 24), (w - 58, 54)], fill=(225, 185, 85, 255), outline=(160, 125, 45, 255), width=1)
    # Bottom-Left Metal Corner
    draw.polygon([(24, h - 36), (62, h - 36), (24, h - 74)], fill=(225, 185, 85, 255), outline=(160, 125, 45, 255), width=1)
    # Bottom-Right Metal Corner
    draw.polygon([(w - 24, h - 36), (w - 62, h - 36), (w - 24, h - 74)], fill=(225, 185, 85, 255), outline=(160, 125, 45, 255), width=1)
    
    # Corner metal rivets
    for rx, ry in [(66, 32), (w - 66, 32), (36, h - 48), (w - 36, h - 48)]:
        draw.ellipse([rx - 2, ry - 2, rx + 2, ry + 2], fill=(255, 240, 160, 255))
    
    # 6. Spine Binding on Left with Stitched Thread
    draw.line([(58, 24), (24, h - 36)], fill=(55, 8, 8, 255), width=4)
    draw.line([(64, 25), (30, h - 35)], fill=(175, 30, 30, 200), width=2)
    for i in range(8):
        sy = 38 + i * 18
        sx = int(58 - (34 * (sy - 24) / (h - 60)))
        draw.line([(sx + 2, sy), (sx + 8, sy)], fill=(225, 195, 120, 255), width=2)
    
    # 7. Red/Gold Foil Official Seal Stamp "ARREST WARRANT // Phenikaa PD"
    seal = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
    sl_draw = ImageDraw.Draw(seal)
    sl_draw.ellipse([6, 6, 134, 134], outline=(225, 45, 45, 220), width=3)
    sl_draw.ellipse([14, 14, 126, 126], outline=(215, 175, 80, 190), width=2)
    sl_draw.ellipse([24, 24, 116, 116], outline=(225, 45, 45, 170), width=1)
    sl_draw.text((26, 48), "ARREST", fill=(235, 45, 45, 240))
    sl_draw.text((22, 68), "WARRANT", fill=(235, 45, 45, 240))
    sl_draw.text((36, 88), "★ OFFICIAL ★", fill=(215, 175, 80, 230))
    seal = seal.rotate(8, expand=True, resample=Image.BICUBIC)
    img.paste(seal, (w - 175, 48), seal)
    
    out_path = os.path.join(out_dir, "arrest_warrant_trapezoid.png")
    img.save(out_path)
    print(f"[+] Successfully generated: {out_path}")


def create_true_perspective_trapezoid_autopsy():
    """
    Creates a photorealistic Slate-Navy Coroner's Autopsy Report Binder in 2.5D perspective.
    Features:
    - True perspective trapezoid (top width 74% of bottom)
    - Medical steel fastener bar at top
    - Forensic Henssge autopsy report sheets peeking from the bottom
    - Cross / Caduceus forensic emblem
    - Deep contact shadow on desk
    """
    w, h = 420, 220
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    
    # 1. Shadow
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    shadow_poly = [
        (48, 28),
        (w - 38, 28),
        (w - 8, h - 8),
        (18, h - 8)
    ]
    s_draw.polygon(shadow_poly, fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=8))
    img.paste(shadow, (4, 8), shadow)
    
    # 2. Forensic Sheets Rim
    pages_poly = [
        (25, h - 38),
        (w - 25, h - 38),
        (w - 18, h - 22),
        (30, h - 22)
    ]
    draw = ImageDraw.Draw(img)
    draw.polygon(pages_poly, fill=(235, 240, 245, 255))
    for ly in range(h - 36, h - 22, 3):
        draw.line([(28, ly), (w - 20, ly)], fill=(195, 205, 215, 200), width=1)
        
    # 3. Main Cover (Slate Navy Forensic Folder)
    cover_poly = [
        (56, 26),
        (w - 56, 26),
        (w - 24, h - 36),
        (24, h - 36)
    ]
    draw.polygon(cover_poly, fill=(35, 48, 62, 255), outline=(20, 30, 42, 255), width=2)
    
    cover_mask = Image.new("L", (w, h), 0)
    cm_draw = ImageDraw.Draw(cover_mask)
    cm_draw.polygon(cover_poly, fill=255)
    
    cover_tex = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ct_pix = cover_tex.load()
    for y in range(24, h - 34):
        for x in range(20, w - 20):
            if cover_mask.getpixel((x, y)) > 0:
                v_shading = int(12 * (y / h))
                noise = random.randint(-6, 6)
                r = min(255, max(0, 34 + v_shading + noise))
                g = min(255, max(0, 48 + v_shading + noise))
                b = min(255, max(0, 64 + v_shading + noise))
                ct_pix[x, y] = (r, g, b, 255)
    img.paste(cover_tex, (0, 0), cover_mask)
    
    # 4. Steel Medical Fastener Bar at top
    draw.rounded_rectangle([130, 18, 290, 36], radius=4, fill=(185, 195, 205, 255), outline=(130, 140, 150, 255), width=1)
    draw.ellipse([145, 23, 153, 31], fill=(90, 100, 110, 255))
    draw.ellipse([267, 23, 275, 31], fill=(90, 100, 110, 255))
    
    # 5. Silver Caduceus / Cross Forensic Emblem
    cross = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    c_draw = ImageDraw.Draw(cross)
    c_draw.rectangle([40, 15, 60, 85], fill=(215, 65, 65, 230))
    c_draw.rectangle([15, 40, 85, 60], fill=(215, 65, 65, 230))
    c_draw.ellipse([20, 20, 80, 80], outline=(220, 230, 240, 180), width=2)
    cross = cross.rotate(-5, expand=True)
    img.paste(cross, (w - 150, 60), cross)
    
    out_path = os.path.join(out_dir, "coroner_autopsy_folder.png")
    img.save(out_path)
    print(f"[+] Successfully generated: {out_path}")


if __name__ == "__main__":
    create_true_perspective_trapezoid_dossier()
    create_true_perspective_trapezoid_warrant()
    create_true_perspective_trapezoid_autopsy()
    print("[SUCCESS] All 3 diegetic depth perspective folders generated!")
