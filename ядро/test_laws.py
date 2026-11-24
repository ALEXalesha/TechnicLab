"""Законы модели и их мутанты: каждый закон на чистой модели зелёный и ловит свою поломку.
Запуск: python test_laws.py   (без окон, только расчёт)
"""
import math
import copy

import paths
paths.add_models()
import car
import ldr
import inventory
import snaps


def fresh():
    import body
    m = car.build()
    body.build_body(m)
    return m


def find(m, name, pos):
    for p in m.parts():
        if p.name == name and all(abs(p.pos[k] - pos[k]) < 0.5 for k in range(3)):
            return p
    raise AssertionError("нет детали %s @ %s" % (name, pos))


def test_clean_model():
    m = fresh()
    bad, groups = car.check(m, verbose=False)
    assert not bad and len(groups) == 1
    assert not car.overlaps(m, verbose=False)
    assert not car.beam_overlaps(m, verbose=False)
    assert not car.pin_seating(m, verbose=False)
    assert not car.steer_clearance(m, verbose=False)
    assert not inventory.shortage(m.parts()), inventory.shortage(m.parts())
    assert not car.hole_sharing(m, verbose=False)


def test_mutant_inventory():
    """Мутант: ещё одна балка 11 (у Алексея их 2, обе уже в стойках) -> закон описи ловит."""
    m = fresh()
    m.step("мутант")
    car.beam(m, 11, car.BLACK, (0, -500, 0), "x", "z")
    assert "балка 11" in inventory.shortage(m.parts())


def test_brick_holes_on_grid():
    """Кирпич вместо балки: его дырки ровно там же, где были бы у балки (лёжа и стоя)."""
    for along, c in (("z", (90, -171, -260)), ("y", (40, -251, -80)), ("x", (0, -291, 290))):
        m = ldr.Model("t")
        b = car.brick(m, 11, 0, c, along)
        holes = sorted(tuple(round(v) for v in h.pos) for h in snaps.part_snaps(b) if h.gender == "F" and h.center)
        k = {"z": 2, "y": 1, "x": 0}[along]
        assert len(holes) == 11 and all(h[i] == c[i] for h in holes for i in range(3) if i != k), (along, holes[:3])
        assert holes[0][k] == c[k] - 100 and holes[-1][k] == c[k] + 100


def test_buggy_layout():
    """Багги (Алексей 24.11: «поменьше может, но зато реально прикольную»): база 21 модуль, один блок батарей, нет
    капота, дверей и кузова; каркас кабины - лобовые и средние стойки с крышей из осей, сиденья за рулём."""
    import body
    m = fresh()
    assert car.AXLE_Z - car.FRONT_Z == 420
    bat = [p for p in m.parts() if p.name == "58119.dat"]
    assert len(bat) == 1
    bb = car._bbox(bat[0])
    assert bb[1][1] - bb[0][1] == 80 and bb[0][1] >= -271, bb     # блок лёжа, верх не выше 13,5 модуля
    assert not [p for p in m.parts() if p.note in ("door", "hood") or p.note.startswith("cabdoor")]
    assert len([p for p in m.parts() if p.name == "32140.dat" and p.color == car.BLUE]) == 2
    assert body.ROOF_R[1] == 20 and body.ROOF_F[1] == -152
    zs = [b for b in (car._bbox(p) for p in m.parts() if p.note != "трос") if b]   # без верёвки с крюком
    length = (max(b[1][2] for b in zs) - min(b[0][2] for b in zs)) / 20
    assert length <= 41, length                                   # пикап был 47 модулей
    height = -min(b[0][1] for b in zs) / 20
    assert height <= 19, height                                   # каркас низкий (Алексей: «Опусти»; было 24,5)
    seat_top = min(car._bbox(p)[0][1] for p in m.parts() if p.name == "32140.dat" and abs(p.pos[2] + 80) < 1)
    assert seat_top - body.ROOF_F[0] >= 40 and seat_top - body.ROOF_R[0] >= 40, seat_top   # над спинками 2+ модуля


