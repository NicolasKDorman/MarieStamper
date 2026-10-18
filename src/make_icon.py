"""Draws stamper.ico: a red stamp-style badge that says STAMPER."""
import sys
from PIL import Image, ImageDraw, ImageFont

out = sys.argv[1]
S = 512
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.rounded_rectangle((8, 8, S - 8, S - 8), radius=80, fill=(255, 250, 235, 255), outline=(180, 30, 30, 255), width=24)
d.rounded_rectangle((52, 52, S - 52, S - 52), radius=50, outline=(180, 30, 30, 255), width=8)
f = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 92)
l, t, r, b = d.textbbox((0, 0), "STAMPER", font=f)
d.text(((S - (r - l)) / 2 - l, 150 - t), "STAMPER", font=f, fill=(180, 30, 30, 255))
f2 = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 70)
txt = "10/3/26"
l, t, r, b = d.textbbox((0, 0), txt, font=f2)
d.text(((S - (r - l)) / 2 - l, 300 - t), txt, font=f2, fill="white", stroke_width=7, stroke_fill="black")
im.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
