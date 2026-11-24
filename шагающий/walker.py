"""Шагающий робот (Алексей 24.11: «шагающий механизм ... сделай все сразу»): 4 ноги на механизме Хокенса
(кривошип 40 : шатун 100 : коромысло 100 : стойка 80, стопа на продолжении шатуна в 200 от кривошипа - внизу
идёт почти по прямой). Кривошипы передней и задней пары - на общих осях поперёк, повёрнуты на 180°; оси
связаны цепочкой 24з. посередине; XL стоит сверху, 20з. кон. на его выходе крутит 20з. кон. на средней оси.
Оси: Y вниз (земля 0), Z вперёд-назад, X поперёк. Запуск: python walker.py (законы)
"""
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "ядро"))
import math

import car
import ldr
from car import BLACK, LGREY, YELLOW, BLUE, TAN, beam, axle, gear

YF = -240                    # дырки рамы (оси кривошипов и коромысел)
ZA = (-60, 60)               # оси кривошипов: передняя и задняя (коромысла - на z ±140, в раме)
CRANK, COUPLER, ROCKER, GROUND = 40, 100, 100, 80
LAYER = {"frame": 50, "rocker": 70, "coupler": 90, "crank": 110}   # |x| слоёв


def _rot_zx(dz, dy):
    """Балка «вдоль z, дырки по x», повёрнутая в плоскости YZ так, что её ось смотрит в (dz, dy)."""
    a = -math.atan2(dy, dz)                                        # rx: (0,0,1) -> (0, -sin a, cos a)
    c, s = math.cos(a), math.sin(a)
    rx = [[1, 0, 0], [0, c, -s], [0, s, c]]                       # поворот вокруг X: z -> (y = s, z = c)
    return ldr.mat_mul(rx, car.ROT[("z", "x")])


def _beam_from(m, n, color, x, p0, dirv):
    """Балка n дырок: дырка 0 в точке p0 (z, y), ось по единичному dirv (dz, dy)."""
    L = (n - 1) * 20
    c = (p0[0] + dirv[0] * L / 2, p0[1] + dirv[1] * L / 2)
    return m.add(car.BEAM[n] if n in car.BEAM else car.BEAM[7], color, (x, c[1], c[0]), _rot_zx(*dirv))


def linkage(phi, zA, sgn):
    """Точки механизма (z, y) при угле кривошипа phi; sgn - коромысло спереди (-1) или сзади (+1) от кривошипа."""
    A = (zA, YF)
    B = (zA + sgn * GROUND, YF)
    C = (A[0] + CRANK * math.cos(phi), A[1] + CRANK * math.sin(phi))
    dx, dy = B[0] - C[0], B[1] - C[1]
    d = math.hypot(dx, dy)
    a = d / 2
    h = math.sqrt(max(COUPLER ** 2 - a * a, 0))
    mx, my = C[0] + dx / 2, C[1] + dy / 2
    D = (mx - dy / d * h * sgn, my + dx / d * h * sgn)                # нижнее пересечение окружностей
    if D[1] < YF:
        D = (mx + dy / d * h * sgn, my - dx / d * h * sgn)
    P = (C[0] + 2 * (D[0] - C[0]), C[1] + 2 * (D[1] - C[1]))
    return A, B, C, D, P


def foot_low_phi(zA, sgn):
    """Угол кривошипа, при котором стопа ниже всего (нога стоит)."""
    return max((k * math.pi / 90 for k in range(180)), key=lambda f: linkage(f, zA, sgn)[4][1])


def leg(m, s, zA, sgn, phi):
    A, B, C, D, P = linkage(phi, zA, sgn)
    x = lambda k: s * LAYER[k]
    u = lambda p, q: ((q[0] - p[0]) / math.hypot(q[0] - p[0], q[1] - p[1]), (q[1] - p[1]) / math.hypot(q[0] - p[0], q[1] - p[1]))
    _beam_from(m, 3, BLACK, x("crank"), A, u(A, C))               # кривошип: дырки A, -, C
    _beam_from(m, 11 if s > 0 else 15, YELLOW, x("coupler"), C, u(C, P))   # шатун: C (0), D (5), стопа P (10); балок 11 две
    _beam_from(m, 7, BLACK, x("rocker"), B, u(B, D))              # коромысло: B (0), D (5)
    m.add("2780.dat", BLACK, (s * (LAYER["crank"] - 10), C[1], C[0]))      # кривошип + шатун
    m.add("2780.dat", BLACK, (s * (LAYER["coupler"] - 10), D[1], D[0]))    # шатун + коромысло
    m.add("2780.dat", BLACK, (s * (LAYER["rocker"] - 10), B[1], B[0]))     # коромысло + рама
    return P