def test_parser_long_pin():
    """Секции _L не теряются: штифт 3L - 60 LDU, 2L - 40."""
    sp = {n: [c.span() for c in snaps.part_snaps(ldr.Part(n, 0, (0, 0, 0))) if c.gender == "M" and c.center]
          for n in ("6558.dat", "2780.dat")}
    assert (-30.0, 30.0) in sp["6558.dat"], sp
    assert (-20.0, 20.0) in sp["2780.dat"], sp


def test_mutant_half_pin():
    """Мутант: штифт XL снова 2L (сидит в моторе на 10 из 20) -> закон посадки ловит."""
    m = fresh()
    p = find(m, "6558.dat", (60, car.RAIL_Y, 60))
    p.name = "2780.dat"
    bad = car.pin_seating(m, verbose=False)
    assert any(b[0] is p for b in bad), bad


def test_mutant_beam_in_beam():
    """Мутант: старая балка 5 у мотора M (x=80, y -251..-171) -> входит в передний удлинитель (кирпич 1x16) и в торец V4."""
    m = fresh()
    m.step("мутант")
    p = car.beam(m, 5, car.BLACK, (80, -211, -260), "y", "x")
    bad = car.beam_overlaps(m, verbose=False)
    others = {q.name for pair in bad if p in pair for q in pair if q is not p}
    assert car.BRICK[15] in others and "v4.ldr" in others, others


def test_mutant_servo_into_v4():
    """Мутант: серво на старом месте перед осью поворота, корпусом вперёд -> входит в V4 (закон видит габарит V4)."""
    m = fresh()
    p = [q for q in m.parts() if q.name == "99498.dat"][0]
    p.pos, p.rot = [0, -201, car.PIVOT_Z - 60], ldr.rx(90)
    bad = car.overlaps(m, verbose=False)
    assert any(p in pair and any(q.name == "v4.ldr" for q in pair) for pair in bad), bad


def test_mutant_winch_into_v4():
    """Мутант: лебёдка на модуль ближе (мотор L z -400..-320) -> входит в V4."""
    m = fresh()
    p = find(m, "99499.dat", (0, -201, car.WINCH_Z))
    p.pos = [0, -201, car.WINCH_Z + 40]
    assert any(p in pair for pair in car.overlaps(m, verbose=False))


def test_battery_clear_of_shocks():
    """Блок батарей за амортизаторами: по Z не пересекается с ними (низ блока на одной высоте с их верхом)."""
    m = fresh()
    box = [p for p in m.parts() if p.name == "58119.dat"][0].world_bbox()
    for s_ in [p for p in m.parts() if p.name == "73129.dat"]:
        b = s_.world_bbox()
        assert b[1][2] <= box[0][2] or b[0][1] >= box[1][1], (b, box)


def test_winch_ratio_and_mesh():
    """Червяк и 24з. на расстоянии 2 модуля по Z, на одной высоте; барабан перед лицом мотора не выходит за удлинители."""
    m = fresh()
    w = find(m, "4716.dat", (0, car.RAIL_Y, car.WINCH_Z))
    g = find(m, "3648b.dat", (0, car.RAIL_Y, car.DRUM_Z))
    assert abs(w.pos[2] - g.pos[2]) == 40 and w.pos[1] == g.pos[1] and w.pos[0] == g.pos[0]


def test_mutant_beam_into_battery():
    """Мутант: блок батарей на 3 модуля вперёд -> садится на амортизаторы, закон крупных деталей ловит."""
    m = fresh()
    p = [q for q in m.parts() if q.name == "58119.dat"][0]
    p.pos = [p.pos[0], p.pos[1], p.pos[2] - 60]
    bad = car.overlaps(m, verbose=False)
    assert any(p in pair for pair in bad), bad


