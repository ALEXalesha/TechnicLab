"""Внедорожник: шасси v1 (мосты, валы, центральный дифференциал, XL).
Оси: X - вправо, Y - вниз (земля y=0), Z - назад. 1 модуль = 20 LDU.
Привод: XL -> 40з. -> 40з. -> вал поперёк -> 20з.дв.кон. -> венец 28з. центрального дифференциала
-> валы вперёд и назад -> 12з.дв.кон. -> 20з.дв.кон. на оси моста (без межколёсного дифференциала).
"""
import math
import os
import sys
import ldr

BLACK, YELLOW, LGREY, DGREY, RED, TAN, BLUE, WHITE = 0, 14, 71, 72, 4, 19, 1, 15
AX_Y = -71            # высота осей колёс и валов (радиус шины 56x26)
AXLE_Z = 260          # задний мост (база 28 модулей: -300..260)
TRACK_X = 160         # середина колеса
BEAM = {3: "32523.dat", 5: "32316.dat", 7: "32524.dat", 9: "40490.dat", 11: "32525.dat", 13: "41239.dat", 15: "32278.dat"}
AXLE = {2: "32062.dat", 3: "4519.dat", 4: "3705.dat", 5: "32073.dat", 6: "3706.dat", 7: "44294.dat", 8: "3707.dat", 10: "3737.dat", 12: "3708.dat", 16: "50451.dat"}

ROT = {  # (вдоль, отверстия) -> поворот балки (базовая: вдоль Z, отверстия по Y)
    ("z", "y"): ldr.I,
    ("z", "x"): ldr.rz(90),
    ("x", "y"): ldr.ry(90),
    ("x", "z"): ldr.mat_mul(ldr.rz(90), ldr.rx(90)),
    ("y", "z"): ldr.rx(90),
    ("y", "x"): ldr.mat_mul(ldr.ry(90), ldr.rx(90)),
}
AXIS_ROT = {"x": ldr.I, "y": ldr.rz(90), "z": ldr.ry(90)}      # ось (базовая вдоль X)
GEAR_ROT = {"z": ldr.I, "x": ldr.ry(90), "y": ldr.rx(90)}      # шестерня/втулка (базовая ось Z)


def beam(m, n, color, c, along, holes):
    return m.add(BEAM[n], color, c, ROT[(along, holes)])


BRICK = {15: "3703.dat", 13: "32018.dat", 11: "3895.dat", 7: "3702.dat", 5: "3894.dat", 3: "3701.dat"}   # дырок -> кирпич


def brick(m, n, color, c, along):
    """Technic-кирпич с n дырками (1x(n+1)) вместо балки: c - середина ряда дырок, шипы вверх.
    Дырка на 10 ниже верха кирпича. along: "z" (дырки по X) или "x" (дырки по Z)."""
    if along == "y":                                   # стоя: длинная сторона вверх, дырки по X, шипы вперёд (-Z)
        return m.add(BRICK[n], color, (c[0], c[1], c[2] - 10), [[0, 0, 1], [1, 0, 0], [0, 1, 0]])
    rot = ldr.ry(90) if along == "z" else ldr.I
    return m.add(BRICK[n], color, (c[0], c[1] - 10, c[2]), rot)


def axle(m, n, color, c, along):
    return m.add(AXLE[n], color, c, AXIS_ROT[along])


def gear(m, name, color, c, axis, flip=False):
    r = GEAR_ROT[axis]
    if flip:
        r = ldr.mat_mul(r, ldr.ry(180))
    return m.add(name, color, c, r)


def wheel_axle(m, z0, front):
    m.tag = "steer" if front else ""
    m.sub = "Передний мост" if front else "Задний мост"
    """Мост: рамка 5x7, ось из двух половин в 20з., шестерня-ведущая 12з. со стороны середины машины."""
    y = AX_Y
    k = 1 if not front else -1          # к середине машины: -k по Z
    side = 1 if not front else -1       # 20з. справа у заднего, слева у переднего (мост = задний, повёрнутый на 180°)
    m.step("Мост %s: рамка и шестерни" % ("передний" if front else "задний"))
    m.add("64179.dat", LGREY, (0, y, z0))
    gear(m, "18575.dat", TAN, (side * 20, y, z0), "x")
    m.step("Полуоси и втулки")
    for s in (1, -1):
        axle(m, 8, BLACK, (s * 90, y, z0), "x")          # половины оси: 10..170 и -170..-10 (встречаются в 20з.)
        gear(m, "3713.dat", LGREY, (s * 60, y, z0), "x")
    m.step("Ведущая шестерня")
    pz = z0 - k * 30
    gear(m, "32270.dat", BLACK, (0, y, pz), "z")
    m.step("Колёса")
    for s in (1, -1):
        rot = ldr.ry(90) if s > 0 else ldr.ry(-90)
        m.add("56145.dat", LGREY, (s * TRACK_X, y, z0), rot)
        m.add("55976.dat", BLACK, (s * TRACK_X, y, z0), rot)
    m.tag = ""


