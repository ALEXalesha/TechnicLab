"""Механическая рука (Алексей 24.11: «руку ... сделай все сразу»): плечо и локоть - актуаторы с моторами M,
захват - мотор L (его вал = ось одной челюсти, вторая крутится навстречу через 24з.-24з.).
Двойное плечо (балки 11, x ±50) и двойное предплечье (балки 15, x ±70); оба актуатора посередине (x 0), их проушины
сидят на ОСЯХ поперёк. Поза: плечо вертикально, предплечье вперёд, челюсти вниз.
Оси: Y вниз (земля 0), Z: минус - вперёд, X поперёк. Запуск: python arm.py (законы)
"""
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "ядро"))
import math

import car
import body
import ldr
from car import BLACK, LGREY, DGREY, YELLOW, BLUE, beam, brick, axle, gear

BY = -31                     # дырки кирпичей основания
S = (-111, 0)                # ось плеча: верх стоек L 3x5
E = (-311, 0)                # ось локтя: верх плеча (балки 11)
A, B1 = (BY, -160), (-151, 0)          # актуатор плеча: конец в основании, основание на плече (|..| = 200)
D, C = (E[0], -160), (-191, 0)         # актуатор локтя: основание на предплечье, конец на плече
JAW_Z = (-220, -280)                   # оси челюстей (ведущая - мотор L - на -280)


def _rx_rad(a):
    c, s_ = math.cos(a), math.sin(a)
    return [[1, 0, 0], [0, c, -s_], [0, s_, c]]


def actuator(m, x, base, end, color=LGREY):
    """Актуатор в плоскости YZ: основание (с мотором M в линию) в base, конец в end; |end-base| = 200 (сжат)."""
    b_loc, e_loc = (20, -10), (0, 190)
    src = (e_loc[0] - b_loc[0], e_loc[1] - b_loc[1])
    dst = (end[0] - base[0], end[1] - base[1])
    R = _rx_rad(math.atan2(dst[1], dst[0]) - math.atan2(src[1], src[0]))
    rb = ldr.mat_vec(R, (0, b_loc[0], b_loc[1]))
    re = ldr.mat_vec(R, (0, e_loc[0], e_loc[1]))
    P = (x, (base[0] - rb[1] + end[0] - re[1]) / 2, (base[1] - rb[2] + end[1] - re[2]) / 2)   # 201 на 200: по 0,5 с концов
    m.add("61927-f1.dat", color, P, R)
    ra = ldr.mat_vec(R, (0, 0, -10))
    axle(m, 3, BLACK, (x, P[1] + ra[1], P[2] + ra[2]), "z").rot = ldr.mat_mul(R, car.AXIS_ROT["z"])
    rm = ldr.mat_vec(R, (0, 0, -20))
    m.add("58120c01.dat", DGREY, (x, P[1] + rm[1], P[2] + rm[2]), ldr.mat_mul(R, ldr.ry(180)))


def _brace_rot(p0, p1):
    """Поворот балки «вдоль z, дырки по x» так, чтобы её ось смотрела из p0 в p1 (y, z)."""
    dy, dz = p1[0] - p0[0], p1[1] - p0[1]
    a = -math.atan2(dy, dz)
    c, s_ = math.cos(a), math.sin(a)
    return ldr.mat_mul([[1, 0, 0], [0, c, -s_], [0, s_, c]], car.ROT[("z", "x")])