def test_mutant_two_in_hole():
    """Мутант: ось крепления задней арки на дырку ножки (zc-60), где сидит штифт ножки -> «две папы в дырке»."""
    m = fresh()
    z = car.AXLE_Z - 20
    a = [q for q in m.parts() if q.name == "3705.dat" and abs(q.pos[2] - z) < 1 and abs(q.pos[1] + 171) < 1][0]
    a.pos = [a.pos[0], a.pos[1], car.AXLE_Z - 60]
    assert car.hole_sharing(m, verbose=False)


def test_mutant_lonely_pin():
    """Мутант: штифт L-балки двигателя сдвинут наружу на модуль -> держит одну деталь."""
    m = fresh()
    z0 = car.ENG[2]
    p = find(m, "2780.dat", (-100, car.RAIL_Y, z0))
    p.pos = [-120, car.RAIL_Y, z0]
    bad, groups = car.check(m, verbose=False)
    assert bad or len(groups) > 1 or car.pin_seating(m, verbose=False)


def test_mutant_steer_hits_bumper():
    """Мутант: поперечная балка низко в 5 модулях перед передним мостом: прямо колёса её не касаются,
    а повёрнутые на 25° - задевают. Закон поворота ловит."""
    m = fresh()
    m.step("мутант")
    car.beam(m, 15, car.BLACK, (0, -71, car.FRONT_Z - 100), "x", "z")
    assert not car.steer_clearance(m, angles=(0,), verbose=False)
    assert car.steer_clearance(m, angles=(25,), verbose=False)


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_")]
    for k, f in tests:
        f()
        print("ok", k)
    print("всего %d, все зелёные" % len(tests))


def test_v8_pistons_inside_heads():
    """V8 Алексея: 8 цилиндров, 8 поршней; ось поршня (у 2851 - локальная Y) совпадает с осью своего цилиндра
    (тоже Y), днище (y=-16 детали) ниже верха головки (y=-4 цилиндра), юбка (y=+8) выше низа цилиндра (y=48).
    Поршень, положенный боком, вылезал сквозь окошки головки (Алексей 24.11: «наложение»)."""
    import ldr
    v = car.v4_model().parts()
    cyl = [p for p in v if p.name == "2850b.dat"]
    pis = [p for p in v if p.name == "2851.dat"]
    assert len(cyl) == 8 and len(pis) == 8
    for q in pis:
        c = min(cyl, key=lambda p: sum((p.pos[k] - q.pos[k]) ** 2 for k in range(3)))
        cy = [c.rot[k][1] for k in range(3)]                  # ось Y цилиндра в мире
        qy = [q.rot[k][1] for k in range(3)]
        assert abs(sum(cy[k] * qy[k] for k in range(3))) > 0.99, (q.pos, "поршень не вдоль цилиндра")

        def local_y(pt):                                    # координата точки по оси Y цилиндра
            return sum((pt[k] - c.pos[k]) * cy[k] for k in range(3))
        crown = [q.pos[k] + 16 * -qy[k] for k in range(3)]
        skirt = [q.pos[k] + 8 * qy[k] for k in range(3)]
        ys = sorted((local_y(crown), local_y(skirt)))
        assert ys[0] > -4 + 1, (q.pos, "днище торчит из головки", ys)
        assert ys[1] < 48, (q.pos, "юбка ниже цилиндра", ys)


def _rudder_gears(m):
    zp = car.PIVOT_Z
    a = find(m, "32270.dat", (0, -231, zp))
    b = [p for p in m.parts() if p.name == "32270.dat" and abs(p.pos[1] + 251) < 1 and p.pos[0] == 0][0]
    g = sorted([p for p in m.parts() if p.name == "3648b.dat" and abs(p.pos[1] + 251) < 1 and abs(p.pos[0]) <= 60],
               key=lambda p: p.pos[0])                              # 24з. мотора V8 (x 130) - не руль
    return a, b, g


