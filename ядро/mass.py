"""Примерный центр тяжести модели: масса по типу детали (граммы, с батарейками), точка - середина габарита.
Для сравнения компоновок (чем ниже y_cg, тем устойчивее на склоне). Запуск: python mass.py"""
import car

MASS = {  # г
    "58119.dat": 165.0,      # блок батарей 8881 с 6 AA
    "58121c01.dat": 70.0, "58120c01.dat": 32.0, "99499.dat": 42.0, "99498.dat": 45.0, "58123.dat": 23.0,
    "55976.dat": 28.0, "56145.dat": 9.0, "64179.dat": 6.0, "65414c01.dat": 8.0, "61903.dat": 2.5,
    "v4.ldr": 30.0, "73129.dat": 4.0, "3703.dat": 6.0, "32278.dat": 4.0, "4185a.dat": 2.0,
}
DEFAULT = 1.2                # балки, штифты, оси, втулки


def cg(parts):
    """-> (масса г, x, y, z центра тяжести в LDU). y < 0 - выше земли."""
    tot = sx = sy = sz = 0.0
    for p in parts:
        b = car._bbox(p)
        if not b:
            continue
        w = MASS.get(p.name, DEFAULT)
        c = [(b[0][k] + b[1][k]) / 2 for k in range(3)]
        tot += w
        sx += w * c[0]
        sy += w * c[1]
        sz += w * c[2]
    return tot, sx / tot, sy / tot, sz / tot


if __name__ == "__main__":
    import body
    m = car.build()
    body.build_body(m)
    t, x, y, z = cg(m.parts())
    print("масса ~%.0f г, центр тяжести: высота %.1f мм над землёй, %.0f мм от передней оси" % (
        t, -y * 0.4, (z - car.FRONT_Z) * 0.4))