DIFF_Z = 10           # центральный дифференциал (0, -131, DIFF_Z), венец со стороны +Z
SHAFT_Y = -71
RAIL_Y = -171
FRONT_Z = -300        # передний мост (под V4: всё над шиной)
PIVOT_Z = -140        # кардан и вертикальная ось поворота переднего моста


def frame(m):
    """Лонжероны, XL, стойки и опоры вала (СХЕМА.md)."""
    m.step("Мотор XL: ось 4 и шестерня 20 на выход (до установки)")
    xl_z = DIFF_Z + 50                                   # 20з. в 1,5 мод. от центра красной 28з.
    axle(m, 4, BLACK, (0, -141, DIFF_Z + 50), "y")
    gear(m, "18575.dat", TAN, (0, -111, DIFF_Z + 50), "y")
    m.step("Мотор XL и лонжероны")
    m.add("58121c01.dat", DGREY, (0, -161, xl_z), ldr.rx(90))        # выход вниз
    for s in (1, -1):
        beam(m, 15, BLACK, (s * 70, RAIL_Y, 0), "z", "x")
        beam(m, 5, BLACK, (s * 70, RAIL_Y - 100, xl_z), "z", "x")     # верхний лонжерон у XL, z 20..100
        # XL шириной 5 модулей: бок на x=±50, лонжерон 60..80 - штифт 3L (30..90), полностью в обеих деталях
        m.add("6558.dat", BLUE, (s * 60, RAIL_Y, xl_z))
        m.add("6558.dat", BLUE, (s * 60, RAIL_Y - 100, xl_z))
    m.step("Стойки: верхний лонжерон к нижнему")
    for s in (1, -1):
        for z in (xl_z - 40,):                                          # одна стойка: верхний лонжерон держат XL и она
            beam(m, 7, BLACK, (s * 110, RAIL_Y - 60, z), "y", "x")     # y -291..-171, снаружи удлинителя
            m.add("6558.dat", BLUE, (s * 90, RAIL_Y, z))                # лонжерон (+ удлинитель на z=100) + стойка
            m.add("6558.dat", BLUE, (s * 90, RAIL_Y - 100, z))          # верхний лонжерон + стойка
    m.step("Стойки и поперечные оси опор вала")
    for z in (DIFF_Z - 50, DIFF_Z + 70):                  # z -40 и 80 - на сетке лонжерона (кратно 20)
        for s in (1, -1):
            beam(m, 5, BLACK, (s * 90, -131, z), "y", "x")              # y -171..-91: лонжерон и ось опоры
            m.add("2780.dat", BLACK, (s * 80, RAIL_Y, z))
        axle(m, 10, BLACK, (0, -91, z), "x")
        m.add("6536.dat", BLACK, (0, -91, z))
        for s in (1, -1):
            gear(m, "3713.dat", LGREY, (s * 20, -91, z), "x")


def rear_suspension(m):
    """Задний мост качается вокруг вала; два амортизатора от рамки моста к удлинителям лонжеронов."""
    z0 = AXLE_Z
    m.step("Удлинители лонжеронов сзади")
    for s in (1, -1):
        beam(m, 11, BLACK, (s * 90, RAIL_Y, 200), "z", "x")           # z 100..300 (под блоком - балка: шипы кирпича упрутся в блок)
        for z in (120, 140):
            m.add("2780.dat", BLACK, (s * 80, RAIL_Y, z))
    m.step("Амортизаторы")
    zs = z0 + 40
    for s in (1, -1):
        m.add("73129.dat", BLACK, (s * 70, -181, zs), ldr.ry(90))     # отверстия y=-181 (верх) и -71 (низ)
        m.add("32054.dat", BLUE, (s * 55, -71, zs), ldr.ry(0) if s > 0 else ldr.ry(180))
        m.add("6558.dat", BLUE, (s * 90, RAIL_Y, zs))                  # 3L: амортизатор + удлинитель + задняя стойка кузова
    m.step("Втулка: мост не уезжает по валу")
    gear(m, "3713.dat", LGREY, (0, AX_Y, z0 - 70), "z")


