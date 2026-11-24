"""Кузов из Technic (Алексей 24.11: «Только Technic»): открытый рамный внедорожник.
Борта - в плоскостях x = ±150 (слой I, 140..160) и ±170 (слой O, 160..180), отверстия по X.
К шасси - осями вдоль X через свободные отверстия удлинителей/стоек, втулки - распорки.
"""
import ldr
import car
from car import BLACK, YELLOW, LGREY, DGREY, BLUE, RED, beam, brick, axle, gear

XI, XO = 150, 170          # слои борта


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def side_part(m, name, color, pos, u, w):
    """Изогнутая/L-балка в плоскости борта: локальная +Z детали -> мир u, локальная +X -> мир w (u, w в плоскости YZ)."""
    c1 = _cross(u, w)
    rot = [[w[0], c1[0], u[0]], [w[1], c1[1], u[1]], [w[2], c1[2], u[2]]]
    return m.add(name, color, pos, rot)


UP, DOWN, FWD, BACK = (0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1)


def mount_axle(m, s, z, y, x_from, x_to, spacers):
    """Ось вдоль X от отверстия шасси до борта; spacers - середины втулок между ними."""
    L = x_to - x_from
    n = {40: 2, 60: 3, 80: 4, 100: 5, 120: 6, 140: 7, 160: 8}[L]
    axle(m, n, BLACK, (s * (x_from + x_to) / 2, y, z), "x")
    for x in spacers:
        gear(m, "3713.dat", LGREY, (s * x, y, z), "x")


def sides(m):
    y = car.RAIL_Y
    for s in (1, -1):
        m.step("Порог %s" % ("правый" if s > 0 else "левый"))
        brick(m, 15, BLACK, (s * XI, y, -60), "z")                     # кирпич 1x16: дырки z -200..80
        for z in (-200, -180):
            mount_axle(m, s, z, y, 80, 180, (110, 130))                 # удлинитель -> порог 140..160 -> L стойки 160..180


def arch(m, s, zc, mounts, top=None, long_pins=(), base_beam=False):
    """Арка над колесом (центр zc): основание - кирпич 1x8 в слое I (y=-171, дырки zc-60..zc+60), к шасси двумя осями;
    сверху приподнятая арка из двух жёлтых L 3x5 (слои O и O2): ножки на zc±60, верх на y=-211, плечи внахлёст 3 дырками.
    Снизу ничего ниже y=-162: колесо при повороте и ходе подвески проходит под аркой."""
    y = car.RAIL_Y
    t = y - 40 if top is None else top                                         # высота верха арки (ножки до t+40)
    if base_beam:                                                              # балка 7: без шипов сверху - над ней стойка актуатора
        beam(m, 7, BLACK, (s * XI, y, zc), "z", "x")
    else:
        brick(m, 7, BLACK, (s * XI, y, zc), "z")                               # кирпич 1x8 (балок 7 не хватает)
    for z in mounts:
        mount_axle(m, s, z, y, 80, 160, (110, 130))
    side_part(m, "32526.dat", YELLOW, (s * XO, t, zc + 20), FWD, DOWN)    # ножка на zc-60, плечо zc+20..zc-60
    side_part(m, "32526.dat", YELLOW, (s * 190, t, zc - 20), BACK, DOWN)  # ножка на zc+60, плечо zc-20..zc+60
    m.add("2780.dat", BLACK, (s * 160, y, zc - 60))                             # ножка O -> основание
    m.add("6558.dat", BLUE, (s * 170, y, zc + 60))                              # ножка O2 -> основание (через пустой слой O)
    for z in (zc - 20, zc, zc + 20):
        if z in long_pins:
            m.add("6558.dat", BLUE, (s * 170, t, z))                            # 3L: стойка актуатора + плечи
        else:
            m.add("2780.dat", BLACK, (s * 180, t, z))                           # плечи внахлёст


def fenders(m):
    y0 = car.RAIL_Y
    for s in (1, -1):
        m.step("Арка переднего колеса %s" % ("справа" if s > 0 else "слева"))
        arch(m, s, car.FRONT_Z, (-320, -300), top=y0 - 20)
        m.step("Арка заднего колеса %s" % ("справа" if s > 0 else "слева"))
        arch(m, s, car.AXLE_Z, (220, 240), top=y0 - 20)   # задние не поворачивают: арка ниже, ножки по бокам колеса


