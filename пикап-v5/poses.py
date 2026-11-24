"""Позы готовой машины для последних страниц инструкции: открытый капот, двери кабины вверх, дверь багажника
с выдвинутым актуатором, колёса в повороте. Детали поворачиваются вокруг своих петель (теги в body.py / car.py)."""
import math

import car
import body
import ldr


def _rot_x(p, deg, hinge):
    """Поворот детали вокруг оси X через точку hinge=(y, z); положительный угол поднимает то, что за петлёй (+z)."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    dy, dz = p.pos[1] - hinge[0], p.pos[2] - hinge[1]
    R = [[1, 0, 0], [0, c, -s], [0, s, c]]
    return ldr.Part(p.name, p.color, (p.pos[0], hinge[0] + c * dy - s * dz, hinge[1] + s * dy + c * dz),
                    ldr.mat_mul(R, p.rot), p.note)


def _rot_y(p, deg, pivot_z):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    dx, dz = p.pos[0], p.pos[2] - pivot_z
    return ldr.Part(p.name, p.color, (c * dx + s * dz, p.pos[1], -s * dx + c * dz + pivot_z),
                    ldr.mat_mul(ldr.ry(deg), p.rot), p.note)


def posed(m, hood=0, cab=0, tail=0, steer=0):
    """Детали модели в позе. hood/cab/tail - углы открытия (°), steer - поворот колёс (°)."""
    out = []
    for p in m.parts():
        q = p
        if p.note == "hood" and hood:
            q = _rot_x(p, -hood, (-311, -200))                     # капот спереди петли: «вверх» - против часовой
        elif p.note.startswith("cabdoor") and cab:
            q = _rot_x(p, cab, (-211, -200))
        elif p.note == "door" and tail:
            q = _rot_x(p, tail, body.HINGE)
        elif p.note == "steer" and steer:
            q = _rot_y(p, steer, car.PIVOT_Z)
        out.append(q)
    if tail:
        out = _actuator_open(out, tail)
    return out


def _actuator_open(parts, tail):
    """Актуатор с мотором поворачиваются вокруг проушины основания на направление к концу на открытой двери;
    контрактный актуатор заменяется выдвинутым (на сколько выдвинулся - видно по длине)."""
    by, bz = body.ACT_B
    d = body.ACT_E0[0] - body.HINGE[0]
    t = math.radians(tail)
    ey, ez = body.HINGE[0] + d * math.cos(t), body.HINGE[1] + d * math.sin(t)
    e0y, e0z = body.ACT_E0
    a0 = math.atan2(e0y - by, e0z - bz)
    a1 = math.atan2(ey - by, ez - bz)
    turn = math.degrees(a1 - a0)                                    # поворот вокруг оси X (в плоскости y-z)
    ext = math.hypot(ey - by, ez - bz) - body.ACT_L0
    res = []
    for p in parts:
        # только узел двери: актуатор, его мотор M и ось 3 между ними (x=150); мотор M двигателя (x=70) не трогать
        if (p.name in ("61927-f1.dat", "58120c01.dat", "4519.dat") and abs(p.pos[0] - 150) < 1
                and abs(p.pos[1] + 331) < 1 and p.pos[2] > 0):
            q = _rot_x(p, -turn, (by, bz))
            if p.name == "61927-f1.dat" and ext > 50:
                q = ldr.Part("61927-f2.dat", q.color, q.pos, q.rot, q.note)
            res.append(q)
        else:
            res.append(p)
    return res


POSES = [
    ("Готов к бездорожью", dict(), (22, -38)),
    ("Капот и двери кабины открыты", dict(hood=55, cab=70), (25, -55)),
    ("Кузов пикапа", dict(), (25, 145)),
    ("Колёса в повороте, вид сбоку", dict(steer=25), (8, -90)),
    ("Всё открыто", dict(hood=55, cab=70, steer=-20), (30, 40)),
]


if __name__ == "__main__":
    import os
    import render
    m = car.build()
    body.build_body(m)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    for k, (ttl, kw, (lat, lon)) in enumerate(POSES):
        mm = ldr.Model("pose%d.ldr" % k)
        mm.steps = [ldr.Step("")]
        body_name = {"58121c01.dat": "58121.dat", "58120c01.dat": "58120.dat"}   # без витого кабеля
        mm.steps[0].parts = [ldr.Part(body_name.get(q.name, q.name), q.color, q.pos, q.rot) for q in posed(m, **kw)]
        p = os.path.join(out, "pose%d.ldr" % k)
        ldr.write_mpd(p, mm, [car.v4_model()])
        print(p)
