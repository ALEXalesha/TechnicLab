"""Гоночная (Алексей 24.11: «а потом гоночную, полностью»; шины 2,3 x 4,3 см = 44309 на дисках 56904).
Основа - багги (рулевое серво, каркас, сиденья, руль от моста, блок батарей лёжа, V8 открыт), но:
- привод только задний: мотор L лежит вдоль машины низко между мостами (ось y -71), выход назад прямо в вал;
- задний мост - кирпич-рамка 6x8 (40345): в её проём влезает ПОВЫШАЮЩАЯ пара 20з. (вал) -> 12з. (полуось) = x1,67
  (в рамку 5x7 не влезала); мост жёстко на 4 подвесах (балки 7) к лонжеронам;
- нет XL, центрального дифференциала, переднего вала, лебёдки, запаски; передний мост без шестерён (только рулит).
Скорость: L ~390 об/мин без нагрузки x1,67 = ~650 об/мин колеса 43 мм -> ~1,4 м/с (~5 км/ч), багги ~1 км/ч.
Запуск: python race.py (законы)
"""
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "ядро"))
import car
import body
import ldr
from car import BLACK, LGREY, BLUE, TAN, beam, axle, gear

RZ = car.AXLE_Z              # задний мост там же, где у багги
LZ = RZ - 60                 # лицо мотора L (выход назад) вплотную к длинной стенке рамки 6x8 (z RZ-51)
WHEEL_R = 54                 # шина 44309: диаметр 108 LDU = 43 мм
GROUND_Y = car.AX_Y + WHEEL_R

DROP_STEPS = (
    "Мотор XL: ось 4", "Стойки и поперечные оси опор вала", "Центральный дифференциал", "Амортизаторы",
    "Втулка: мост не уезжает", "Мотор L и стойки", "Червяк на выходе", "Нижние балки и направляющая",
    "Поставь лебёдку", "Барабан:", "Трос:", "Запасное колесо",
    "Углы крыши и боковые линии",                       # обтекаемая: крыши нет - лобовая рамка и дуга за сиденьями
)


def _strip(m):
    keep = []
    for st in m.steps:
        if st.sub == "Задний мост" or any(st.title.startswith(t) for t in DROP_STEPS):
            continue
        if st.sub == "Передний мост" and st.title.startswith(("Мост передний", "Ведущая")):
            st.parts = [p for p in st.parts if p.name == "64179.dat"]      # рамка остаётся, шестерни - нет
            st.title = "Мост передний: рамка (без привода)"
        if st.title.startswith("Поставь оба моста"):     # задний мост у гоночной свой (ставится позже)
            st.attach = ["Передний мост"]
            st.title = "Поставь передний мост"
        if st.title.startswith("Мотор XL и лонжероны"):
            st.parts = [p for p in st.parts if p.name != "58121c01.dat" and not (p.name == "6558.dat" and abs(abs(p.pos[0]) - 60) < 1)]
            st.title = "Лонжероны"
        keep.append(st)
    m.steps = keep
    for p in m.parts():                                                  # низкие шины Алексея
        if p.name == "55976.dat":
            p.name = "44309.dat"
        elif p.name == "56145.dat":
            p.name = "56904.dat"
    m.steps[0].attach = []
    # стойки рамы - балки 5 (y -251..-171): верхние лонжероны держали XL - их нет, балки 7 нужны подвесам моста
    for st in m.steps:
        if st.title.startswith("Стойки: верхний лонжерон"):
            st.parts = [p for p in st.parts if not (p.name == "6558.dat" and abs(p.pos[1] + 271) < 1)]
            for p in st.parts:
                if p.name == car.BEAM[7]:
                    p.name, p.pos = car.BEAM[5], (p.pos[0], -211, p.pos[2])
            st.title = "Стойки рамы (под средние стойки кабины)"
        if st.title == "Лонжероны":
            st.parts = [p for p in st.parts if not (p.name == car.BEAM[5] and abs(p.pos[1] + 271) < 1)]
        if st.title.startswith("Стойки батарейного блока"):
            for p in st.parts:
                if p.name == car.BEAM[7]:
                    p.name, p.pos = car.BEAM[5], (p.pos[0], -211, p.pos[2])
        if st.title.startswith("Приёмники ИК"):
            st.parts = []
            st.title = "Приёмники ИК снаружи средних стоек кабины"
            for s in (1, -1):
                rot = [[0, 0, s], [1, 0, 0], [0, 1, 0]]
                st.parts.append(ldr.Part("58123.dat", car.LGREY, (s * 180, -291, 10), rot))
                for y in (-311, -271):
                    st.parts.append(ldr.Part("2780.dat", BLACK, (s * 140, y, 20)))