def front_pillars(m):
    """Стойки лобовой рамки (z=-200), кабина пикапа выше на 6 модулей: L 3x5 (слой O) на пороге, балка 5 (I, y -311..-231),
    балка 5 (O, -371..-291), гнутая 4x6 (I): прямой участок -331..-431, гнутый назад до крестовой дырки (-467, -152)."""
    y = car.RAIL_Y
    for s in (1, -1):
        m.step("Стойка лобовой рамки %s" % ("справа" if s > 0 else "слева"))
        side_part(m, "32526.dat", LGREY, (s * XO, y - 80, -200), DOWN, BACK)   # вертикаль -251..-171, низ назад -180, -160
        m.add("2780.dat", BLACK, (s * 160, y, -160))
        beam(m, 5, LGREY, (s * XI, -271, -200), "y", "x")                      # I: -311..-231 (дырка -271 - ось панели)
        for yy in (y - 60, y - 80):
            m.add("2780.dat", BLACK, (s * 160, yy, -200))                       # L (O) + балка I
        beam(m, 5, LGREY, (s * XO, -331, -200), "y", "x")                      # O: -371..-291
        for yy in (-291, -311):
            m.add("2780.dat", BLACK, (s * 160, yy, -200))                       # балка I + балка O
        side_part(m, "6629.dat", LGREY, (s * XI, -331, -200), UP, BACK)         # I: -331..-431, верх назад (наклон стекла)
        for yy in (-351, -371):
            m.add("2780.dat", BLACK, (s * 160, yy, -200))                       # балка O + гнутая (на -331 - петля капота)


ZR = 420           # задние стойки (багажник +6 модулей, Алексей 24.11: «нет места, куда положить»)
ZD = 460           # петля двери багажника


def trunk_frame(m):
    """Рама под багажник: накладка (балка 5, x ±110, z 280..360) на удлинитель лонжерона и новая балка 5 (x ±90,
    z 340..420). Накладку к удлинителю держат штифт z=280 и 3L амортизатора z=300."""
    y = car.RAIL_Y
    m.step("Удлинение рамы назад под багажник")
    for s in (1, -1):
        beam(m, 5, BLACK, (s * 110, y, 320), "z", "x")                         # z 280..360
        m.add("2780.dat", BLACK, (s * 100, y, 280))
        beam(m, 5, BLACK, (s * 90, y, 380), "z", "x")                          # z 340..420


def trunk_floor(m):
    """Пол багажника: 6 поперечин (ось 6 + соединитель + ось 6, x -120..120) на z 320..420 сквозь балки рамы
    (x ±90), накладки (z 320..360) и низ задних стоек (z 380..420) - они же скрепляют раму."""
    y = car.RAIL_Y
    m.step("Пол кузова: шесть поперечин")
    for z in range(320, 421, 20):
        axle(m, 6, BLACK, (-60, y, z), "x")
        m.add("59443.dat", DGREY, (0, y, z), ldr.ry(90))
        axle(m, 6, BLACK, (60, y, z), "x")
    m.step("Задний борт кузова: поперечины между задними стойками")
    for yy in (-191, -211):                                                     # сквозь низ задних стоек (L, x 100..120)
        axle(m, 6, BLACK, (-60, yy, ZR), "x")
        m.add("59443.dat", DGREY, (0, yy, ZR), ldr.ry(90))
        axle(m, 6, BLACK, (60, yy, ZR), "x")
    for yy in (-271, -291):                                                     # сквозь балки 7 стоек (x 80..100)
        axle(m, 10, BLACK, (0, yy, ZR), "x")


def rear_posts(m):
    """Задние стойки кузова пикапа (z=420): L 3x5 (x 100..120) + балка 7 (80..100) до y=-351, между ними задний борт."""
    y = car.RAIL_Y
    for s in (1, -1):
        m.step("Задняя стойка %s" % ("справа" if s > 0 else "слева"))
        side_part(m, "32526.dat", LGREY, (s * 110, y - 80, ZR), DOWN, FWD)     # вертикаль -251..-171, низ вперёд 400, 380
        # к раме - поперечинами пола (trunk_floor): z 380, 400, 420 сквозь балку рамы и низ стойки
        beam(m, 7, BLACK, (s * 90, y - 120, ZR), "y", "x")                      # -351..-231
        for yy in (y - 60, y - 80):
            m.add("2780.dat", BLACK, (s * 100, yy, ZR))


