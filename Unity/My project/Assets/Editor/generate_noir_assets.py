import os
import math
import random
from PIL import Image, ImageDraw, ImageFilter

script_dir = os.path.dirname(os.path.abspath(__file__))
# Target: Assets/Textures/NoirUI
out_dir = os.path.normpath(os.path.join(script_dir, "..", "Textures", "NoirUI"))
os.makedirs(out_dir, exist_ok=True)
random.seed(42)

# 1. Seamless Cork Texture (512x512)
def make_cork():
    w, h = 512, 512
    img = Image.new("RGB", (w, h), (160, 110, 68))
    pix = img.load()
    for y in range(h):
        for x in range(w):
            base = 160 + int(18 * math.sin(x * 0.05) * math.cos(y * 0.05))
            noise = random.randint(-18, 18)
            r = min(255, max(0, base + noise))
            g = min(255, max(0, int(r * 0.68) + random.randint(-10, 10)))
            b = min(255, max(0, int(r * 0.42) + random.randint(-8, 8)))
            pix[x, y] = (r, g, b)
    draw = ImageDraw.Draw(img)
    # Add cork flecks
    for _ in range(800):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        rw = random.randint(2, 7)
        rh = random.randint(2, 5)
        if random.random() < 0.65:
            c = (random.randint(70, 105), random.randint(45, 70), random.randint(25, 45))
        else:
            c = (random.randint(190, 225), random.randint(145, 175), random.randint(95, 125))
        draw.ellipse([x, y, x + rw, y + rh], fill=c)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.7))
    img.save(os.path.join(out_dir, "cork_seamless.png"))
    print("cork_seamless.png generated")

# 2. Mahogany Wood Grain (512x512)
def make_wood():
    w, h = 512, 512
    img = Image.new("RGB", (w, h), (62, 32, 18))
    pix = img.load()
    for y in range(h):
        for x in range(w):
            grain = int(14 * math.sin(y * 0.08 + 2 * math.sin(x * 0.01)))
            noise = random.randint(-8, 8)
            r = min(255, max(0, 62 + grain + noise))
            g = min(255, max(0, int(r * 0.52)))
            b = min(255, max(0, int(r * 0.30)))
            pix[x, y] = (r, g, b)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    img.save(os.path.join(out_dir, "wood_frame_mahogany.png"))
    print("wood_frame_mahogany.png generated")

# 3. 3D Glossy Push-Pin (128x128 RGBA)
def make_pushpin():
    w, h = 128, 128
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Drop shadow
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.ellipse([58, 62, 104, 94], fill=(0, 0, 0, 130))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=4))
    img.paste(shadow, (0, 0), shadow)
    
    draw = ImageDraw.Draw(img)
    # Brass needle tip peek
    draw.polygon([(64, 76), (62, 92), (66, 92)], fill=(180, 160, 100, 220))
    # Red Pin Head base
    cx, cy, r = 60, 52, 28
    for i in range(r, 0, -1):
        ratio = i / r
        red = int(245 - 90 * ratio)
        green = int(45 - 30 * ratio)
        blue = int(45 - 30 * ratio)
        draw.ellipse([cx - i, cy - i, cx + i, cy + i], fill=(red, green, blue, 255))
    # Specular 3D highlight (top-left gleam)
    hl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hl_draw = ImageDraw.Draw(hl)
    hl_draw.ellipse([46, 36, 62, 48], fill=(255, 230, 230, 210))
    hl_draw.ellipse([50, 40, 58, 46], fill=(255, 255, 255, 245))
    hl = hl.filter(ImageFilter.GaussianBlur(radius=1.5))
    img.paste(hl, (0, 0), hl)
    img.save(os.path.join(out_dir, "pushpin_3d.png"))
    print("pushpin_3d.png generated")

# 4. Polaroid Paper Card Background (256x310 RGBA)
def make_card_bg():
    w, h = 256, 310
    img = Image.new("RGBA", (w, h), (247, 245, 238, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w-1, h-1], outline=(218, 214, 202, 255), width=1)
    pix = img.load()
    for y in range(h):
        for x in range(w):
            n = random.randint(-4, 4)
            r, g, b, a = pix[x, y]
            pix[x, y] = (min(255, max(0, r + n)), min(255, max(0, g + n)), min(255, max(0, b + n)), 255)
    img.save(os.path.join(out_dir, "paper_card_bg.png"))
    print("paper_card_bg.png generated")

# 5. Soft Card Drop Shadow (270x324 RGBA)
def make_card_shadow():
    w, h = 270, 324
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([12, 14, w - 12, h - 10], radius=8, fill=(0, 0, 0, 140))
    img = img.filter(ImageFilter.GaussianBlur(radius=7))
    img.save(os.path.join(out_dir, "card_drop_shadow.png"))
    print("card_drop_shadow.png generated")