def build():
    m = ldr.Model("arm.ldr")
    m.tag = ""
    m.sub = ""
    m.step("Основание: два кирпича 1x16 и поперечные оси")
    for s in (1, -1):
        brick(m, 15, BLACK, (s * 90, BY, -20), "z")                 # дырки z -160..120
    axle(m, 10, BLACK, (0, BY, A[1]), "x")                         # x -100..100: конец актуатора плеча
    m.step("Стойки плеча: L 3x5 (короткое плечо на кирпиче, длинное до оси плеча)")
    for s in (1, -1):
        body.side_part(m, "32526.dat", YELLOW, (s * 70, S[0], S[1]), body.DOWN, body.BACK)   # верх (-111,0), низ z 0..40
        for z in (20, 40):
            m.add("2780.dat", BLACK, (s * 80, BY, z))
    m.step("Двойное плечо: балки 11 вверх; оси плеча и основания актуатора")
    for s in (1, -1):
        beam(m, 11, YELLOW, (s * 50, (S[0] + E[0]) // 2, 0), "y", "x")   # y -311..-111
    axle(m, 8, BLACK, (0, S[0], S[1]), "x")                         # x -80..80: стойки + плечо
    axle(m, 6, BLACK, (0, B1[0], B1[1]), "x")                       # x -60..60: плечо + проушина посередине
    axle(m, 10, BLACK, (0, C[0], C[1]), "x")                        # x -100..100: плечо + распорка локтя снаружи
    m.step("Двойное предплечье: балки 15 вперёд; ось локтя, ось основания актуатора локтя")
    for s in (1, -1):
        beam(m, 15, YELLOW, (s * 70, E[0], -140), "z", "x")         # z -280..0
    axle(m, 8, BLACK, (0, E[0], E[1]), "x")                         # x -80..80
    axle(m, 10, BLACK, (0, D[0], D[1]), "x")                        # x -100..100: предплечье + распорка
    m.step("Актуатор плеча с мотором M; локоть - распорка балка 15 (актуатор у Алексея один)")
    actuator(m, 0, B1, A)
    a = math.atan2(C[0] - D[0], C[1] - D[1])                         # ось распорки от D к C в плоскости YZ
    R = ldr.mat_mul(_rx_rad(-a), car.ROT[("z", "x")])
    R = ldr.mat_mul(_rx_rad(math.atan2(C[0] - D[0], C[1] - D[1]) * 0), R) if False else _brace_rot(D, C)
    m.add(car.BEAM[15], BLACK, (90, D[0] + (C[0] - D[0]) * 0.7, D[1] + (C[1] - D[1]) * 0.7), R)   # x 90: снаружи предплечья, на удлинённых осях   # дырки 0 (D) и 10 (C)
    m.step("Захват: две оси поперёк, 24з.-24з., челюсти L 3x5 вниз, мотор L снаружи на ведущей оси")
    for z in JAW_Z:
        axle(m, 8, BLACK, (0, E[0], z), "x")
        gear(m, "3648b.dat", LGREY, (-40, E[0], z), "x")
    for z, back in ((JAW_Z[0], True), (JAW_Z[1], False)):
        for x in (-20, 20):
            body.side_part(m, "32526.dat", BLACK, (x, E[0], z), body.DOWN, body.BACK if back else body.FWD)
    m.add("99499.dat", DGREY, (80, E[0], JAW_Z[1]), ldr.ry(90))       # лицо на x 80, вал - ось челюсти
    m.add("6558.dat", BLUE, (80, E[0], JAW_Z[1] + 20))               # 3L: предплечье + лицо мотора
    power(m)
    return m


BAT_A = (0, BY - 20, 240)    # блок лёжа за основанием: торцевые дырки (x ±110) на y BY и BY-40, z 200 и 280


def power(m):
    """Питание (Алексей 25.11: «не у всех моделей есть передатчик ... и батарейный блок»): блок лёжа позади основания -
    заодно противовес руке; держат его две кирпича 1x12 снаружи (x ±120) на двух осях 16 сквозь кирпичи основания (z 100, 120),
    по два штифта в торцы блока. Приёмник ИК - на правом кирпиче снаружи, два штифта лица. Красный выход - мотор M
    актуатора плеча, синий - мотор L захвата."""
    x0, y0, z0 = BAT_A
    m.step("Питание: две оси 16 сквозь основание, кирпичи 1x12 назад")
    for z in (100, 120):
        axle(m, 16, BLACK, (0, BY, z), "x")                          # x -160..160: кирпичи + балки
    for s in (1, -1):
        brick(m, 11, BLACK, (s * 120, BY, 200), "z")                 # кирпич 1x12: дырки z 100..300
    m.step("Батарейный блок лёжа (переключатель сверху), по два штифта в торцы")
    m.add("58119.dat", LGREY, BAT_A, ldr.rx(90))
    for s in (1, -1):
        for z in (z0 - 40, z0 + 40):
            m.add("2780.dat", BLACK, (s * 110, BY, z))
    m.step("Приёмник ИК на правом кирпиче: лицо к нему, два штифта")
    m.add("58123.dat", LGREY, (170, BY - 10, 240), ldr.ry(90))       # лицо (x 130) к балке, дырки лица z 220 и 260
    for z in (220, 260):
        m.add("2780.dat", BLACK, (130, BY, z))


if __name__ == "__main__":
    import inventory
    m = build()
    car.check(m)
    car.overlaps(m)
    car.beam_overlaps(m)
    car.pin_seating(m)
    car.hole_sharing(m)
    print("нехватка:", inventory.shortage(m.parts()) or "нет", len(m.parts()))
