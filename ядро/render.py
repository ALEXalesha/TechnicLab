"""Картинки модели через LDView (без окна) и коллаж из нескольких ракурсов."""
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

LDVIEW = os.environ.get("LDVIEW", r"C:\Users\User\AppData\Local\LPub3D\3rdParty\ldview-4.5\bin\LDView64.exe")
LDRAW = os.environ.get("LDRAWDIR", r"C:\DevCache\lego\ldraw")
VIEWS = {"спереди-слева": (25, -45), "сзади-справа": (25, 135), "сбоку": (0, 90), "сверху": (89, 0),
         "спереди": (0, 0), "снизу": (-60, 30)}


def snap(ldr_path, png, lat, lon, w=640, h=480):
    args = [LDVIEW, ldr_path, "-LDrawDir=" + LDRAW, "-SaveSnapshot=" + png, "-SaveWidth=%d" % w,
            "-SaveHeight=%d" % h, "-SaveActualSize=0", "-DefaultLatLong=%d,%d" % (lat, lon),
            "-BackgroundColor3=0xF4F4F4", "-AutoCrop=0", "-SaveAlpha=0", "-ShowHighlightLines=1"]
    subprocess.run(args, check=True, timeout=120, creationflags=0x08000000)


def collage(ldr_path, out_png, views=None, w=560, h=420):
    views = views or VIEWS
    tmp = []
    for name, (lat, lon) in views.items():
        p = out_png[:-4] + "_" + str(len(tmp)) + ".png"
        snap(ldr_path, p, lat, lon, w, h)
        tmp.append((name, p))
    cols = 3
    rows = (len(tmp) + cols - 1) // cols
    img = Image.new("RGB", (cols * w, rows * h), (244, 244, 244))
    dr = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 18)
    except OSError:
        font = None
    for k, (name, p) in enumerate(tmp):
        im = Image.open(p).convert("RGB")
        img.paste(im, ((k % cols) * w, (k // cols) * h))
        dr.text(((k % cols) * w + 8, (k // cols) * h + 6), name, fill=(40, 40, 40), font=font)
        os.replace(p, p)  # оставить для крупного просмотра
    img.save(out_png)
    return out_png