# 6. Arrest Warrant Folder (360x160 RGBA)
def make_arrest_folder():
    w, h = 360, 160
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Drop shadow
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([6, 8, w - 6, h - 4], radius=6, fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=5))
    img.paste(shadow, (0, 0), shadow)
    
    draw = ImageDraw.Draw(img)
    # Deep red folder base
    draw.rounded_rectangle([4, 4, w - 8, h - 8], radius=6, fill=(128, 26, 26, 255), outline=(78, 14, 14, 255), width=2)
    # Kraft paper accent stripe on left
    draw.rectangle([12, 10, 26, h - 14], fill=(188, 154, 108, 255))
    # Brass corner tabs
    draw.polygon([(4, 4), (28, 4), (4, 28)], fill=(195, 160, 75, 255))
    draw.polygon([(w - 8, 4), (w - 32, 4), (w - 8, 28)], fill=(195, 160, 75, 255))
    # Distressed Red Rubber Stamp Circle
    stamp = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    st_draw = ImageDraw.Draw(stamp)
    st_draw.ellipse([6, 6, 94, 94], outline=(215, 45, 45, 210), width=3)
    st_draw.ellipse([14, 14, 86, 86], outline=(215, 45, 45, 180), width=1)
    st_draw.text((18, 40), "WARRANT", fill=(215, 45, 45, 230))
    stamp = stamp.rotate(14, expand=True, resample=Image.BICUBIC)
    img.paste(stamp, (220, 25), stamp)
    img.save(os.path.join(out_dir, "arrest_warrant_folder.png"))
    print("arrest_warrant_folder.png generated")

# 7. 90s Police Walkie Talkie (280x150 RGBA)
def make_walkie_talkie():
    w, h = 280, 150
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Shadow
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([6, 8, w - 6, h - 4], radius=10, fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=5))
    img.paste(shadow, (0, 0), shadow)
    
    draw = ImageDraw.Draw(img)
    # Radio Body (Matte dark composite)
    draw.rounded_rectangle([4, 12, w - 8, h - 8], radius=8, fill=(34, 38, 42, 255), outline=(55, 60, 66, 255), width=2)
    # Side rubber grip ridges
    for i in range(5):
        draw.line([10, 28 + i * 18, 10, 38 + i * 18], fill=(22, 24, 26, 255), width=3)
        draw.line([w - 14, 28 + i * 18, w - 14, 38 + i * 18], fill=(22, 24, 26, 255), width=3)
    # Antenna stub on top left
    draw.rounded_rectangle([24, 2, 40, 14], radius=3, fill=(20, 22, 24, 255))
    # Volume dial on top right
    draw.rounded_rectangle([w - 60, 4, w - 38, 14], radius=3, fill=(160, 140, 75, 255))
    # Backlit LCD Screen
    draw.rounded_rectangle([26, 24, w - 26, 68], radius=4, fill=(14, 42, 22, 255), outline=(8, 26, 14, 255), width=2)
    # Speaker grille slats
    for j in range(4):
        draw.rounded_rectangle([40, 80 + j * 12, w - 40, 86 + j * 12], radius=2, fill=(18, 20, 22, 255))
    img.save(os.path.join(out_dir, "police_radio_90s.png"))
    print("police_radio_90s.png generated")

# 8. Banker's Lamp Prop (150x260 RGBA)
def make_bankers_lamp():
    w, h = 150, 260
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Shadow under base
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.ellipse([25, 230, 125, 255], fill=(0, 0, 0, 140))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=4))
    img.paste(shadow, (0, 0), shadow)
    
    # Stepped Brass Base
    draw.ellipse([30, 226, 120, 248], fill=(175, 138, 62, 255), outline=(135, 102, 42, 255), width=2)
    draw.ellipse([45, 218, 105, 234], fill=(195, 155, 75, 255))
    # Curved Brass Stem
    draw.line([(75, 220), (75, 80)], fill=(185, 145, 68, 255), width=8)
    draw.line([(70, 85), (80, 85)], fill=(215, 175, 95, 255), width=4)
    # Green Glass Shade (Hood)
    draw.rounded_rectangle([15, 30, 135, 78], radius=16, fill=(16, 105, 52, 255), outline=(10, 68, 32, 255), width=2)
    draw.ellipse([28, 36, 122, 48], fill=(32, 175, 88, 170))
    draw.ellipse([42, 38, 108, 44], fill=(180, 245, 205, 200))
    # Brass pull chain with ball
    draw.line([(95, 78), (95, 125)], fill=(185, 145, 68, 255), width=2)
    draw.ellipse([92, 124, 98, 130], fill=(215, 175, 95, 255))
    img.save(os.path.join(out_dir, "bankers_lamp_prop.png"))
    print("bankers_lamp_prop.png generated")

# 9. Soft Radial Atmospheric Light (512x512 RGBA)
def make_soft_light():
    w, h = 512, 512
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pix = img.load()
    cx, cy, max_r = 256, 256, 250
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy)
            if d < max_r:
                t = 1.0 - (d / max_r)
                # Smooth quadratic falloff
                alpha = int(75 * (t ** 2))
                pix[x, y] = (255, 225, 155, alpha)
    img.save(os.path.join(out_dir, "soft_radial_light.png"))
    print("soft_radial_light.png generated")

if __name__ == "__main__":
    make_cork()
    make_wood()
    make_pushpin()
    make_card_bg()
    make_card_shadow()
    make_arrest_folder()
    make_walkie_talkie()
    make_bankers_lamp()
    make_soft_light()
    print("All 9 Noir UI assets successfully created!")

