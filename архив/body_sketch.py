"""Эскиз кузова сбоку поверх настоящего шасси (габариты деталей в проекции y-z), для согласования пропорций.
Запуск: python body_sketch.py -> кузов-эскиз.png
"""
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "ядро"))
import math
import os

from PIL import Image, ImageDraw, ImageFont

import car

OUT = os.path.dirname(os.path.abspath(__file__))
S = 1.6            # пикселей на LDU
Z0, Y0 = -520, -520  # левый верхний угол листа в LDU
W, H = int(1060 * S), int(560 * S)

# контур кузова (z, y): нос слева (z<0). Решение Claude - на согласование.
ROOF_Y = -431
BODY = [(-455, -150), (-460, -250), (-450, -345), (-200, -370), (-90, ROOF_Y), (400, ROOF_Y), (425, -410),
        (430, -230), (435, -150)]
WINDOWS = [[(-180, -380), (-100, -422), (90, -422), (90, -380)],
           [(110, -380), (110, -422), (390, -422), (405, -380)]]
HINGE = (420, -411)            # петля двери багажника
ACT_B, ACT_E = (220, -311), (420, -331)   # актуатор: основание на блоке 2, конец на двери (закрыта)


def P(z, y):
    return ((z - Z0) * S, (y - Y0) * S)


def main():
    m = car.build()
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 18)
    fb = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 22)
    # земля и сетка модулей
    d.line([P(Z0, 0), P(Z0 + 1060, 0)], fill=(120, 90, 60), width=3)
    for z in range(-500, 541, 100):
        d.line([P(z, 0), P(z, 8)], fill=(150, 150, 150))
        d.text(P(z - 15, 12), "%d" % (z // 20), fill=(150, 150, 150), font=f)
    # детали шасси: габарит в проекции
    for p in m.parts():
        b = car._bbox(p)
        if not b or p.name in ("55976.dat", "56145.dat"):
            continue
        d.rectangle([P(b[0][2], b[0][1]), P(b[1][2], b[1][1])], fill=(205, 210, 218), outline=(150, 156, 166))
    for z in (car.FRONT_Z, car.AXLE_Z):
        d.ellipse([P(z - 71, -142), P(z + 71, 0)], fill=(40, 40, 40))
        d.ellipse([P(z - 38, -109), P(z + 38, -33)], fill=(200, 200, 200))
    # кузов
    d.line([P(*q) for q in BODY], fill=(20, 20, 20), width=5)
    for z in (car.FRONT_Z, car.AXLE_Z):          # арки
        a = [P(z + 88 * math.cos(t), -71 - 88 * math.sin(t)) for t in [i * math.pi / 24 for i in range(25)]]
        d.line(a, fill=(240, 190, 0), width=7)
    for w_ in WINDOWS:
        d.polygon([P(*q) for q in w_], outline=(60, 120, 200), fill=(215, 232, 250))
    # дверь багажника и актуатор (закрыто и открыто на 95°)
    d.ellipse([P(HINGE[0] - 6, HINGE[1] - 6), P(HINGE[0] + 6, HINGE[1] + 6)], fill=(200, 0, 0))
    a = math.radians(95)
    dz, dy = 200 * math.sin(a), 200 * math.cos(a)
    d.line([P(*HINGE), P(HINGE[0] + dz, HINGE[1] + dy)], fill=(200, 0, 0), width=3)
    e2 = (HINGE[0] + 80 * math.sin(a), HINGE[1] + 80 * math.cos(a))
    d.line([P(*ACT_B), P(*ACT_E)], fill=(0, 140, 60), width=6)
    d.line([P(*ACT_B), P(*e2)], fill=(0, 140, 60), width=2)
    d.text(P(-500, -505), "Кузов: эскиз сбоку на настоящем шасси (серое - детали, клетка = 5 модулей)", fill=(0, 0, 0), font=fb)
    d.text(P(-500, -480), "Длина %d мод. (%.0f см), высота %d мод. (%.0f см), база %d мод., свесы: перед %d, зад %d" % (
        (435 + 460) // 20, (435 + 460) * 0.04, -ROOF_Y // 20, -ROOF_Y * 0.04, (car.AXLE_Z - car.FRONT_Z) // 20,
        (car.FRONT_Z + 460) // 20, (435 - car.AXLE_Z) // 20), fill=(40, 40, 40), font=f)
    d.text(P(200, -500), "красное - дверь: закрыта и открыта на 95°", fill=(200, 0, 0), font=f)
    d.text(P(200, -478), "зелёное - актуатор с мотором M", fill=(0, 140, 60), font=f)
    out = os.path.join(OUT, "кузов-эскиз.png")
    img.save(out)
    print(out)


if __name__ == "__main__":
    main()
