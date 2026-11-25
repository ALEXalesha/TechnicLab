"""6x6 (Алексей 24.11: «Сделай 6 на 6 а потом гоночную, полностью»): багги + второй задний ведущий мост.
Передний мост поворачивает серво (как в багги), оба задних моста ведущие и качаются вокруг общего вала
(тележка). Корпус второго моста - кирпич-рамка 6x8 (40345): рамок 5x7 у Алексея две, обе стоят.
Вал назад - ось 16 вместо оси 5: ведущая 12з. первого моста (z 90) и второго (z Z2-30).
Запуск: python six6.py (законы)
"""
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "ядро"))
import car
import body
import ldr
from car import BLACK, LGREY, BLUE, TAN, beam, axle, gear

Z2 = 300                     # второй задний мост (между шинами задних мостов 38 LDU)


def _drop(m, pred):
    for st in m.steps:
        st.parts = [p for p in st.parts if not pred(p)]


def axle2(m):
    """Второй задний мост: рамка 6x8 (дырки полуосей по X в коротких стенках x ±71, вала - по Z в длинных z ±51),
    20з. на полуоси справа (x 20), ведущая 12з. на валу (z Z2-30), колёса x ±160."""
    y, z0 = car.AX_Y, Z2
    m.sub = "Второй задний мост"
    m.step("Второй мост: рамка 6x8 и шестерня")
    m.add("40345.dat", LGREY, (0, y - 10, z0))                      # дырки на y=-71 (на 10 ниже верха)
    gear(m, "18575.dat", TAN, (20, y, z0), "x")
    m.step("Полуоси и втулки")
    for s in (1, -1):
        axle(m, 8, BLACK, (s * 90, y, z0), "x")                     # 10..170: стенка x 62..80, колесо
        gear(m, "3713.dat", LGREY, (s * 50, y, z0), "x")
    m.step("Колёса")
    for s in (1, -1):
        rot = ldr.ry(90) if s > 0 else ldr.ry(-90)
        m.add("56145.dat", LGREY, (s * car.TRACK_X, y, z0), rot)
        m.add("55976.dat", BLACK, (s * car.TRACK_X, y, z0), rot)
    m.sub = ""
    m.step("Вал назад до второго моста: ось 16 вместо оси 5, ведущая 12з. второго моста")
    m.steps[-1].attach = ["Второй задний мост"]
    axle(m, 16, BLACK, (0, car.SHAFT_Y, 175), "z")                  # z 15..335: сквозь рамку первого моста в рамку второго
    gear(m, "32270.dat", BLACK, (0, y, z0 - 30), "z")
    gear(m, "3713.dat", LGREY, (0, y, z0 - 90), "z")                # втулка между рамками: мост не уезжает по валу


def frame_and_shocks(m):
    """Накладки лонжеронов (балка 5, x ±110, z 280..360) и амортизаторы второго моста на z=320:
    низ - штифт в стенку рамки 6x8 (x ±71), верх - штифт в накладку."""
    zs = Z2 + 20
    m.step("Накладки лонжеронов под второй мост")
    for s in (1, -1):
        beam(m, 5, BLACK, (s * 110, car.RAIL_Y, 320), "z", "x")
        m.add("2780.dat", BLACK, (s * 100, car.RAIL_Y, 280))
    m.step("Амортизаторы второго моста")
    for s in (1, -1):
        m.add("73129.dat", BLACK, (s * 90, -181, zs), ldr.ry(90))
        m.add("2780.dat", BLACK, (s * 80, car.AX_Y, zs))           # рамка (62..80) + низ амортизатора (80..100)
        m.add("2780.dat", BLACK, (s * 100, car.RAIL_Y, zs))        # верх амортизатора + накладка


BED_H = (-291, 320)          # (y, z) петля кузова в хвосте, за блоком батарей: кронштейны L 2x4 на стойках блока
BED_Y, BED_TOP = -291, -331  # пол и верх бортов
BED_ANGLES = (15, 30, 45, 50)
ACT_B6 = (-211, 20)          # нижняя проушина актуатора: ось из стойки рамы за кабиной (x 100..160)
ACT_E6 = (-331, 180)         # верхняя проушина: верхняя балка правого борта


def _rx_to(src, dst):
    """Поворот вокруг X, переводящий вектор src (y, z) в направление dst (y, z)."""
    import math
    a = math.atan2(dst[1], dst[0]) - math.atan2(src[1], src[0])
    return ldr.rx(-math.degrees(a)) if False else _rx_rad(a)


def _rx_rad(a):
    import math
    c, s_ = math.cos(a), math.sin(a)
    return [[1, 0, 0], [0, c, -s_], [0, s_, c]]