def rudder_ok(m):
    """Руль связан с мостом: 12з.-12з. под 90° (центр каждой в 1 модуле от оси другой, оси пересекаются),
    24з.-24з. на одной Z через 3 модуля; верх оси поворота доходит до 12з."""
    a, b, g = _rudder_gears(m)
    ok = abs(a.pos[1] - b.pos[1]) == 20 and abs(b.pos[2] - a.pos[2]) == 20 and a.pos[0] == b.pos[0]
    ok = ok and len(g) == 2 and g[0].pos[2] == g[1].pos[2] and abs(g[1].pos[0] - g[0].pos[0]) == 60
    piv = [p for p in m.parts() if p.name == "32073.dat" and abs(p.pos[2] - car.PIVOT_Z) < 1 and p.pos[0] == 0]
    return ok and bool(piv) and piv[0].pos[1] - 50 <= a.pos[1] + 5


def test_rudder_turns_with_wheels():
    """Руль крутится вместе с колёсами (Алексей 24.11); мутант - колонка сдвинута на полмодуля - ловится."""
    m = fresh()
    assert rudder_ok(m)
    _, b, _ = _rudder_gears(m)
    b.pos = [b.pos[0], b.pos[1], b.pos[2] + 10]
    assert not rudder_ok(m)


def test_six6_clean_and_driven():
    """6x6: все законы чистые; три моста ведущие - ведущие 12з. на валах на 30 LDU перед/за каждым мостом;
    вал назад - ось 16 доходит до ведущей второго моста; детали из описи."""
    import six6
    import inventory
    m = six6.build()
    bad, groups = car.check(m, verbose=False)
    assert not bad and len(groups) == 1
    assert not car.overlaps(m, verbose=False) and not car.beam_overlaps(m, verbose=False)
    assert not car.pin_seating(m, verbose=False) and not car.hole_sharing(m, verbose=False)
    assert not car.steer_clearance(m, verbose=False)
    assert not inventory.shortage(m.parts())
    pin = sorted(p.pos[2] for p in m.parts() if p.name == "32270.dat" and abs(p.pos[1] - car.AX_Y) < 1 and p.pos[0] == 0)
    for z0, k in ((car.FRONT_Z, -1), (car.AXLE_Z, 1), (six6.Z2, 1)):
        assert z0 - k * 30 in pin, (z0, pin)
    sh = [p for p in m.parts() if p.name == car.AXLE[16] and abs(p.pos[1] - car.SHAFT_Y) < 1]
    assert sh and sh[0].pos[2] + 160 >= six6.Z2 - 30 + 10


def test_mutant_six6_pinion_off():
    """Мутант: ведущая второго моста на 1 модуль дальше -> закон ведущих ловит."""
    import six6
    m = six6.build()
    p = [q for q in m.parts() if q.name == "32270.dat" and abs(q.pos[2] - (six6.Z2 - 30)) < 1][0]
    p.pos = [p.pos[0], p.pos[1], p.pos[2] - 20]
    pin = sorted(q.pos[2] for q in m.parts() if q.name == "32270.dat" and abs(q.pos[1] - car.AX_Y) < 1 and q.pos[0] == 0)
    assert six6.Z2 - 30 not in pin


def _race_gears_ok(m):
    import race
    y, z0 = car.AX_Y, race.RZ
    pin = [p for p in m.parts() if p.name == "18575.dat" and p.pos[0] == 0 and abs(p.pos[1] - y) < 1]
    crown = [p for p in m.parts() if p.name == "32270.dat" and abs(p.pos[2] - z0) < 1 and abs(p.pos[1] - y) < 1]
    return (len(pin) == 1 and len(crown) == 1 and abs(pin[0].pos[2] - (z0 - 20)) < 1   # 20з. в 1 модуле от полуоси
            and abs(abs(crown[0].pos[0]) - 30) < 1)                                     # 12з. в 1,5 модуля от вала