def b_pillars(m):
    """Средние стойки кабины за сиденьями (z=20): справа балка 15, слева кирпич 1x16 стоя (x ±130, y -471..-191),
    двумя штифтами к стойкам рамы (балки 7, x ±110). Верх - задняя поперечина крыши кабины."""
    m.step("Средние стойки кабины")
    for s in (1, -1):
        if s > 0:
            beam(m, 15, LGREY, (s * 130, -331, 20), "y", "x")
        else:
            brick(m, 15, LGREY, (s * 130, -331, 20), "y")
        for yy in (-211, -251):
            m.add("2780.dat", BLACK, (s * 120, yy, 20))


def tailgate(m):
    """Дверь багажника: две гнутые 4x6 (слой x 160..180) на петлях (оси 4 через верх задних стоек), между ними две
    оси-перекладины, на них две чёрные рамки 4x6 - сплошная дверь. Справа актуатор 8x2x2: основание на кронштейне у блока 1 (z=140, y=-311), конец на двери
    (z=340, y=-331); мотор M в линию с актуатором. Ход 5 модулей открывает дверь примерно на 95°."""
    y = car.RAIL_Y
    m.sub = "Дверь багажника"
    m.tag = "door"
    m.step("Боковины двери")
    for s in (1, -1):
        side_part(m, "6629.dat", LGREY, (s * 170, -411, ZD), DOWN, FWD)       # крестовая дырка на петле, вниз до -311, низ внутрь
    m.step("Перекладины двери: две линии из осей поперёк, на них две чёрные рамки 4x6 - сплошная дверь")
    for s in (1, -1):
        m.add("40344.dat", BLACK, (s * 60, -331, ZD - 10), ldr.rx(90))          # стоит в плоскости двери, торцевые дырки по X
    for y in (-351, -311):                                                       # на y -351/-311 (стенки рамок x ±10, ±110)
        axle(m, 7, BLACK, (-110, y, ZD), "x")                                    # x -180..-40
        m.add("59443.dat", DGREY, (-40, y, ZD), ldr.ry(90))
        axle(m, 4, BLACK, (0, y, ZD), "x")                                       # x -40..40 (соединители - в проёмах рамок)
        m.add("59443.dat", DGREY, (40, y, ZD), ldr.ry(90))
        axle(m, 7, BLACK, (110, y, ZD), "x")                                     # x 40..180
    m.tag = ""
    m.sub = ""
    m.step("Поставь дверь: петли - оси через верх задних стоек")
    m.steps[-1].attach = ["Дверь багажника"]
    for s in (1, -1):
        mount_axle(m, s, ZD, -411, 100, 180, (130, 150))
    zb = ACT_B[1]
    m.step("Стойка актуатора на задней арке справа")
    side_part(m, "32140.dat", BLACK, (150, -251, zb), DOWN, BACK)                 # L 2x4: вверх от плеча арки до -251, низ z 260..280
    beam(m, 5, BLACK, (120, -271, zb), "y", "x")                                # y -311..-231, рядом с блоком 2 (x до 110)
    for yy in (-251, -231):
        m.add("6558.dat", BLUE, (140, yy, zb))                                  # 3L: балка 110..130 + L 2x4 140..160
    m.step("Актуатор и мотор M")
    m.add("61927-f1.dat", LGREY, (150, -331, zb + 10))                          # основание (150,-311,260), конец (150,-331,460)
    m.add("6558.dat", BLUE, (140, -311, zb))                                    # балка 110..130 + проушина 140..160
    m.add("2780.dat", BLACK, (160, -331, ZD))                                   # конец актуатора + боковина двери
    axle(m, 3, BLACK, (150, -331, zb), "z")                                     # мотор M -> вход актуатора
    m.add("58120c01.dat", DGREY, (150, -331, zb - 10), ldr.ry(180))             # корпус вперёд z 130..250, сбоку блоков


HINGE = (-411, ZD)                     # (y, z) петли двери
ACT_B, ACT_E0 = (-311, ZD - 200), (-331, ZD)   # (y, z) основания актуатора и конца на закрытой двери
ACT_L0, ACT_STROKE = (20 ** 2 + 200 ** 2) ** 0.5, 100