def build():
    m = ldr.Model("walker.ldr")
    m.tag = ""
    m.sub = ""
    m.step("Рама: две балки 15 вдоль, оси кривошипов и цепочки поперёк")
    for s in (1, -1):
        car.brick(m, 15, BLACK, (s * LAYER["frame"], YF, 0), "z")         # кирпич 1x16: дырки z -140..140
    for z in ZA:
        axle(m, 12, BLACK, (0, YF, z), "x")                               # x -120..120: кривошипы обеих сторон
    m.step("Цепочка 24з. между осями кривошипов")
    for z in range(ZA[0], ZA[1] + 1, 60):
        gear(m, "3648b.dat", LGREY, (0, YF, z), "x")
        if z not in ZA:
            axle(m, 6 if z == 0 else 4, BLACK, (0, YF, z), "x")           # паразитки (средняя - длиннее, к 20з.)
    m.step("Мотор XL сверху: 20з. кон. на выходе -> 20з. кон. на средней оси")
    gear(m, "18575.dat", TAN, (30, YF, 0), "x")
    gear(m, "18575.dat", TAN, (0, YF - 30, 0), "y")
    axle(m, 3, BLACK, (0, YF - 50, 0), "y")
    m.add("58121c01.dat", car.DGREY, (0, YF - 50, 0), ldr.rx(90))         # выход вниз, корпус вверх
    import body
    for s in (1, -1):                                                     # стойки XL: L 3x5 (x ±70), 2 штифта в раму
        body.side_part(m, "32526.dat", YELLOW, (s * 70, YF - 80, 0), body.DOWN, body.BACK)   # верх (-320, 0), угол (-240, 0)
        for z in (20, 40):
            m.add("2780.dat", BLACK, (s * 60, YF, z))
        m.add("6558.dat", BLUE, (s * 60, YF - 60, 0))                     # 3L: ухо XL (x ±50) + стойка
    m.step("Ноги: механизм Хокенса, левые и правые, передние и задние (кривошипы на 180°)")
    feet = []
    for zA, sgn in ((ZA[0], -1), (ZA[1], 1)):
        phi = foot_low_phi(zA, sgn)
        for s in (1, -1):
            feet.append(leg(m, s, zA, sgn, phi + (0 if s > 0 else math.pi)))
    power(m)
    return m, feet


BAT_W = (0, -120, 0)         # блок стоя под рамой между ногами: верх y -209 (под шестернями), низ -50


def power(m):
    """Питание (Алексей 25.11): блок батарей под рамой между ногами, длинной стороной вдоль. Торцы блока (дырки вдоль Z)
    висят на подвесах: L 2x4 внутри рамы (x ±30) - штифт в раму и крестовой конец на оси 6 (z ±120), ось от этого не
    крутится; на оси посередине поперечный блок 1x2 - его дырка смотрит вдоль Z; к ней балка 3 поперёк, к балке 3 - две
    стоячие балки 9 (дырки вдоль Z), в них по два штифта из торца блока. Приёмник ИК сзади на задних балках 9."""
    import body
    m.step("Подвесы блока: L 2x4 в раму, оси 6 через крестовые концы, поперечные блоки 1x2")
    for zs in (1, -1):
        u = body.FWD if zs > 0 else body.BACK
        for x in (30, -30):
            body.side_part(m, "32140.dat", BLACK, (x, YF, zs * 120), u, body.DOWN)   # крест на z ±120, дырки до ±60
            m.add("2780.dat", BLACK, (x + (10 if x > 0 else -10), YF, zs * 100))       # L + рама
        axle(m, 6, BLACK, (0, YF, zs * 120), "x")                     # x -60..60: рама, кресты L, блок 1x2
        m.add("6536.dat", BLACK, (0, YF, zs * 120))                   # дырка штифта - на 20 ниже, вдоль Z
    m.step("Балки 3 поперёк и стоячие балки 9 (дырки вдоль Z)")
    for zs in (1, -1):
        beam(m, 3, BLACK, (0, YF + 20, zs * 140), "x", "z")           # x -20..20, за поперечным блоком
        for x in (-20, 0, 20):
            m.add("2780.dat", BLACK, (x, YF + 20, zs * 130), ldr.ry(90))   # балка 3 + блок 1x2 / балки 9
        for x in (-20, 20):
            beam(m, 9, YELLOW, (x, -140, zs * 120), "y", "z")         # дырки y -220..-60
    m.step("Батарейный блок между подвесами: по два штифта в каждый торец")
    m.add("58119.dat", LGREY, BAT_W, ldr.ry(90))
    for zs in (1, -1):
        for x in (-20, 20):
            for y in (BAT_W[1] - 40, BAT_W[1] + 40):
                m.add("2780.dat", BLACK, (x, y, zs * 110), ldr.ry(90))
    m.step("Приёмник ИК сзади: лицо к задним балкам 9, два штифта")
    m.add("58123.dat", LGREY, (0, -130, 170))                         # лицо z 130, дырки лица (±20, -120)
    for x in (-20, 20):
        m.add("2780.dat", BLACK, (x, -120, 130), ldr.ry(90))


if __name__ == "__main__":
    import inventory
    m, feet = build()
    car.check(m)
    car.overlaps(m)
    car.beam_overlaps(m)
    car.pin_seating(m)
    car.hole_sharing(m)
    print("стопы (z, y):", [(round(p[0]), round(p[1])) for p in feet])
    print("нехватка:", inventory.shortage(m.parts()) or "нет", len(m.parts()))