def rear_axle(m):
    """Задний мост: рамка 6x8, полуоси (оси 8) сквозь короткие стенки x ±71; 12з. кон. на правой полуоси (x 30),
    20з. кон. на валу (z RZ-20) - повышающая пара; колёса на x ±160."""
    y, z0 = car.AX_Y, RZ
    m.sub = "Задний мост"
    m.step("Задний мост: рамка 6x8 и полуоси")
    m.add("40345.dat", LGREY, (0, y - 10, z0))
    for s in (1, -1):
        axle(m, 8, BLACK, (s * 90, y, z0), "x")
        gear(m, "3713.dat", LGREY, (s * 50, y, z0), "x")
    gear(m, "32270.dat", BLACK, (30, y, z0), "x")                    # 12з. на полуоси: 30 от оси вала
    m.step("Колёса")
    for s in (1, -1):
        rot = ldr.ry(90) if s > 0 else ldr.ry(-90)
        m.add("56904.dat", BLACK, (s * car.TRACK_X, y, z0), rot)
        m.add("44309.dat", BLACK, (s * car.TRACK_X, y, z0), rot)
    m.sub = ""
    m.step("Поставь задний мост: 4 подвеса (балки 7) от лонжеронов к стенкам рамки")
    m.steps[-1].attach = ["Задний мост"]
    for s in (1, -1):
        for z in (z0 - 20, z0 + 20):
            beam(m, 7, BLACK, (s * 50, -131, z), "y", "x")           # y -191..-71, внутри проёма рамки
            if z == z0 + 20:                                         # здесь же штифт лонжерон-удлинитель: один 3L на троих
                m.add("6558.dat", BLUE, (s * 70, car.RAIL_Y, z))
            else:
                m.add("2780.dat", BLACK, (s * 60, car.RAIL_Y, z))  # подвес + лонжерон (x 60..80)
            m.add("2780.dat", BLACK, (s * 60, y, z))               # подвес + стенка рамки 6x8


def motor(m):
    """Мотор L вдоль машины на высоте вала: лицо на z LZ вплотную к длинной стенке рамки 6x8, два штифта из лица
    (x ±20) в её дырки по Z + вал сквозь среднюю дырку; корпус вперёд до LZ-140 (просвет ~14 LDU)."""
    y = car.AX_Y
    m.step("Мотор L лёжа: лицом к рамке моста, вал назад, 20з. кон.")
    m.add("99499.dat", LGREY, (0, y, LZ), ldr.ry(180))              # выход смотрит назад (+Z)
    for x in (-20, 20):
        m.add("2780.dat", BLACK, (x, y, LZ), ldr.ry(90))            # лицо мотора + стенка рамки
    axle(m, 4, BLACK, (0, y, RZ - 40), "z")                         # z RZ-80 .. RZ: мотор -> стенка -> 20з.
    gear(m, "18575.dat", TAN, (0, y, RZ - 20), "z")


def build():
    bat = car.BAT
    car.BAT = (bat[0], bat[1], bat[2] + 20)            # блок на модуль назад: перед ним задний подвес моста
    try:
        m = car.build()
        body.build_body(m)
    finally:
        car.BAT = bat
    _strip(m)
    for st in m.steps:                                 # арки на модуль ниже: колёса 43 мм, верх шины y -125
        if st.title.startswith("Арка "):
            for p in st.parts:
                if p.name == "32526.dat" or (p.name == "2780.dat" and abs(abs(p.pos[0]) - 180) < 1):
                    p.pos = (p.pos[0], p.pos[1] + 20, p.pos[2])
    for st in m.steps:                                 # штифт лонжерон-удлинитель на z 140 заменит 3L подвеса
        if st.title.startswith("Удлинители лонжеронов"):
            st.parts = [p for p in st.parts if not (p.name == "2780.dat" and abs(p.pos[2] - (RZ + 20)) < 1)]
    for st in m.steps:
        if st.title.startswith("Поперечины крыши"):
            st.title = "Верх лобовой рамки и дуга безопасности за сиденьями"
    hinge = body.HOOD_H
    body.HOOD_H = (-311, -200)                         # у низкой лобовой рамки петля - дырка гнутой балки на -311
    try:
        body.hood(m)                                   # капот из панелей 3x11 и 5x11 закрывает V8: нос клином
    finally:
        body.HOOD_H = hinge
    rear_axle(m)
    motor(m)
    return m


def hood_clearance(m):
    """Капот гоночной (петля на -311) открывается до 55° без задеваний."""
    hinge = body.HOOD_H
    body.HOOD_H = (-311, -200)
    try:
        return body.hood_clearance(m, verbose=False)
    finally:
        body.HOOD_H = hinge


def ground_clearance(m):
    """Просвет: от низа самой низкой детали (кроме шин) до земли, LDU."""
    low = max(car._bbox(p)[1][1] for p in m.parts() if car._bbox(p) and p.name not in ("44309.dat", "56904.dat"))
    return GROUND_Y - low


if __name__ == "__main__":
    import inventory
    import mass
    m = build()
    car.check(m)
    car.overlaps(m)
    car.beam_overlaps(m)
    car.pin_seating(m)
    car.hole_sharing(m)
    car.steer_clearance(m)
    print("нехватка:", inventory.shortage(m.parts()) or "нет", len(m.parts()), "просвет", ground_clearance(m))
    t, x, y, z = mass.cg(m.parts())
    print("масса ~%.0f г, ЦТ %.1f мм над землёй" % (t, (GROUND_Y - y) * 0.4))