def door_angle_full():
    """Угол открытия двери при полном ходе актуатора (+100): решение |B - E(θ)| = L0 + 100."""
    import math
    d = ACT_E0[0] - HINGE[0]
    best = None
    for k in range(0, 1800):
        t = math.radians(k / 10)
        ey, ez = HINGE[0] + d * math.cos(t), HINGE[1] + d * math.sin(t)
        L = math.hypot(ey - ACT_B[0], ez - ACT_B[1])
        if L >= ACT_L0 + ACT_STROKE:
            return k / 10
        best = k / 10
    return best


def door_clearance(m, angles=None, verbose=True, tag="door", hinge=None, axis_sign=1):
    """Закон: дверь, открытая на угол θ (по умолчанию - до угла полного хода актуатора), не задевает ничего,
    кроме петель и актуатора. Поворот вокруг оси X через петлю hinge (y, z)."""
    import math
    hinge = hinge or HINGE
    if angles is None:
        a = door_angle_full()
        angles = (a / 3, 2 * a / 3, a)
    parts = m.parts()
    door = [p for p in parts if p.note == tag]
    rest = [p for p in parts if p.note != tag and (p.name in car.BEAMS_ALL or p.name in car.BULKY)
            and not p.name.startswith("61927")]
    bad = []
    for a in angles:
        c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a)) * axis_sign
        R = [[1, 0, 0], [0, c, -s_], [0, s_, c]]
        for p in door:
            dy, dz = p.pos[1] - hinge[0], p.pos[2] - hinge[1]
            if abs(dy) < 1 and abs(dz) < 1:
                continue                     # петля на самой оси поворота: стоит на месте, в стойке - так и задумано
            q = ldr.Part(p.name, p.color, (p.pos[0], hinge[0] + c * dy - s_ * dz, hinge[1] + s_ * dy + c * dz),
                         ldr.mat_mul(R, p.rot))
            for A in car._boxes(q):
                for r in rest:
                    if any(all(min(A[1][k], B[1][k]) - max(A[0][k], B[0][k]) > 3 for k in range(3)) for B in car._boxes(r)):
                        bad.append((round(a), q.name, r.name, [round(v) for v in r.pos]))
    if verbose:
        for b in bad[:8]:
            print("ДВЕРЬ %s %d°: %s задевает %s %s" % ((tag,) + b))
        print("дверь %s: задеваний %d" % (tag, len(bad)))
    return bad


HOOD_H = (-331, -200)      # (y, z) петля капота: дырка гнутой балки лобовой стойки


def hood_clearance(m, verbose=True):
    """Капот открывается вверх вокруг петли HOOD_H до 55° и ничего не задевает."""
    return door_clearance(m, angles=(20, 40, 55), verbose=verbose, tag="hood", hinge=HOOD_H, axis_sign=-1)


def cab_door_clearance(m, verbose=True):
    """Двери кабины поднимаются вверх вокруг петли (y=-211, z=-200) до 80° и ничего не задевают."""
    bad = []
    for s in (1, -1):
        bad += door_clearance(m, angles=(30, 60, 80), verbose=verbose, tag="cabdoor%d" % s, hinge=(-211, -200), axis_sign=1)
    return bad


def hood(m):
    """Капот на петлях: две гнутые 4x6 (x ±120) крестовой дыркой на оси-петле от лобовой стойки (y=-311, z=-200),
    прямой участок вперёд до z=-300, гнутый вниз к носу. Сверху две панели (3x11 и 5x11) на трёх поперечных осях сквозь их каналы - закрывают весь V4. Открывается рукой вверх (Алексей: «капот открываться должен, но лучше не на моторе»)."""
    m.step("Капот: боковины на петлях")
    m.tag = "hood"
    for s in (1, -1):
        side_part(m, "6629.dat", LGREY, (s * 120, HOOD_H[0], -200), FWD, DOWN)
        mount_axle(m, s, -200, HOOD_H[0], 100, 160, (135,))                   # капот 110..130, полувтулка, стойка 140..160
    m.step("Панели капота на поперечных осях: тёмно-серая 3x11 у стекла, чёрная 5x11 над мотором")
    y = HOOD_H[0]
    m.add("15458.dat", DGREY, (0, y, -220))                                     # 3x11: z -250..-190, канал z=-220
    axle(m, 12, BLACK, (0, y, -220), "x")                                       # x -120..120: ось 16 задела бы стойку при открытии
    m.add("64782.dat", BLACK, (0, y, -300))                                     # 5x11: z -350..-250, каналы -320/-300/-280
    axle(m, 16, BLACK, (0, y, -300), "x")
    axle(m, 12, BLACK, (0, y, -280), "x")
    m.tag = ""


