"""Лист деталей с картинками (для сверки с Алексеем): каждая деталь отрисована LDView, рядом количество и название.
Запуск: python bom_sheet.py -> багги/детали-шасси.png
"""
import collections
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

import car
import ldr
import render

import paths

OUT = paths.folder("багги")
CACHE = os.path.join(paths.CACHE, "parts_png")
COLOR_RU = {0: "чёрный", 71: "светло-серый", 72: "тёмно-серый", 19: "бежевый", 1: "синий", 4: "красный", 14: "жёлтый", 15: "белый"}
HIDDEN_ANY = ("Beam", "Axle ", "Pin", "Bush", "Cross Block", "Connector")   # внутри - цвет любой


def part_png(name, color):
    os.makedirs(CACHE, exist_ok=True)
    png = os.path.join(CACHE, "%s_%d.png" % (name.replace(".dat", ""), color))
    if not os.path.exists(png):
        tmp = png[:-4] + ".ldr"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("1 %d 0 0 0 1 0 0 0 1 0 0 0 1 %s\n" % (color, name))
        args = [render.LDVIEW, tmp, "-LDrawDir=" + render.LDRAW, "-SaveSnapshot=" + png, "-SaveWidth=220",
                "-SaveHeight=160", "-SaveActualSize=0", "-DefaultLatLong=30,45", "-BackgroundColor3=0xFFFFFF",
                "-AutoCrop=0", "-SaveAlpha=0"]
        subprocess.run(args, check=True, timeout=60, creationflags=0x08000000)
    return png


def sheet(parts, out_png, title):
    c = collections.Counter((p.name, p.color) for p in parts if p.name.endswith(".dat"))
    items = sorted(c.items(), key=lambda x: (ldr.title(x[0][0]), -x[1]))
    cols, cw, ch = 4, 370, 200
    rows = (len(items) + cols - 1) // cols
    img = Image.new("RGB", (cols * cw, rows * ch + 60), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 16)
    fb = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 22)
    d.text((12, 14), title, fill=(20, 20, 20), font=fb)
    for k, ((name, color), n) in enumerate(items):
        x, y = (k % cols) * cw, (k // cols) * ch + 60
        im = Image.open(part_png(name, color)).convert("RGB").resize((220, 160))
        img.paste(im, (x + 5, y))
        t = ldr.title(name)
        any_col = any(h in t for h in HIDDEN_ANY)
        d.text((x + 230, y + 10), "x%d" % n, fill=(200, 40, 40), font=fb)
        d.text((x + 230, y + 44), name.replace(".dat", ""), fill=(60, 60, 60), font=f)
        d.text((x + 230, y + 66), "цвет любой" if any_col else COLOR_RU.get(color, str(color)), fill=(60, 60, 60), font=f)
        d.text((x + 8, y + 160), t[:40], fill=(40, 40, 40), font=f)
        d.rectangle((x, y - 2, x + cw - 2, y + ch - 4), outline=(225, 225, 225))
    img.save(out_png)
    return out_png


if __name__ == "__main__":
    import body
    m = car.build()
    body.build_body(m)
    print(sheet(m.parts(), os.path.join(OUT, "детали-шасси.png"), "Вся машина: сколько деталей нужно (V4 - твой собранный, не считается)"))
