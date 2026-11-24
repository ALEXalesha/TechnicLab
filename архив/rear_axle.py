"""Задний мост: рамка 5x7, дифференциал 28 з., полуоси, колёса 56x26, ведущая шестерня с кардана.
Оси: X - поперёк (вправо +), Y - вниз (земля y=0), Z - вдоль (назад +). 1 модуль = 20 LDU.
"""
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "ядро"))
import ldr

BLACK, YELLOW, LGREY, DGREY, RED, TAN, BLUE = 0, 14, 71, 72, 4, 19, 1
R_WHEEL = 71          # радиус шины 56x26
AX_Y = -R_WHEEL       # высота осей колёс
REAR_Z = 180          # задний мост (база 18 модулей)
TRACK_X = 160         # середина колеса от оси машины


def build(z0=REAR_Z, name="rear_axle.ldr"):
    m = ldr.Model(name)
    y = AX_Y
    m.step("Рамка моста и дифференциал")
    m.add("64179.dat", LGREY, (0, y, z0))
    m.add("62821.dat", DGREY, (0, y, z0), ldr.ry(90))
    m.step("Полуоси")
    for s in (1, -1):
        m.add("3707.dat", BLACK, (s * 100, y, z0))
        m.add("3713.dat", LGREY, (s * 60, y, z0), ldr.ry(90))
    m.step("Ведущая шестерня")
    m.add("32270.dat", BLACK, (0, y, z0 - 37))
    m.add("4519.dat", LGREY, (0, y, z0 - 37 - 30), ldr.ry(90))   # ось 3 через торцевое отверстие рамки
    m.step("Колёса")
    for s in (1, -1):
        rot = ldr.ry(90) if s > 0 else ldr.ry(-90)
        m.add("56145.dat", LGREY, (s * TRACK_X, y, z0), rot)
        m.add("55976.dat", BLACK, (s * TRACK_X, y, z0), rot)
    return m


if __name__ == "__main__":
    import os, sys
    import render
    import snaps
    out = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out, exist_ok=True)
    m = build()
    p = os.path.join(out, "rear_axle.ldr")
    ldr.write_mpd(p, m, [])
    parts = m.parts()
    pairs = snaps.connections(parts)
    linked = {i for ij in pairs for i in ij}
    for i, prt in enumerate(parts):
        print("%-12s %-50s %s" % (prt.name, ldr.title(prt.name)[:50], "ok" if i in linked else "НЕ ДЕРЖИТСЯ"))
    if "--img" in sys.argv:
        render.collage(p, os.path.join(out, "rear_axle.png"))