def lights(m):
    """Фары: лампы Алексея, приклеенные к кирпичам 1x2, - на шипах передних удлинителей (кирпичи 1x16), светом вперёд.
    Провод ламп - в разъём сверху на блоке батарей 2 (светят, пока блок включён)."""
    m.step("Фары: кирпичи с лампами на шипы передних удлинителей")
    for s in (1, -1):
        m.add("3004.dat", 15, (s * 90, -205, -400), ldr.ry(90), note="фара")   # белые - лампы Алексея


def cab_doors(m):
    """Двери кабины вверх (как у Ламборгини): петля - штифт 3L поперёк в лобовую стойку (z=-200, y=-211), двери в слоях
    x 180..220 снаружи. Рама двери: L 3x5 низ+задняя стойка (слой O2), L 3x5 верх+передняя (O3), продолжение назад -
    L 3x5 (O3) внахлёст. Полудверь 6x3 модуля: z -200..-100, y -251..-211."""
    for s in (1, -1):
        m.sub = "Дверь кабины " + ("правая" if s > 0 else "левая")
        m.tag = "cabdoor%d" % s
        m.step("Рама двери")
        side_part(m, "32526.dat", RED, (s * 190, -211, -200), BACK, UP)    # низ -200..-120, задняя стойка вверх -231,-251
        side_part(m, "32526.dat", YELLOW, (s * 210, -251, -120), FWD, DOWN)  # верх -120..-200, передняя вниз -231,-211
        m.add("2780.dat", BLACK, (s * 200, -251, -120))
        m.step("Продолжение двери назад")
        side_part(m, "32140.dat", BLACK, (s * 210, -211, -160), BACK, UP)    # L 2x4 (O3): крест на -160, низ -140..-100, вверх -231
        for z in (-140, -120):
            m.add("2780.dat", BLACK, (s * 200, -211, z))
        m.tag = ""
        m.sub = ""
        m.step("Поставь дверь кабины: штифт 3L - петля в лобовой стойке")
        m.steps[-1].attach = ["Дверь кабины " + ("правая" if s > 0 else "левая")]
        m.add("6558.dat", BLUE, (s * 190, -211, -200))                          # стойка 160..180 + дверь O2 + O3


def dash(m):
    """Руль: ось-панель 16 поперёк через лобовые стойки (y=-291, z=-200), на ней 6536 (x=-60) дыркой штифта вверх
    вдоль Z, колонка - ось 2, руль - шкив 4185a (3 модуля) на z=-180. Колонка крутится в круглой дырке - руль вертится."""
    m.step("Панель и руль")
    axle(m, 16, BLACK, (0, -271, -200), "x")                                    # x -160..160: дырки балок стоек 140..160
    m.add("6536.dat", BLACK, (-60, -271, -200), ldr.rx(180))                    # дырка штифта вдоль Z на y=-291
    axle(m, 2, BLACK, (-60, -291, -190), "z")                                   # z -210..-170
    m.add("4185a.dat", DGREY, (-60, -291, -180))                                # руль


def seats(m):
    """Сиденья сразу за рулём: L 2x4 на стойках серво (кирпичи 1x12 стоя, x ±40, z=-80), слой x 50..70: спинка
    вверх (-311..-251), сиденье вперёд до z=-100; вторая L 2x4 (серая, x 70..90) - сиденье в 2 модуля шириной.
    Водитель слева - на одной линии с рулём (x=-60..-80)."""
    m.step("Сиденья водителя и пассажира")
    for s in (1, -1):
        side_part(m, "32140.dat", BLUE, (s * 60, -311, -80), DOWN, FWD)     # крест вверху -311, вниз до -251, вперёд -100
        for y in (-271, -251):
            m.add("2780.dat", BLACK, (s * 50, y, -80))
        side_part(m, "32140.dat", LGREY, (s * 80, -311, -80), DOWN, FWD)    # вторая половина: сиденье шириной 2 модуля
        for y in (-311, -291):
            m.add("2780.dat", BLACK, (s * 70, y, -80))


