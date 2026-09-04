#!/usr/bin/env python3
"""Generate per-reel 1080x1920 cover images + a contact sheet (all reels grid)."""
import json, os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = "/home/user/work"
COVER_DIR = os.path.join(BASE, "covers")
os.makedirs(COVER_DIR, exist_ok=True)

F_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
F_REG  = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"

def cover(img_path, line1, line2, rid, out_path, W=1080, H=1920):
    im = Image.open(img_path).convert("RGB")
    # cover-crop to 9:16
    tw, th = im.size
    target = W / H
    if tw / th > target:
        nw = int(th * target); x0 = (tw - nw) // 2
        im = im.crop((x0, 0, x0 + nw, th))
    else:
        nh = int(tw / target); y0 = (th - nh) // 2
        im = im.crop((0, y0, tw, y0 + nh))
    im = im.resize((W, H), Image.LANCZOS)

    # darken + vignette-ish gradient at bottom
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i in range(220):
        a = int(160 * (i / 220) ** 1.6)
        d.rectangle([0, H - 220 + i, W, H - 220 + i + 1], fill=(0, 0, 0, a))
    # top thin strip for brand
    for i in range(130):
        a = int(110 * (1 - i / 130) ** 1.4)
        d.rectangle([0, i, W, i + 1], fill=(0, 0, 0, a))
    im = Image.alpha_composite(im.convert("RGBA"), ov)

    d = ImageDraw.Draw(im)
    # brand
    fb = ImageFont.truetype(F_BOLD, 46)
    brand = "SHIVHOM"
    bb = d.textbbox((0, 0), brand, font=fb)
    d.text(((W - (bb[2] - bb[0])) / 2, 26), brand, font=fb, fill=(255, 220, 150, 235))

    # hook lines near bottom
    f1 = ImageFont.truetype(F_BOLD, 92 if len(line1) <= 18 else 76)
    f2 = ImageFont.truetype(F_BOLD, 66 if len(line2) <= 18 else 56)

    def draw_center(dr, text, font, cy, fill=(255, 255, 255, 255), stroke=(0, 0, 0, 210), sw=6):
        bb = dr.textbbox((0, 0), text, font=font, stroke_width=sw)
        tw_, th_ = bb[2] - bb[0], bb[3] - bb[1]
        dr.text(((W - tw_) / 2, cy - th_ / 2), text, font=font,
                fill=fill, stroke_fill=stroke, stroke_width=sw)

    draw_center(d, line1, f1, H - 320)
    draw_center(d, line2, f2, H - 320 + 150, fill=(255, 243, 208, 255))

    # trishul symbol (simple vector) next to brand
    cx = W / 2
    t = ImageDraw.Draw(im)
    t.line([(cx - 90, 108), (cx + 90, 108)], fill=(255, 200, 120, 200), width=4)
    for dx in (-40, 0, 40):
        t.line([(cx + dx, 108), (cx + dx, 52)], fill=(255, 200, 120, 200), width=5)
        t.polygon([(cx + dx - 26, 58), (cx + dx + 26, 58), (cx + dx, 24)],
                  outline=(255, 200, 120, 220), width=5)

    im.convert("RGB").save(out_path, quality=92)
    print("cover", rid)

def contact_sheet(spec):
    ids = [r["id"] for r in spec["reels"] if os.path.exists(os.path.join(BASE, "img", f"{r['img']}.jpg"))]
    cols, rows = 4, math.ceil(len(ids) / 4)
    cw, ch = 360, 640
    sheet = Image.new("RGB", (cols * cw + 60, rows * ch + 60), (12, 10, 18))
    d = ImageDraw.Draw(sheet)
    ft = ImageFont.truetype(F_BOLD, 30)
    d.text((30, 16), f"SHIVHOM — Reel Cover Grid ({len(ids)} reels)", font=ft, fill=(255, 230, 170))
    for i, rid in enumerate(ids):
        r = next(x for x in spec["reels"] if x["id"] == rid)
        c = os.path.join(COVER_DIR, f"cover_{rid:02d}.jpg")
        if not os.path.exists(c):
            cover(os.path.join(BASE, "img", f"{r['img']}.jpg"), r["cover1"], r["cover2"], rid, c)
        im = Image.open(c).resize((cw, ch), Image.LANCZOS)
        x = 30 + (i % cols) * cw
        y = 66 + (i // cols) * ch
        sheet.paste(im, (x, y))
        # id badge
        d.rectangle([x + 6, y + 6, x + 66, y + 46], fill=(0, 0, 0))
        d.text((x + 14, y + 8), f"{rid:02d}", font=ft, fill=(255, 200, 100))
    sheet.save(os.path.join(BASE, "cover_grid.jpg"), quality=90)
    print("grid saved:", os.path.join(BASE, "cover_grid.jpg"))

if __name__ == "__main__":
    with open(os.path.join(BASE, "reels.json")) as f:
        spec = json.load(f)
    contact_sheet(spec)
