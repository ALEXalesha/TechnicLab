"""Схема компоновки сбоку: где кабина, где багажник, что их занимает. Сверху - как сейчас, снизу - предложение.
Запуск: python layout_sketch.py -> компоновка.png
"""
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "ядро"))
import os

from PIL import Image, ImageDraw, ImageFont

import car
import body

OUT = os.path.dirname(os.path.abspath(__file__))
S = 1.25
Z0, Z1, Y0 = -500, 520, -470
W, H = int((Z1 - Z0) * S), int(520 * S)

GROUP = {"58119.dat": ("батареи", (250, 250, 250)), "58123.dat": ("приёмники", (120, 170, 230)),
         "58121c01.dat": ("мотор XL", (150, 150, 150)), "99498.dat": ("серво", (150, 150, 150)),
         "v4.ldr": ("V8", (230, 120, 110)), "99499.dat": ("лебёдка", (150, 150, 150)),
         "4185a.dat": ("руль", (60, 60, 60)), "40344.dat": ("дверь", (60, 60, 60))}


def P(z, y):
    return ((z - Z0) * S, (y - Y0) * S)


def panel(title, boxes, zones, extra=None):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 17)
    fb = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 21)
    d.line([P(Z0, 0), P(Z1, 0)], fill=(120, 90, 60), width=3)
    for (z0, z1, y0, y1, name, col) in zones:
        d.rectangle([P(z0, y0), P(z1, y1)], fill=col)
        d.text(P(z0 + 6, y0 + 4), name, fill=(30, 30, 30), font=fb)
    for (b, name, col) in boxes:
        d.rectangle([P(b[0][2], b[0][1]), P(b[1][2], b[1][1])], fill=col, outline=(70, 70, 70), width=2)
        d.text(P(b[0][2] + 3, b[0][1] + 3), name, fill=(20, 20, 20), font=f)
    for z in (car.FRONT_Z, car.AXLE_Z):
        d.ellipse([P(z - 71, -142), P(z + 71, 0)], outline=(30, 30, 30), width=4)
    for item in extra or []:
        item(d, f)
    d.text((10, 8), title, fill=(0, 0, 0), font=fb)
    d.text((W - 150, 8), "перед <-", fill=(90, 90, 90), font=f)
    return img


def main():
    m = car.build()
    body.build_body(m)
    boxes = []
    for p in m.parts():
        if p.name in GROUP:
            name, col = GROUP[p.name]
            boxes.append((car._bbox(p), name, col))
        elif p.name == "32140.dat" and p.color == car.BLUE:
            boxes.append((car._bbox(p), "сиденье", (90, 120, 230)))
    now = panel("Сейчас: кабина и багажник заняты механикой", boxes,
                [(-200, 120, -411, -171, "кабина?", (225, 238, 255)), (120, 340, -411, -171, "багажник?", (225, 245, 225))])

    # предложение: сиденья вперёд к рулю, приёмники - за сиденья наверх, крыша кабины до стойки B,
    # багажник продлён назад на 6 модулей с полом и бортами, дверь на z=460
    new = []
    for b, name, col in boxes:
        if name == "сиденье":
            b = ((b[0][0], b[0][1], -70), (b[1][0], b[1][1], -30))
        elif name == "приёмники":
            b = ((b[0][0], -420, 20), (b[1][0], -340, 120))
        elif name == "дверь":
            b = ((b[0][0], b[0][1], b[0][2] + 120), (b[1][0], b[1][1], b[1][2] + 120))
        new.append((b, name, col))

    def roof(d, f):
        d.line([P(-200, -411), P(20, -411), P(20, -171)], fill=(0, 0, 0), width=5)      # крыша кабины и стойка B
        d.text(P(-190, -440), "крыша кабины + стойка B", fill=(0, 0, 0), font=f)
        d.line([P(290, -211), P(450, -211)], fill=(0, 120, 0), width=6)                 # пол багажника
        d.text(P(300, -240), "пол багажника", fill=(0, 100, 0), font=f)
        d.line([P(340, -411), P(460, -411)], fill=(0, 0, 0), width=3)
        d.text(P(-190, -150), "серво стоит между сиденьями (сбоку они накладываются)", fill=(60, 60, 60), font=f)
        d.text(P(120, -150), "батареи - стенка между кабиной и багажником", fill=(60, 60, 60), font=f)
    prop = panel("Предложение: сиденья у руля, приёмники за кабиной, багажник +6 модулей назад", new,
                 [(-200, 20, -411, -171, "кабина", (215, 230, 255)), (290, 460, -411, -211, "багажник (пустой)", (210, 245, 210))],
                 [roof])
    out = Image.new("RGB", (W, 2 * H + 10), (200, 200, 200))
    out.paste(now, (0, 0))
    out.paste(prop, (0, H + 10))
    p = os.path.join(OUT, "компоновка.png")
    out.save(p)
    print(p)


if __name__ == "__main__":
    main()