def _unit(v):
    n = sum(c * c for c in v) ** 0.5
    return [c / n for c in v]


def _axle_along(m, n, color, start, d):
    """Ось n модулей от точки start вдоль единичного d (d в плоскости YZ)."""
    a, b = d[1], d[2]
    rot = [[0, 1, 0], [a, 0, b], [b, 0, -a]]                 # столбцы: X->d, Y->X, Z->(0,b,-a)
    rot = [[rot[0][0], rot[0][1], rot[0][2]], [rot[1][0], rot[1][1], rot[1][2]], [rot[2][0], rot[2][1], rot[2][2]]]
    L = n * 20
    c = [start[k] + d[k] * L / 2 for k in range(3)]
    return m.add(car.AXLE[n], color, c, [[0, 1, 0], [a, 0, b], [b, 0, -a]])


def _joiner_at(m, center, d):
    a, b = d[1], d[2]
    return m.add("59443.dat", DGREY, center, [[1, 0, 0], [0, b, a], [0, -a, b]])   # столбцы: X->X, Y->(0,b,-a), Z->d


ROOF_F = (-467, -152)      # (y, z) верх лобовой стойки (крестовая дырка гнутой 4x6)
ROOF_R = (-471, 20)        # (y, z) верх средней стойки кабины (балка 15 / кирпич 1x16)
XC = 190                   # x угловых соединителей крыши


def roof(m):
    """Контур крыши из осей: передняя и задняя поперечины (ось 10 + соединитель + ось 8) сквозь верх стоек,
    боковые линии (ось 16 + соединитель + ось 7) под наклоном, углы - угловые соединители 90° (#6)."""
    m.step("Поперечины крыши: спереди через верх лобовых стоек, сзади через верх задних стоек")
    for (y, z) in (ROOF_F, ROOF_R):
        axle(m, 10, BLACK, (-80, y, z), "x")                                     # x -180..20
        m.add("59443.dat", DGREY, (20, y, z), ldr.ry(90))
        axle(m, 8, BLACK, (100, y, z), "x")                                      # x 20..180
    m.step("Углы крыши и боковые линии")
    d = _unit([0, ROOF_R[0] - ROOF_F[0], ROOF_R[1] - ROOF_F[1]])
    a, b = d[1], d[2]
    for s in (1, -1):
        F = (s * XC, ROOF_F[0], ROOF_F[1])
        R = (s * XC, ROOF_R[0], ROOF_R[1])
        # угол: плечо -Z детали -> к середине (-s по X), плечо -Y -> вдоль линии крыши
        m.add("32014.dat", BLACK, F, [[0, 0, s], [-b * s, -a, 0], [a * s, -b, 0]])
        m.add("32014.dat", BLACK, R, [[0, 0, s], [b * s, a, 0], [-a * s, b, 0]])
        p0 = [F[k] + d[k] * 10 for k in range(3)]
        _axle_along(m, 8, BLACK, p0, d)                                          # крыша кабины: 8 модулей между углами


def build_body(m):
    m.sub = ""
    sides(m)
    fenders(m)
    front_pillars(m)
    trunk_frame(m)
    rear_posts(m)
    trunk_floor(m)
    b_pillars(m)
    hood(m)
    lights(m)
    dash(m)
    cab_doors(m)
    seats(m)
    roof(m)


if __name__ == "__main__":
    import os
    import render
    import inventory
    m = car.build()
    build_body(m)
    bad, groups = car.check(m, verbose=True)
    car.overlaps(m)
    car.beam_overlaps(m)
    car.pin_seating(m)
    car.steer_clearance(m)
    car.hole_sharing(m)
    door_clearance(m)
    cab_door_clearance(m)
    hood_clearance(m)
    print("нехватка:", inventory.shortage(m.parts()) or "нет")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    p = os.path.join(out, "suv_body.ldr")
    ldr.write_mpd(p, m, [car.v4_model()])
    render.collage(p, os.path.join(out, "suv_body.png"))
