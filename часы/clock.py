"""Маятниковые часы (Алексей 24.11: «+ маятниковые часы ... сделай все сразу»).
Рама - две стоячие балки 15 (передняя z -30, задняя z 30), оси вдоль Z, шестерни между ними (z ±10). Сверху вниз:
ось маятника - якорь из двух L 2x4 (крестовые концы на оси) над анкерным колесом 24з.; анкерная ось 24з. + 8з.;
промежуточная 40з. + 8з. со стрелкой (L 2x4) спереди; барабан 40з. с катушкой сзади, верёвка с грузом.
Маятник сзади: L 2x4 на оси + балка 11, внизу шина на оси. Передача барабан -> анкерное колесо 1:25.
Часовой стрелки нет: 1:12 из шестерён Алексея (8, 12, 16, 20, 24, 36, 40) не собирается.
Оси: Y вниз (земля 0), X вправо, Z: минус - лицо часов. Запуск: python clock.py (законы)
"""
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "ядро"))
import car
import body
import ldr
from car import BLACK, LGREY, YELLOW, BLUE, RED, beam, brick, axle, gear

Y_ANCHOR, Y_ESC, Y_MID, Y_DRUM = -420, -360, -300, -240
BOT = -140                   # нижняя дырка балок рамы
PZ = 30                      # балки рамы на z ±30
BOB_Y = -220                 # грузик маятника (низ балки 11; на -240 - ось барабана)


def build():
    m = ldr.Model("clock.ldr")
    m.tag = ""
    m.sub = ""
    m.step("Основание: кирпичи 1x16 поперёк спереди и сзади, рама - две балки 15 стоя")
    for s in (1, -1):
        brick(m, 15, BLACK, (0, BOT, s * (PZ + 20)), "x")            # дырки по Z на x -140..140
        beam(m, 15, BLACK, (0, (BOT + Y_ANCHOR) // 2, s * PZ), "y", "z")   # дырки по Z на y -420..-140
        m.add("2780.dat", BLACK, (0, BOT, s * (PZ + 10)), ldr.ry(90))       # балка рамы + кирпич
    m.step("Барабан: 40з., катушка из втулок сзади, верёвка с грузом")
    axle(m, 6, BLACK, (0, Y_DRUM, 20), "z")                          # z -40..80
    gear(m, "3649.dat", LGREY, (0, Y_DRUM, 10), "z")
    for z in (50, 60, 70):
        gear(m, "3713.dat", LGREY, (0, Y_DRUM, z), "z")
    m.add("4-4cyli.dat", 15, (20, Y_DRUM, 60), [[2, 0, 0], [0, 70, 0], [0, 0, 2]], note="трос")   # верёвка вниз
    m.add("2736.dat", LGREY, (20, Y_DRUM + 80, 60), ldr.rz(90), note="трос")                     # груз-крюк
    m.step("Промежуточная ось: 40з. к анкерной, 8з. к барабану, стрелка спереди")
    axle(m, 5, BLACK, (0, Y_MID, -10), "z")                          # z -60..40
    gear(m, "3649.dat", LGREY, (0, Y_MID, -10), "z")
    gear(m, "3647.dat", LGREY, (0, Y_MID, 10), "z")
    body.side_part(m, "32140.dat", RED, (0, Y_MID, -50), body.UP, (1, 0, 0))   # стрелка: крестовой конец на оси
    m.step("Анкерная ось: 8з. к промежуточной, анкерное колесо 24з.")
    axle(m, 4, BLACK, (0, Y_ESC, 0), "z")                            # z -40..40
    gear(m, "3647.dat", LGREY, (0, Y_ESC, -10), "z")
    gear(m, "3648b.dat", YELLOW, (0, Y_ESC, 10), "z")
    m.step("Ось маятника: якорь - L 2x4 над анкерным колесом; маятник сзади")
    axle(m, 5, BLACK, (0, Y_ANCHOR, 10), "z")                        # z -40..60
    body.side_part(m, "32140.dat", BLACK, (0, Y_ANCHOR, 10), (1, 0, 0), body.DOWN)   # якорь: плечо вбок, лапа вниз
    body.side_part(m, "32140.dat", YELLOW, (0, Y_ANCHOR, 50), body.DOWN, (1, 0, 0))     # подвес: крест на оси, вниз
    beam(m, 11, YELLOW, (0, Y_ANCHOR + 120, 70), "y", "z")           # маятник: дырки y -420..-220
    for y in (Y_ANCHOR + 20, Y_ANCHOR + 40):
        m.add("2780.dat", BLACK, (0, y, 60), ldr.ry(90))           # подвес + маятник
    axle(m, 4, BLACK, (0, BOB_Y, 100), "z")                          # z 60..140
    m.add("56145.dat", LGREY, (0, BOB_Y, 115))
    m.add("55976.dat", BLACK, (0, BOB_Y, 115))
    return m


if __name__ == "__main__":
    import inventory
    m = build()
    car.check(m)
    car.overlaps(m)
    car.beam_overlaps(m)
    car.pin_seating(m)
    car.hole_sharing(m)
    print("нехватка:", inventory.shortage(m.parts()) or "нет", len(m.parts()))