def front_yoke(m):
    """Вилка переднего моста (часть узла «Передний мост»): балки к рамке моста, стойки, ось с 32039 над карданом."""
    z0, zp = FRONT_Z, PIVOT_Z
    m.tag = "steer"
    m.sub = "Передний мост"
    m.step("Вилка переднего моста")
    for s in (1, -1):
        brick(m, 13, BLACK, (s * 60, AX_Y, (z0 - 40 + zp) // 2), "z")   # кирпич 1x14: z0-60 .. ось поворота+20
        for z in (z0 - 40, z0 + 40):
            m.add("2780.dat", BLACK, (s * 50, AX_Y, z))
        beam(m, 5, BLACK, (s * 80, -111, zp), "y", "x")              # стойки вилки, y -151..-71
        m.add("2780.dat", BLACK, (s * 70, AX_Y, zp))
    axle(m, 10, BLACK, (0, -131, zp), "x")
    m.add("32039.dat", LGREY, (0, -151, zp), ldr.rx(90))              # крестовое отверстие вертикально над карданом
    m.tag = ""
    m.sub = ""


def front_steering(m):
    """Передний мост поворачивается целиком вокруг вертикальной оси над карданом (кулаков нет).
    Ось поворота = вал серво: сверху серво, ниже подшипник 6536 на раме, внизу крестовое отверстие 32039 на вилке моста."""
    z0, zp = FRONT_Z, PIVOT_Z
    m.tag = "steer"
    m.tag = ""
    m.step("Подшипник оси поворота на раме")
    axle(m, 10, BLACK, (0, RAIL_Y, zp - 20), "x")                      # через передние удлинители
    m.add("6536.dat", BLACK, (0, RAIL_Y, zp - 20), ldr.rx(90))         # штифтовое отверстие вертикально на z=zp
    m.step("Передние удлинители лонжеронов")
    zs = zp + 60                                                       # серво в 3 модулях ЗА осью поворота (впереди V4)
    for s in (1, -1):
        brick(m, 15, BLACK, (s * 90, RAIL_Y, -260), "z")             # кирпич 1x16: z -400..-120 (спереди держат лебёдку)
        for z in (-140, -120):
            m.add("2780.dat", BLACK, (s * 80, RAIL_Y, z))
    m.step("Стойки серво")
    for s in (1, -1):
        brick(m, 11, BLACK, (s * 40, -251, zs), "y")                 # кирпич 1x12 стоя: дырки y -351..-151
    axle(m, 8, BLACK, (0, RAIL_Y, zs), "x")                           # через лонжероны и стойки
    for s in (1, -1):
        gear(m, "32123a.dat", LGREY, (s * 55, RAIL_Y, zs), "x")       # полувтулка между стойкой и лонжероном
    m.step("Серво руля и понижение 12:36 (±90° серво -> ±30° моста)")
    m.add("99498.dat", LGREY, (0, -201, zs), ldr.mat_mul(ldr.ry(180), ldr.rx(90)))   # выход вниз, корпус назад (впереди V4)
    for s in (1, -1):
        for y in (-291, -331):
            m.add("2780.dat", BLACK, (s * 30, y, zs))
    axle(m, 2, BLACK, (0, -201, zs), "y")
    gear(m, "32270.dat", BLACK, (0, -191, zs), "y")
    axle(m, 3, BLACK, (0, -171, zp), "y")                             # ось поворота (y -201..-141)
    gear(m, "32498.dat", BLACK, (0, -191, zp), "y")


ENG = (0, -251, -280)  # ось коленвала V4 (поперёк машины) под капотом


def v4_model():
    """Двигатель Алексея (собран у него, по 10 фото 24.11): V8 - два ряда по 4 цилиндра 2850b под 90° (±45° от
    вертикали), головки наружу-вверх, в окошках «клевер» видны красные поршни 2851; коленвал из жёлтых колен 2853
    вдоль блока, шатуны 2852 серые; торцы - V из балок 3 + балка 5 снизу; сверху в развале - две пластины 1x10.
    Начало координат - ось коленвала (её ось 12 ставится в engine). Вращение коленвала двигает поршни (как у него)."""
    v = ldr.Model("v4.ldr")
    v.step("V8 Алексея (собран заранее)")
    c45 = math.cos(math.radians(45))
    THROW, ROD, CYL = 10, 40, 50                  # колено 10, шатун 40 (шар), начало цилиндра в 50 от вала по оси ряда
    for i, x in enumerate((-60, -20, 20, 60)):
        phi = 90                                  # колена вниз: днища всех 8 поршней у верха головок, видны в окошках
        rc = ldr.mat_mul(ldr.rx(phi), ldr.ry(90))
        pin = ldr.mat_vec(rc, (10, 0, 0))         # ось колена на валу (дырка колена в x=-10 детали)
        v.add("2853.dat", YELLOW, (x - 5 + pin[0], pin[1], pin[2]), rc)
        for bank in (1, -1):
            u = (0, -c45, bank * c45)                                      # ось ряда: от вала к головке
            pu = pin[1] * u[1] + pin[2] * u[2]
            perp2 = pin[1] ** 2 + pin[2] ** 2 - pu ** 2
            t = pu + math.sqrt(ROD * ROD - perp2)                          # где поршень на оси ряда
            q = (0, t * u[1], t * u[2])
            d = (q[1] - pin[1], q[2] - pin[2])
            v.add("2852.dat", LGREY, (x + bank * 4, pin[1], pin[2]),
                  ldr.mat_mul(ldr.rx(math.degrees(math.atan2(-d[1], -d[0]))), ldr.ry(90)))
            r = ldr.rx(-bank * 45)
            v.add("2851.dat", RED, (x, q[1], q[2]), r)   # ось поршня - его Y, вдоль цилиндра; дырка пальца вдоль вала
            v.add("2850b.dat", LGREY, (x, CYL * u[1], CYL * u[2]), ldr.mat_mul(r, ldr.ry(90)))
    for x in (-90, 90):                                                      # торцы: буква V из балок 3 + низ балка 5
        beam(v, 5, LGREY, (x, 0, 0), "z", "x")   # средняя дырка - ось коленвала
        for bank in (1, -1):
            v.add(BEAM[3], LGREY, (x, -30 * c45, bank * 30 * c45),
                  ldr.mat_mul(ldr.rx(-bank * 45), ROT[("y", "x")]))
    for z in (-10, 10):                                                      # пластины сверху в развале
        v.add("4477.dat", LGREY, (0, -46, z))
    return v


def _v4_part_boxes():
    """Габарит каждой детали V8 по её настоящим вершинам (повёрнутый цилиндр по осям мира дал бы лишние 10 LDU)."""
    out = []
    for p in v4_model().parts():
        w = [ldr.mat_vec(p.rot, q) for q in ldr._points_cached(p.name)]
        out.append((tuple(min(v[k] for v in w) + p.pos[k] for k in range(3)),
                    tuple(max(v[k] for v in w) + p.pos[k] for k in range(3))))
    return out


def v4_box():
    """Габарит V8 от оси коленвала - из его деталей (раньше было число на глаз)."""
    bs = _v4_part_boxes()
    return (tuple(min(b[0][k] for b in bs) for k in range(3)), tuple(max(b[1][k] for b in bs) for k in range(3)))


L35 = [[0, 1, 0], [0, 0, 1], [1, 0, 0]]   # балка 3x5 L: длинное плечо вертикально вверх, короткое вдоль +Z внизу


def engine(m):
    """V4 поперёк под капотом. Торцы - L-балки 3x5: короткое плечо на переднем удлинителе (3 штифта),
    вверху коленвал. Мотор M (тот же выход приёмника, что XL) под коленвалом, 24з.-24з. справа снаружи."""
    x0, y0, z0 = ENG
    m.step("Торцевые L-балки двигателя")
    for s in (1, -1):
        m.add("32526.dat", BLACK, (s * 110, y0, z0), L35)             # дырки: (x, -251..-171, z0) и (x, -171, z0+20/40)
        for z in (z0, z0 + 20, z0 + 40):
            if s > 0 and z == z0:
                continue          # справа это отверстие удлинителя занимает штифт 3L мотора M
            m.add("2780.dat", BLACK, (s * 100, RAIL_Y, z))
    m.step("Мотор M и коленвал")
    m.add("58120c01.dat", DGREY, (70, y0 + 60, z0), ldr.ry(-90))      # лицо на x=70, корпус влево
    # мотор держат: штифт 3L из нижнего отверстия лица в передний удлинитель + выходная ось в L-балке (над торцом V4 - пусто)
    m.add("6558.dat", BLUE, (80, RAIL_Y, z0))
    axle(m, 5, BLACK, (100, y0 + 60, z0), "x")                        # x 50..150
    gear(m, "3648b.dat", LGREY, (130, y0 + 60, z0), "x")
    axle(m, 12, BLACK, (10, y0, z0), "x")                             # коленвал x -110..130
    gear(m, "3648b.dat", LGREY, (130, y0, z0), "x")
    m.step("V4 (твой собранный)")
    m.add("v4.ldr", 16, (0, y0, z0))


V4_BOX = v4_box()      # габарит V8 из деталей v4_model
V4_PART_BOXES = _v4_part_boxes()

WINCH_Z = -400         # ось мотора L и червяка (перед V4)
DRUM_Z = WINCH_Z + 40  # барабан за червяком, трос уходит вперёд под мотором


def winch(m):
    """Лебёдка: L-мотор стоит выходом вниз, червяк -> 24з. на оси барабана (1:24, червяк держит груз без тока).
    Трос с катушки x 20..40 идёт вперёд под мотором через отверстие 6536 (направляющая)."""
    zm, zd, y = WINCH_Z, DRUM_Z, RAIL_Y
    m.sub = "Лебёдка"
    m.step("Мотор L и стойки")
    m.add("99499.dat", DGREY, (0, y - 30, zm), ldr.rx(90))             # выход вниз (y=-201), корпус до y=-341
    for s in (1, -1):
        for z in (zm - 20, zm + 20):
            beam(m, 9, BLACK, (s * 50, y - 80, z), "y", "x")           # y -331..-171
            for yy in (y - 40, y - 160):                                # отверстия мотора y=-211 и -331
                m.add("6558.dat", BLUE, (s * 40, yy, z))                # 3L: мотор 10..30 + стойка 40..60
    m.step("Червяк на выходе мотора")
    axle(m, 4, BLACK, (0, y - 10, zm), "y")                             # y -221..-141, в моторе 20
    gear(m, "32123a.dat", LGREY, (0, y - 25, zm), "y")
    gear(m, "4716.dat", LGREY, (0, y, zm), "y")                         # червяк y -191..-151
    gear(m, "32123a.dat", LGREY, (0, y + 25, zm), "y")
    m.step("Нижние балки и направляющая троса")
    for s in (1, -1):
        beam(m, 5, BLACK, (s * 70, y, zm + 20), "z", "x")              # z -400..-320
        for z in (zm - 20, zm + 20):
            m.add("2780.dat", BLACK, (s * 60, y, z))
    axle(m, 6, BLACK, (0, y - 20, zm - 20), "x")                        # x -60..60, y -191, z -400
    gear(m, "3713.dat", LGREY, (-30, y - 20, zm - 20), "x")
    gear(m, "32123a.dat", LGREY, (15, y - 20, zm - 20), "x")
    m.add("6536.dat", BLACK, (30, y - 20, zm - 20))                     # отверстие для троса вдоль Z на y=-171, x=30
    m.sub = ""
    m.step("Поставь лебёдку: по 2 штифта в удлинители")
    m.steps[-1].attach = ["Лебёдка"]
    for s in (1, -1):
        for z in (zm, zm + 60):
            m.add("2780.dat", BLACK, (s * 80, y, z))
    m.step("Барабан: ось через удлинители, 24з. к червяку, катушка справа")
    axle(m, 12, BLACK, (0, y, zd), "x")                                 # x -120..120: втулки снаружи удлинителей
    gear(m, "3648b.dat", LGREY, (0, y, zd), "x")
    gear(m, "3713.dat", LGREY, (-20, y, zd), "x")
    gear(m, "32123a.dat", LGREY, (15, y, zd), "x")                      # катушка x 20..40
    gear(m, "3713.dat", LGREY, (50, y, zd), "x")
    for s in (1, -1):
        gear(m, "3713.dat", LGREY, (s * 110, y, zd), "x")
    m.step("Трос: привяжи свою верёвку (~40 см) к катушке, протяни вперёд через дырку 6536, на конец - крюк")
    L = 110                                                             # от катушки (z -360) за нос (z -470)
    m.add("4-4cyli.dat", 25, (30, y, zd), [[4, 0, 0], [0, 0, 4], [0, -L, 0]], note="трос")   # оранжевая линия = верёвка
    m.add("2736.dat", LGREY, (30, y, zd - L - 10), ldr.ry(-90), note="трос")                # крюк (буксирный шар или свой)


BAT = (0, -251, 160)   # батарейный блок 8881 над задним мостом (низ y=-181)


def power(m):
    """Блок 1 (езда, руль) на двух вертикальных балках; блок 2 (лебёдка, дверь) пристёгнут сзади штифтами 3L через «уши»;
    приёмники за блоком 2 на поперечной балке. Приёмник 1 от блока 1: красный - XL + M (V4), синий - серво.
    Приёмник 2 от блока 2: красный - L лебёдки, синий - M двери."""
    x0, y0, z0 = BAT
    m.step("Стойки батарейного блока")
    for s in (1, -1):
        beam(m, 7, BLACK, (s * 120, -231, z0 + 20), "y", "x")          # y -291..-171
        m.add("6558.dat", BLUE, (s * 105, RAIL_Y, z0 + 20))             # в удлинитель лонжерона
    m.step("Батарейный блок")
    m.add("58119.dat", LGREY, BAT)
    for s in (1, -1):
        for y in (y0 - 40, y0 + 40):
            m.add("2780.dat", BLACK, (s * 110, y, z0 + 20))
    m.step("Второй блок (лебёдка, дверь): за первым, «уши» к «ушам», на модуль выше - над амортизаторами")
    b2 = (0, y0 - 20, z0 + 80)
    m.add("58119.dat", LGREY, b2)
    for s in (1, -1):
        for y in (y0 - 20, y0):                                          # общие отверстия «ушей» y=-271 и -251
            m.add("6558.dat", BLUE, (s * 100, y, z0 + 40), ldr.ry(90))  # блок1 z 170..190 + блок2 z 210..230


def receivers(m):
    """Приёмники ИК снаружи средних стоек кабины (x ±140, z=20; стойки ставит body.b_pillars): лицом к середине, два
    отверстия лица (y -271 и -231). Кабина свободна под сиденья (Алексей 24.11: «кабину видно плохо»).
    Приёмник 1 (блок 1): красный XL + M (V8), синий серво; приёмник 2 (блок 2): красный L (лебёдка), синий M (дверь)."""
    zb = 20
    m.step("Приёмники ИК снаружи средних стоек кабины")
    for s in (1, -1):
        rot = [[0, 0, s], [1, 0, 0], [0, 1, 0]]                    # локальная X -> вверх/вниз, лицо (-Z) -> к середине
        m.add("58123.dat", LGREY, (s * 180, -251, zb - 10), rot)
        for y in (-271, -231):                                       # -211 и -251 - штифты стойки к раме
            m.add("2780.dat", BLACK, (s * 140, y, zb))


def drivetrain(m):
    y = SHAFT_Y
    m.step("Центральный дифференциал, валы; поставь оба моста")
    m.steps[-1].attach = ["Задний мост", "Передний мост"]
    m.add("65414c01.dat", LGREY, (0, y, DIFF_Z))         # дифференциал Алексея: красная 28з. дв.кон. на +Z (центр DIFF_Z+20)
    axle(m, 6, BLACK, (0, y, -65), "z")                  # вперёд: z -5..-125, в дифференциале и в кардане по 15
    m.add("61903.dat", LGREY, (0, y, PIVOT_Z))          # кардан в точке поворота
    axle(m, 7, BLACK, (0, y, -220), "z", ).note = "steer"   # от кардана к ведущей 12з. (z -150..-290): поворачивается с мостом
    axle(m, 12, BLACK, (0, y, 135), "z")                 # назад: z 15..255 (до ведущей заднего моста и в торец рамки)


def build():
    m = ldr.Model("suv.ldr")
    m.tag = ""
    wheel_axle(m, AXLE_Z, front=False)
    wheel_axle(m, FRONT_Z, front=True)
    front_yoke(m)
    m.sub = ""
    frame(m)
    drivetrain(m)
    rear_suspension(m)
    front_steering(m)
    power(m)
    receivers(m)
    engine(m)
    winch(m)
    return m


def check(m, verbose=True):
    import snaps
    parts = [p for p in m.parts() if p.note != "трос"]     # верёвка Алексея и крюк - не детали Lego
    pairs = snaps.connections(parts)
    linked = {i for ij in pairs for i in ij}
    bad = [i for i in range(len(parts)) if i not in linked]
    groups = snaps.components(parts, pairs)
    PINS = {"2780.dat", "6558.dat", "32054.dat", "3749.dat"}
    deg = {}
    for i, j in pairs:
        deg[i] = deg.get(i, 0) + 1
        deg[j] = deg.get(j, 0) + 1
    lonely = [i for i, p in enumerate(parts) if p.name in PINS and deg.get(i, 0) < 2]
    bad = bad + lonely
    if verbose:
        for i in lonely:
            p = parts[i]
            print("ШТИФТ ДЕРЖИТ ТОЛЬКО ОДНУ ДЕТАЛЬ: %s @ %s" % (p.name, [round(v) for v in p.pos]))
        for i in bad:
            p = parts[i]
            print("НЕ ДЕРЖИТСЯ: %s %s @ %s" % (p.name, ldr.title(p.name)[:40], [round(v) for v in p.pos]))
        print("деталей %d, групп сцепления %d (размеры %s)" % (len(parts), len(groups), [len(g) for g in groups[:6]]))
    return bad, groups


BULKY = {"58121c01.dat", "58120c01.dat", "99499.dat", "99498.dat", "58119.dat", "58123.dat", "65414c01.dat", "55976.dat",
         "56145.dat", "64179.dat", "73129.dat", "3649.dat", "18575.dat", "32270.dat", "61903.dat", "32498.dat",
         "3648b.dat", "4716.dat", "v4.ldr", "61927-f1.dat", "40344.dat", "4185a.dat"}


def steer_clearance(m, angles=(-25, -15, 15, 25), verbose=True):
    """Закон: передний мост, повёрнутый на угол вокруг оси поворота, не задевает шинами/дисками/рамкой моста остальное."""
    import math
    parts = m.parts()
    steer = [p for p in parts if p.note == "steer" and p.name in ("55976.dat", "56145.dat", "64179.dat")]
    rest = [p for p in parts if p.note != "steer" and p.name not in ("61903.dat", "3705.dat")]
    bad = []
    for a in angles:
        c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        for p in steer:
            dx, dz = p.pos[0], p.pos[2] - PIVOT_Z
            q = ldr.Part(p.name, p.color, (c * dx + s_ * dz, p.pos[1], -s_ * dx + c * dz + PIVOT_Z), ldr.mat_mul(ldr.ry(a), p.rot))
            A = q.world_bbox()
            for r in rest:
                B = r.world_bbox()
                if B and all(min(A[1][k], B[1][k]) - max(A[0][k], B[0][k]) > 4 for k in range(3)):
                    bad.append((a, q.name, r.name, [round(v) for v in r.pos]))
    if verbose:
        for b in bad[:12]:
            print("РУЛЬ %+d°: %s задевает %s %s" % b)
        print("задеваний при повороте: %d" % len(bad))
    return bad


GEARS = {"3649.dat", "18575.dat", "32270.dat", "65414c01.dat", "32498.dat", "3648b.dat", "4716.dat"}


def overlaps(m, shrink=2.0, verbose=True):
    """Закон: габариты крупных деталей (моторы, блок, приёмники, колёса, рамки, шестерни) не пересекаются.
    Габарит - по осям мира (для повёрнутых деталей с запасом), сжат на shrink LDU с каждой стороны.
    Пары, сцепленные напрямую (шестерня на оси рамки и т.п.), и шина с диском - не считаются."""
    import snaps
    parts = m.parts()
    idx = [i for i, p in enumerate(parts) if p.name in BULKY]
    bb = {i: (_boxes(parts[i]) if parts[i].name == "v4.ldr" else [_bbox(parts[i])]) for i in idx}
    bad = []
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            i, j = idx[a], idx[b]
            if any(A and B and all(min(A[1][k], B[1][k]) - max(A[0][k], B[0][k]) > 2 * shrink for k in range(3))
                   for A in bb[i] for B in bb[j]):
                if snaps._tyre_on_rim(parts[i], parts[j]) or snaps._tyre_on_rim(parts[j], parts[i]):
                    continue
                ni, nj = parts[i].name, parts[j].name
                # зацепление шестерён и шестерни в проёме рамки моста / в венце дифференциала - намеренно
                if {ni, nj} <= GEARS | {"64179.dat"} and ({ni, nj} & GEARS):
                    continue
                bad.append((parts[i], parts[j]))
    if verbose:
        for p, q in bad:
            print("ПЕРЕСЕЧЕНИЕ: %s %s  и  %s %s" % (p.name, [round(v) for v in p.pos], q.name, [round(v) for v in q.pos]))
        print("пересечений крупных деталей: %d" % len(bad))
    return bad


PINS = {"2780.dat", "6558.dat"}
PIN_SEAT = 15         # LDU: каждая половина штифта сидит в своей детали не меньше чем на 15 из 20


def pin_seating(m, verbose=True):
    """Закон: штифт сидит хотя бы в двух деталях, в каждой на PIN_SEAT LDU и больше.
    Ловит «полуштифт»: деталь на 10 LDU в стороне от сетки (зазор в полмодуля), а штифт формально касается отверстия."""
    import snaps
    parts = m.parts()
    S = [snaps.part_snaps(p) for p in parts]
    bad = []
    for i, p in enumerate(parts):
        if p.name not in PINS:
            continue
        seats = []
        for j, q in enumerate(parts):
            if j == i:
                continue
            best = 0.0
            sl = snaps.SHOCK_PRELOAD if q.name == "73129.dat" else 0.0
            for a in S[i]:
                if a.gender != "M":
                    continue
                for b in S[j]:
                    if b.gender == "F" and snaps.connects(a, b, slack=sl):
                        best = max(best, snaps.overlap_len(a, b, slack=sl))
            if best > 0.5:
                seats.append((round(best), q.name))
        if sum(1 for L, _ in seats if L >= PIN_SEAT) < 2:
            bad.append((p, seats))
    if verbose:
        for p, seats in bad:
            print("ШТИФТ СИДИТ МЕЛКО: %s @ %s -> %s" % (p.name, [round(v) for v in p.pos], seats))
        print("мелко сидящих штифтов: %d" % len(bad))
    return bad


def hole_sharing(m, verbose=True):
    """Закон: в одном отверстии не сидят две «папы» (штифт и ось, два штифта) на одном и том же участке.
    Ловит: ось крепления и штифт ножки арки в одной дырке основания."""
    import snaps
    parts = m.parts()
    S = [snaps.part_snaps(p) for p in parts]
    bad = []
    for i, p in enumerate(parts):
        for f in S[i]:
            if f.gender != "F":
                continue
            occ = []                     # (j, отрезок вдоль оси f)
            u = f.axis()
            for j, q in enumerate(parts):
                if j == i:
                    continue
                for mc in S[j]:
                    if mc.gender == "M" and snaps.connects(f, mc) and snaps.overlap_len(f, mc) > 2:
                        d = [mc.pos[k] - f.pos[k] for k in range(3)]
                        along = sum(d[k] * u[k] for k in range(3))
                        sg = 1 if sum(mc.axis()[k] * u[k] for k in range(3)) > 0 else -1
                        a0, a1 = sorted((along + sg * mc.span()[0], along + sg * mc.span()[1]))
                        f0, f1 = f.span()
                        occ.append((j, max(a0, f0), min(a1, f1)))
                        break
            for x in range(len(occ)):
                for y in range(x + 1, len(occ)):
                    (j1, s1, e1), (j2, s2, e2) = occ[x], occ[y]
                    if j1 != j2 and min(e1, e2) - max(s1, s2) > 2:
                        bad.append((p, parts[j1], parts[j2]))
    if verbose:
        for p, a_, b_ in bad[:10]:
            print("ДВЕ ДЕТАЛИ В ОДНОЙ ДЫРКЕ: %s @ %s: %s и %s" % (p.name, [round(v) for v in p.pos], a_.name, b_.name))
        print("отверстий с двумя «папами»: %d" % len(bad))
    return bad


SHAPED = {"32526.dat", "6629.dat", "32348.dat", "32140.dat", "60484.dat", "32009.dat", "32271.dat", "15458.dat", "64782.dat"}
BEAMS_ALL = set(BEAM.values()) | set(BRICK.values()) | SHAPED
BODY_BBOX = {"58120c01.dat": "58120.dat", "58121c01.dat": "58121.dat"}   # габарит мотора без кабеля


def _bbox(p):
    if p.name == "v4.ldr":
        return tuple(tuple(p.pos[k] + V4_BOX[i][k] for k in range(3)) for i in (0, 1))
    if p.name in BODY_BBOX:
        return ldr.Part(BODY_BBOX[p.name], p.color, p.pos, p.rot).world_bbox()
    return p.world_bbox()




def _boxes(p):
    """Габарит по частям: у L/гнутых балок - кубик 20x20x20 вокруг каждой дырки (пустой угол буквы L не занят)."""
    if p.name in ("61927-f1.dat", "61927-f2.dat"):                       # актуатор: корпус широкий, шток с проушиной узкий
        L = 190 if p.name.endswith("f1.dat") else 290
        out = []
        for lo, hi in (((-21, -19, -19), (21, 29, 150)), ((-10, -10, 150), (10, 10, L + 9))):
            cs = [ldr.mat_vec(p.rot, (x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
            out.append((tuple(min(c[k] for c in cs) + p.pos[k] for k in range(3)),
                        tuple(max(c[k] for c in cs) + p.pos[k] for k in range(3))))
        return out
    if p.name == "v4.ldr":                                               # V8: по деталям (развал между рядами пустой)
        return [tuple(tuple(b[i][k] + p.pos[k] for k in range(3)) for i in (0, 1)) for b in V4_PART_BOXES]
    if p.name not in SHAPED:
        b = _bbox(p)
        return [b] if b else []
    import snaps
    out = []
    for c in snaps.part_snaps(p):
        if c.gender == "F":
            u, (s0, s1) = c.axis(), c.span()
            ctr = [c.pos[k] + u[k] * (s0 + s1) / 2 for k in range(3)]          # середина отверстия, а не точка снапа
            out.append((tuple(ctr[k] - 10 for k in range(3)), tuple(ctr[k] + 10 for k in range(3))))
    return out


def beam_overlaps(m, gap=3.0, verbose=True):
    """Закон: балка не входит в другую балку, мотор, блок, приёмник, колесо, рамку или шестерню (габариты по осям)."""
    parts = m.parts()
    big = BULKY | set(BODY_BBOX) | {"99499.dat"}
    idx = [i for i, p in enumerate(parts) if p.name in BEAMS_ALL or p.name in big]
    bb = {i: _boxes(parts[i]) for i in idx}
    bad = []
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            i, j = idx[a], idx[b]
            if parts[i].name not in BEAMS_ALL and parts[j].name not in BEAMS_ALL:
                continue          # крупное с крупным - закон overlaps
            if any(all(min(A[1][k], B[1][k]) - max(A[0][k], B[0][k]) > gap for k in range(3))
                   for A in bb[i] for B in bb[j]):
                bad.append((parts[i], parts[j]))
    if verbose:
        for p, q in bad:
            print("БАЛКА ВХОДИТ: %s %s  и  %s %s" % (p.name, [round(v) for v in p.pos], q.name, [round(v) for v in q.pos]))
        print("балок внутри других деталей: %d" % len(bad))
    return bad


if __name__ == "__main__":
    import render
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    m = build()
    p = os.path.join(out, "suv.ldr")
    ldr.write_mpd(p, m, [v4_model()])
    check(m)
    overlaps(m)
    beam_overlaps(m)
    pin_seating(m)
    hole_sharing(m)
    import inventory
    print("нехватка по описи:", inventory.shortage(m.parts()) or "нет")
    steer_clearance(m)
    if "--img" in sys.argv:
        render.collage(p, os.path.join(out, "suv.png"))