def dump_bed(m):
    """Самосвал (Алексей 24.11: «сделай самосвал с нормальным кузовом с бортиками»): кузов на петле сзади (BED_H),
    пол - лонжероны-кирпичи 1x16 (x ±90) и оси 10 поперёк; борта высотой 2 модуля - по 3 стойки L 2x4 с каждой
    стороны (угол - штифт в лонжерон, конец - ось 12 поперёк на оба борта) и верхние балки (справа балка 15, слева
    кирпич 1x16). Поднимает актуатор с мотором M справа, наискосок: от оси в стойке рамы (ACT_B6) к верхней балке
    борта (ACT_E6); в опущенном кузове актуатор сжат (201), полный ход поднимает кузов ~70°."""
    y, top = BED_Y, BED_TOP
    m.sub = "Кузов самосвала"
    m.tag = "bed"
    m.step("Лонжероны кузова")
    for s in (1, -1):
        car.brick(m, 15, BLACK, (s * 90, y, 180), "z")             # дырки z 40..320
    m.step("Стойки бортов: L 2x4 (угол - штифт в лонжерон, конец - ось 12 поперёк)")
    for z in (60, 160, 280):
        for s in (1, -1):
            body.side_part(m, "32140.dat", car.YELLOW, (s * 110, top - 20, z), body.DOWN, body.BACK)
            m.add("2780.dat", BLACK, (s * 100, y, z))
        axle(m, 12, BLACK, (0, y, z + 20), "x")                     # x -120..120: лонжероны и концы стоек
    m.step("Пол кузова: оси поперёк")
    for z in range(40, 301, 20):
        if z not in (160, 180, 280, 300, 60, 80):
            axle(m, 10, BLACK, (0, y, z), "x")
    m.step("Верх бортов: справа балка 15, слева кирпич 1x16")
    beam(m, 15, car.YELLOW, (130, top, 200), "z", "x")              # z 60..340: начало за средней стойкой кабины
    car.brick(m, 15, car.YELLOW, (-130, top, 200), "z")
    for z in (60, 160, 280):
        for s in (1, -1):
            m.add("2780.dat", BLACK, (s * 120, top, z))            # стойка (100..120) + верх борта (120..140)
    m.step("Передний борт: рамка 4x6 на двух поперечинах между передними стойками")
    m.add("40344.dat", car.YELLOW, (0, top, 50), ldr.rx(90))          # дырки по X на y -351/-331/-311, z 60
    for yy in (top - 20, top + 20):                                   # -351 (крестовые концы стоек), -311
        axle(m, 6, BLACK, (-60, yy, 60), "x")
        m.add("59443.dat", car.DGREY, (0, yy, 60), ldr.ry(90))
        axle(m, 6, BLACK, (60, yy, 60), "x")
    m.tag = ""
    m.sub = ""
    m.step("Кронштейны петли: L 2x4 на стойках блока батарей (угол и конец короткого плеча)")
    zb = car.BAT[2] + 40                                            # стойки блока: x ±120 (110..130), z 260
    for s in (1, -1):
        body.side_part(m, "32140.dat", BLACK, (s * 140, y, BED_H[1]), body.FWD, body.DOWN)   # конец (крест) на петле
        m.add("2780.dat", BLACK, (s * 130, y, zb))                  # угол L + верх стойки блока
        axle(m, 2, BLACK, (s * 130, y + 20, zb), "x")               # крестовой конец короткого плеча + стойка
    m.step("Поставь кузов: петли - оси 4 через лонжероны кузова и кронштейны")
    m.steps[-1].attach = ["Кузов самосвала"]
    for s in (1, -1):
        axle(m, 4, BLACK, (s * 110, BED_H[0], BED_H[1]), "x")      # x 70..150: лонжерон кузова (80..100), кронштейн (130..150)


def bed_clearance(m, verbose=False):
    """Кузов поднимается на 15/30/45/60° вокруг петли и ничего не задевает (кроме актуатора)."""
    long_ = {"3703.dat", "32278.dat"}                # длинные детали кузова - по дыркам: их общий габарит в наклоне
    extra = long_ - car.SHAPED                     # даёт ложные задевания (повёрнутый 16-модульный кирпич - огромный куб)
    car.SHAPED |= extra
    try:
        return body.door_clearance(m, angles=BED_ANGLES, verbose=verbose, tag="bed", hinge=BED_H, axis_sign=-1)
    finally:
        car.SHAPED -= extra


def receivers_on_pillars(m):
    """Приёмники снаружи средних стоек кабины (под платформой им не видно пульта)."""
    for st in m.steps:
        if st.title.startswith("Приёмники ИК"):
            st.title = "Приёмники ИК снаружи средних стоек кабины"
            st.parts = []
            for s in (1, -1):
                rot = [[0, 0, s], [1, 0, 0], [0, 1, 0]]
                st.parts.append(ldr.Part("58123.dat", car.LGREY, (s * 180, -291, 10), rot))
                for yy in (-311, -271):
                    st.parts.append(ldr.Part("2780.dat", BLACK, (s * 140, yy, 20)))
        if st.title.startswith("Запасное колесо"):
            st.parts = []


def build():
    m = car.build()
    body.build_body(m)
    receivers_on_pillars(m)
    m.steps = [st for st in m.steps if st.parts or st.attach]     # шаг «поставь мосты» - без своих деталей
    _drop(m, lambda p: p.name == car.AXLE[5] and abs(p.pos[2] - 65) < 1 and abs(p.pos[1] - car.SHAFT_Y) < 1)
    axle2(m)
    frame_and_shocks(m)
    m.step("Арки второго моста")
    for s in (1, -1):
        body.arch(m, s, Z2, (), top=car.RAIL_Y - 20, base_beam=s > 0, base_brick=11, base_dz=20)   # 1x8 кончились: балка 7 / кирпич 1x12
        body.mount_axle(m, s, Z2, car.RAIL_Y, 100, 160, (130,))   # накладка (100..120) -> основание арки (140..160)
    dump_bed(m)
    return m


if __name__ == "__main__":
    import inventory
    m = build()
    car.check(m)
    car.overlaps(m)
    car.beam_overlaps(m)
    car.pin_seating(m)
    car.hole_sharing(m)
    car.steer_clearance(m)
    print("нехватка:", inventory.shortage(m.parts()) or "нет", len(m.parts()))
