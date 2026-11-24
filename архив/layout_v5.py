"""Компоновка по рисунку Алексея 24.11 21:52: внизу по всей длине слой электроники (зелёное), сверху кабина (синее)
и багажник (красное) с углублением в слой электроники, задняя дверь наклонная. Размеры коробок - настоящие габариты
деталей из модели (LDU). Запуск: python layout_v5.py -> компоновка-v5.png
"""
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "ядро"))
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
S = 1.3
Z0, Z1, Y0 = -500, 520, -520
W, H = int((Z1 - Z0) * S), int(560 * S)
FRONT_Z, REAR_Z, WR = -300, 260, 71

LAYER = (-171, -281)            # слой электроники: от верха лонжеронов на 5,5 модулей вверх
ROOF = -451                     # крыша (сейчас -411): кабине нужен пол над слоем
# (z0, z1, y_top, y_bottom, подпись, цвет)
BOXES = [
    (-440, -360, -255, -181, "лебёдка L\n(лёжа)", (150, 150, 150)),
    (-330, -230, -301, -227, "V8", (230, 120, 110)),
    (-318, -248, -229, -161, "M", (150, 150, 150)),
    (-110, -10, -340, -201, "серво", (150, 150, 150)),
    (-60, 40, -291, -211, "приёмники\n(по бокам)", (120, 170, 230)),
    (-3, 123, -281, -161, "XL", (150, 150, 150)),
    (140, 300, -261, -181, "батарея 1 (лёжа)", (250, 250, 250)),
    (140, 300, -341, -261, "батарея 2 (лёжа)", (250, 250, 250)),
]


def P(z, y):
    return ((z - Z0) * S, (y - Y0) * S)


def main():
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 16)
    fb = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 20)
    d.line([P(Z0, 0), P(Z1, 0)], fill=(120, 90, 60), width=3)
    # зоны
    d.rectangle([P(-470, LAYER[1]), P(470, LAYER[0])], fill=(220, 245, 200))                 # электроника
    d.rectangle([P(-200, ROOF), P(140, LAYER[1])], fill=(215, 228, 255))                     # кабина
    d.polygon([P(140, ROOF), P(300, ROOF), P(460, LAYER[1]), P(140, LAYER[1])], fill=(255, 220, 220))   # багажник
    d.rectangle([P(310, LAYER[1]), P(450, LAYER[0] - 10)], fill=(255, 190, 190), outline=(200, 0, 0), width=3)
    d.text(P(318, -275), "углубление\n(закрытое)", fill=(160, 0, 0), font=f)
    d.rectangle([P(-470, -321), P(-200, LAYER[1])], fill=(235, 235, 235))                    # капот
    for (z0, z1, yt, yb, name, col) in BOXES:
        d.rectangle([P(z0, yt), P(z1, yb)], fill=col, outline=(60, 60, 60), width=2)
    # сиденья, руль
    for z in (-100,):
        d.rectangle([P(z, -361), P(z + 20, -281)], fill=(70, 100, 220))
        d.rectangle([P(z - 60, -301), P(z + 20, -281)], fill=(70, 100, 220))
    d.text(P(-160, -385), "сиденья", fill=(40, 60, 160), font=f)
    d.ellipse([P(-185, -361), P(-175, -321)], fill=(50, 50, 50))
    for (z0, z1, yt, yb, name, col) in BOXES:                               # подписи поверх всего
        d.multiline_text(P(z0 + 3, yb - 40 if name == "серво" else yt + 2), name, fill=(20, 20, 20), font=f)
    # контур кузова
    d.line([P(-470, -321), P(-200, -321), P(-170, ROOF), P(300, ROOF), P(460, LAYER[1]), P(470, LAYER[0]),
            P(470, -151), P(-470, -151), P(-470, -321)], fill=(0, 0, 0), width=4)
    d.line([P(300, ROOF), P(460, LAYER[1])], fill=(200, 0, 0), width=7)
    d.text(P(360, -420), "дверь (наклонная)", fill=(200, 0, 0), font=fb)
    for z in (FRONT_Z, REAR_Z):
        d.ellipse([P(z - WR, -2 * WR), P(z + WR, 0)], outline=(30, 30, 30), width=4)
    d.text(P(-460, -500), "По твоему рисунку: внизу электроника, сверху кабина и багажник (перед слева)", fill=(0, 0, 0), font=fb)
    d.text(P(-460, -475), "Крыша выше на 2 модуля (-451 вместо -411): кабине нужен пол над слоем электроники",
           fill=(60, 60, 60), font=f)
    d.text(P(-200, -305), "кабина", fill=(30, 50, 140), font=fb)
    d.text(P(150, -305), "багажник", fill=(160, 0, 0), font=fb)
    d.text(P(-460, -170), "слой электроники", fill=(40, 110, 30), font=fb)
    p = os.path.join(OUT, "компоновка-v5.png")
    img.save(p)
    print(p)


if __name__ == "__main__":
    main()
