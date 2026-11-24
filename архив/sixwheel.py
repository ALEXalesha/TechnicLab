"""6x6 с танковым разворотом (Алексей 24.11: «Начни сейчас и попробуй сделать полностью»; направление - проходимость).
Каждый борт: 3 колеса, цепочка из 7 шестерён 24з. (шаг 3 модуля) между двумя рядами кирпичей 1x16 (x ±70 и ±110),
концы - балки 5 снаружи и внутри. Левый борт крутит XL, правый - L: мотор лежит поперёк, сверху 24з. на его оси
входит в цепочку борта. Руль не нужен: поворот - разной скоростью бортов (пульт 8885/8879: левый рычаг - левый борт).
Оси как в car.py: X вправо, Y вниз (земля 0), Z назад. Запуск: python sixwheel.py
"""
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "ядро"))
import car
import ldr
from car import BLACK, LGREY, DGREY, BLUE, YELLOW, beam, brick, axle, gear

AXY = -71                    # оси колёс и цепочек
ZW = (-180, 0, 180)          # оси колёс (между шинами 38 LDU)
ZG = tuple(range(-180, 181, 60))   # шестерни цепочки
WX = 170                     # середина колеса
MY = AXY - 60                # оси моторов: 24з. над шестернёй цепочки
MZ = {-1: -60, 1: 60}        # мотор левого борта (XL) и правого (L) по Z


def side(m, s):
    """Борт s (-1 левый, 1 правый): два ряда кирпичей, концы, цепочка 24з., оси колёс и паразиток, колёса."""
    name = "левый" if s < 0 else "правый"
    m.sub = "Борт " + name
    m.step("Борт %s: два ряда кирпичей 1x16" % name)
    brick(m, 15, BLACK, (s * 70, AXY, 0), "z")                     # внутренний ряд: дырки z -140..140
    brick(m, 15, BLACK, (s * 110, AXY, 0), "z")                    # наружный ряд
    m.step("Концы борта: балки 5 изнутри и снаружи")
    for e in (-1, 1):
        beam(m, 5, BLACK, (s * 50, AXY, e * 140), "z", "x")        # дырки z e*100 .. e*180
        beam(m, 5, BLACK, (s * 130, AXY, e * 140), "z", "x")
        for z in (e * 100, e * 140):
            m.add("2780.dat", BLACK, (s * 60, AXY, z))
            m.add("2780.dat", BLACK, (s * 120, AXY, z))
    m.step("Цепочка шестерён 24з. и оси")
    for z in ZG:
        gear(m, "3648b.dat", LGREY, (s * 90, AXY, z), "x")
        if z in ZW:
            if abs(z) == 180:
                axle(m, 7, BLACK, (s * 110, AXY, z), "x")            # x 40..180: конец изнутри, шестерня, конец снаружи, колесо
            else:
                axle(m, 6, BLACK, (s * 120, AXY, z), "x")            # x 60..180
        else:
            axle(m, 3, BLACK, (s * 90, AXY, z), "x")                 # паразитка x 60..120
    m.step("Колёса")
    rot = ldr.ry(90) if s > 0 else ldr.ry(-90)
    for z in ZW:
        m.add("56145.dat", LGREY, (s * WX, AXY, z), rot)
        m.add("55976.dat", BLACK, (s * WX, AXY, z), rot)
    m.sub = ""


def build():
    m = ldr.Model("six.ldr")
    m.tag = ""
    m.sub = ""
    for s in (-1, 1):
        side(m, s)
    m.step("Поперечины между бортами (оси 8 сквозь внутренние ряды)")
    for z in (-40, 40, -20, 20):
        axle(m, 8, BLACK, (0, AXY, z), "x")
    return m


if __name__ == "__main__":
    m = build()
    car.check(m)
    car.overlaps(m)
    car.beam_overlaps(m)
    car.pin_seating(m)
    car.hole_sharing(m)