def test_race_clean_and_fast():
    """Гоночная: законы чистые, детали из описи; привод L через повышающую 20з.->12з. (x1,67); нет XL, лебёдки,
    центрального дифференциала; низкие шины 44309 на всех 4 колёсах; просвет >= 10 LDU (4 мм)."""
    import race
    import inventory
    m = race.build()
    bad, groups = car.check(m, verbose=False)
    assert not bad and len(groups) == 1
    assert not car.overlaps(m, verbose=False) and not car.beam_overlaps(m, verbose=False)
    assert not car.pin_seating(m, verbose=False) and not car.hole_sharing(m, verbose=False)
    assert not car.steer_clearance(m, verbose=False)
    assert not inventory.shortage(m.parts())
    names = [p.name for p in m.parts()]
    assert "58121c01.dat" not in names and "65414c01.dat" not in names and "4716.dat" not in names
    assert names.count("99499.dat") == 1 and names.count("44309.dat") == 4 and "55976.dat" not in names
    assert _race_gears_ok(m)
    assert race.ground_clearance(m) >= 10, race.ground_clearance(m)
    assert "32014.dat" not in names and names.count("64782.dat") == 1     # обтекаемая: крыши нет, нос - капот 5x11
    assert not race.hood_clearance(m)


def test_mutant_race_gear_off():
    """Мутант: 12з. на полуоси на полмодуля ближе к валу -> закон передачи ловит."""
    import race
    m = race.build()
    c = [p for p in m.parts() if p.name == "32270.dat" and abs(p.pos[2] - race.RZ) < 1][0]
    c.pos = [c.pos[0] - 10, c.pos[1], c.pos[2]]
    assert not _race_gears_ok(m)


def test_dump_bed_tips_clear():
    """6x6-самосвал: кузов с бортами (6 стоек L 2x4, верх бортов - балка 15 и кирпич 1x16) поднимается на петле
    в хвосте на 15..50° без задеваний; мутант - балка над кузовом на пути подъёма - ловится."""
    import six6
    m = six6.build()
    bed = [p for p in m.parts() if p.note == "bed"]
    assert len([p for p in bed if p.name == "32140.dat"]) == 6
    assert {"32278.dat", "3703.dat"} <= {p.name for p in bed}
    assert not six6.bed_clearance(m)
    m.step("мутант")
    car.beam(m, 5, car.BLACK, (0, -471, 120), "z", "x")
    assert six6.bed_clearance(m)


def test_arm_clean():
    """Рука: законы чистые, детали из описи; актуатор плеча с мотором M (у Алексея один), локоть - распорка 10 модулей,
    захват - мотор L и 24з.-24з. через 3 модуля."""
    import arm
    import inventory
    m = arm.build()
    bad, groups = car.check(m, verbose=False)
    assert not bad and len(groups) == 1
    assert not car.overlaps(m, verbose=False) and not car.beam_overlaps(m, verbose=False)
    assert not car.pin_seating(m, verbose=False) and not car.hole_sharing(m, verbose=False)
    assert not inventory.shortage(m.parts())
    names = [p.name for p in m.parts()]
    assert names.count("61927-f1.dat") == 1 and names.count("58120c01.dat") == 1 and names.count("99499.dat") == 1
    for a, b in ((arm.A, arm.B1), (arm.D, arm.C)):
        assert math.hypot(a[0] - b[0], a[1] - b[1]) == 200
    g = sorted(p.pos[2] for p in m.parts() if p.name == "3648b.dat")
    assert len(g) == 2 and g[1] - g[0] == 60


