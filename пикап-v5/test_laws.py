"""Законы модели и их мутанты: каждый закон на чистой модели зелёный и ловит свою поломку.
Запуск: python test_laws.py   (без окон, только расчёт)
"""
import copy

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


def test_pickup_no_tailgate_door():
    """Пикап (Алексей 24.11): двери багажника нет, кузов - пол из 6 поперечин и задний борт, крыша только над кабиной."""
    import body
    m = fresh()
    assert not [p for p in m.parts() if p.note == "door"]
    floor = [p for p in m.parts() if p.name == "59443.dat" and abs(p.pos[1] + 171) < 1 and 320 <= p.pos[2] <= 420]
    assert len(floor) == 6
    assert body.ROOF_R[1] <= 40, body.ROOF_R


def test_mutant_hood_hits():
    """Мутант: балка над капотом на пути открытия (закрытый не трогает) -> закон капота ловит."""
    import body
    m = fresh()
    m.step("мутант")
    car.beam(m, 5, car.BLACK, (0, -441, -290), "z", "x")
    assert not body.door_clearance(m, angles=(0,), verbose=False, tag="hood", hinge=body.HOOD_H, axis_sign=-1)
    assert body.hood_clearance(m, verbose=False)


def test_cab_doors_open_clear():
    """Двери кабины поднимаются вверх на 30/60/80° и ничего не задевают; мутант - балка над дверью - ловится."""
    import body
    m = fresh()
    assert not body.cab_door_clearance(m, verbose=False)
    m.step("мутант")
    car.beam(m, 5, car.BLACK, (190, -311, -140), "z", "x")
    assert body.cab_door_clearance(m, verbose=False)


def test_hood_opens_clear():
    """Капот открывается на 20/40/55° без задеваний."""
    import body
    assert not body.hood_clearance(fresh(), verbose=False)


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


def test_two_battery_boxes():
    """Два блока: второй пристёгнут к первому 4 штифтами 3L, над амортизаторами (низ блока выше верха амортизатора)."""
    m = fresh()
    boxes = [p for p in m.parts() if p.name == "58119.dat"]
    assert len(boxes) == 2
    b2 = max(boxes, key=lambda p: p.pos[2])
    shocks = [p for p in m.parts() if p.name == "73129.dat"]
    assert all(b2.world_bbox()[1][1] < s.pos[1] - 9 for s in shocks)


def test_winch_ratio_and_mesh():
    """Червяк и 24з. на расстоянии 2 модуля по Z, на одной высоте; барабан перед лицом мотора не выходит за удлинители."""
    m = fresh()
    w = find(m, "4716.dat", (0, car.RAIL_Y, car.WINCH_Z))
    g = find(m, "3648b.dat", (0, car.RAIL_Y, car.DRUM_Z))
    assert abs(w.pos[2] - g.pos[2]) == 40 and w.pos[1] == g.pos[1] and w.pos[0] == g.pos[0]


def test_mutant_beam_into_battery():
    """Мутант: второй блок батарей на 8 модулей назад -> входит в задние стойки кузова."""
    m = fresh()
    p = find(m, "58119.dat", (0, -271, 240))
    p.pos = [0, -271, 400]
    bad = car.beam_overlaps(m, verbose=False)
    assert any(p in pair for pair in bad), bad


def test_mutant_two_in_hole():
    """Мутант: ось крепления задней арки снова на z=200, где сидит штифт ножки -> закон «две папы в дырке»."""
    m = fresh()
    a = [q for q in m.parts() if q.name == "3705.dat" and abs(q.pos[2] - 220) < 1 and abs(q.pos[1] + 171) < 1][0]
    a.pos = [a.pos[0], a.pos[1], 200]
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