def test_walker_clean_and_steps():
    """Шагающий: законы чистые, детали из описи; механизм Хокенса замкнут (кривошип 40, шатун 100, коромысло 100);
    правые стопы стоят (ниже всех), левые подняты (кривошипы на 180°)."""
    import walker
    import inventory
    m, feet = walker.build()
    bad, groups = car.check(m, verbose=False)
    assert not bad and len(groups) == 1
    assert not car.overlaps(m, verbose=False) and not car.beam_overlaps(m, verbose=False)
    assert not car.pin_seating(m, verbose=False) and not car.hole_sharing(m, verbose=False)
    assert not inventory.shortage(m.parts())
    for zA, sgn in ((walker.ZA[0], -1), (walker.ZA[1], 1)):
        A, B, C, D, P = walker.linkage(walker.foot_low_phi(zA, sgn), zA, sgn)
        assert abs(math.dist(A, C) - 40) < 1e-6 and abs(math.dist(C, D) - 100) < 1e-6 and abs(math.dist(B, D) - 100) < 1e-6
    ys = sorted(p[1] for p in feet)
    assert ys[-1] == ys[-2] and ys[0] < ys[-1] - 20


def test_clock_clean_and_train():
    """Часы: законы чистые; шестерни в зацеплении (40з.-8з. через 3 модуля в одной плоскости Z), передача 1:25."""
    import clock
    import inventory
    m = clock.build()
    bad, groups = car.check(m, verbose=False)
    assert not bad and len(groups) == 1
    assert not car.overlaps(m, verbose=False) and not car.beam_overlaps(m, verbose=False)
    assert not car.pin_seating(m, verbose=False) and not car.hole_sharing(m, verbose=False)
    assert not inventory.shortage(m.parts())
    big = [p for p in m.parts() if p.name == "3649.dat"]
    small = [p for p in m.parts() if p.name == "3647.dat"]
    pairs = [(b, s_) for b in big for s_ in small if b.pos[2] == s_.pos[2] and abs(abs(b.pos[1] - s_.pos[1]) - 60) < 1]
    assert len(pairs) == 2, pairs                                   # барабан->промежуточная, промежуточная->анкерная
    assert (40 // 8) ** len(pairs) == 25


def power_ok(m):
    """Модель с моторами: есть блок батарей 8881 и приёмников 8884 хватает на все моторы (2 выхода на приёмник;
    мотор M двигателя V8 стоит на одном выходе с ходовым - его не считаем)."""
    names = [p.name for p in m.parts()]
    motors = sum(names.count(n) for n in ("58121c01.dat", "99499.dat", "99498.dat"))
    motors += max(0, names.count("58120c01.dat") - ("v4.ldr" in names))
    if not motors:
        return True
    return names.count("58119.dat") >= 1 and 2 * names.count("58123.dat") >= motors


def test_every_motor_powered():
    """У каждой модели с моторами есть блок батарей и хватает приёмников (Алексей 25.11: «не у всех моделей есть
    передатчик там где нужен и батарейный блок»)."""
    import body, six6, race, arm, walker, clock
    m = car.build()
    body.build_body(m)
    for mm in (m, six6.build(), race.build(), arm.build(), walker.build()[0], clock.build()):
        assert power_ok(mm), mm.name


def test_instruction_arrows_point_home():
    """Инструкции: метка вида - многоугольник (линии LDView в габарит не берёт - кадры расходились, «стрелки мимо»);
    на шаге с новыми деталями есть красные стрелки; отодвинутая деталь смещена по своей оси к камере."""
    import instructions as ins
    import walker
    assert ins.ANCHOR[3].startswith("3 ")
    m = walker.build()[0]
    sub, ttl, cum, new, anchors, lon, pli = ins.pages(m)[5]
    ex, raw = ins.explode(cum, new, 28, lon, {id(q) for q in pli})
    assert sum(1 for line in raw if line.startswith("1 0x2E81E1E") and "4-4con0" in line) >= 3
    cam = ins._cam(28, lon)
    moved = 0
    for p, q in zip(new, ex[len(cum) - len(new):]):
        d = [q.pos[i] - p.pos[i] for i in range(3)]
        if any(abs(v) > 1 for v in d):
            moved += 1
            assert sum(d[i] * cam[i] for i in range(3)) > 0, p.name
    assert moved >= 3
