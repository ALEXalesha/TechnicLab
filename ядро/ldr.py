"""LDraw: чтение деталей (габариты в своих осях), сборка модели кодом, запись .ldr/.mpd.
Единицы LDU: 1 модуль Technic = 20 LDU = 8 мм. Ось Y в LDraw направлена ВНИЗ (верх = -Y).
"""
import os
import math

LDRAW = os.environ.get("LDRAWDIR", r"C:\DevCache\lego\ldraw")
SEARCH = ["parts", "p", os.path.join("parts", "s"), "models"]
_bbox_cache = {}
_title_cache = {}


def find(name):
    name = name.replace("\\", os.sep).replace("/", os.sep)
    for d in SEARCH:
        p = os.path.join(LDRAW, d, name)
        if os.path.exists(p):
            return p
        p2 = os.path.join(LDRAW, d, name.lower())
        if os.path.exists(p2):
            return p2
    return None


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def mat_vec(m, v):
    return [m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
            m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
            m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2]]


def title(name):
    if name not in _title_cache:
        p = find(name)
        t = "?"
        if p:
            with open(p, encoding="utf-8", errors="replace") as f:
                t = f.readline().strip()[2:]
        _title_cache[name] = t
    return _title_cache[name]


def _points(name, depth=0):
    """Все вершины детали в её осях (рекурсивно)."""
    p = find(name)
    if not p or depth > 12:
        return []
    pts = []
    with open(p, encoding="utf-8", errors="replace") as f:
        for line in f:
            t = line.split()
            if not t:
                continue
            if t[0] == "1" and len(t) >= 15:
                x, y, z = map(float, t[2:5])
                m = [[float(t[5]), float(t[6]), float(t[7])],
                     [float(t[8]), float(t[9]), float(t[10])],
                     [float(t[11]), float(t[12]), float(t[13])]]
                sub = " ".join(t[14:])
                for q in _points_cached(sub, depth + 1):
                    r = mat_vec(m, q)
                    pts.append((r[0] + x, r[1] + y, r[2] + z))
            elif t[0] in ("3", "4"):
                n = int(t[0])
                v = list(map(float, t[2:2 + 3 * n]))
                for i in range(n):
                    pts.append((v[3 * i], v[3 * i + 1], v[3 * i + 2]))
    return pts


_pts_cache = {}


def _points_cached(name, depth=0):
    key = name.lower()
    if key not in _pts_cache:
        pts = _points(name, depth)
        # прорежение: для габаритов хватает крайних точек по сетке 1 LDU
        uniq = {(round(a), round(b), round(c)) for a, b, c in pts}
        _pts_cache[key] = list(uniq)
    return _pts_cache[key]


def bbox(name):
    if name not in _bbox_cache:
        pts = _points_cached(name)
        if not pts:
            _bbox_cache[name] = None
        else:
            xs, ys, zs = zip(*pts)
            _bbox_cache[name] = ((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))
    return _bbox_cache[name]


# --- повороты (матрицы 3x3) ---
I = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def rx(deg):
    c, s = round(math.cos(math.radians(deg)), 6), round(math.sin(math.radians(deg)), 6)
    return [[1, 0, 0], [0, c, -s], [0, s, c]]


def ry(deg):
    c, s = round(math.cos(math.radians(deg)), 6), round(math.sin(math.radians(deg)), 6)
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]


def rz(deg):
    c, s = round(math.cos(math.radians(deg)), 6), round(math.sin(math.radians(deg)), 6)
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


class Part:
    def __init__(self, name, color, pos, rot=I, note=""):
        self.name, self.color, self.pos, self.rot, self.note = name, color, list(pos), rot, note

    def line(self):
        m = self.rot
        f = lambda v: ("%.4f" % v).rstrip("0").rstrip(".") if abs(v - round(v)) > 1e-6 else str(int(round(v)))
        nums = [*self.pos, m[0][0], m[0][1], m[0][2], m[1][0], m[1][1], m[1][2], m[2][0], m[2][1], m[2][2]]
        return "1 %d %s %s" % (self.color, " ".join(f(v) for v in nums), self.name)

    def world_bbox(self):
        b = bbox(self.name)
        if b is None:
            return None
        (x0, y0, z0), (x1, y1, z1) = b
        corners = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        w = [mat_vec(self.rot, c) for c in corners]
        w = [(a + self.pos[0], b_ + self.pos[1], c + self.pos[2]) for a, b_, c in w]
        xs, ys, zs = zip(*w)
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


class Step:
    def __init__(self, title=""):
        self.title, self.parts = title, []


class Model:
    """Модель = подсборки (submodel) из шагов. Подсборка вставляется в другую как деталь."""

    def __init__(self, name):
        self.name = name
        self.steps = []
        self.subs = []          # (имя файла подсборки, Model)

    def step(self, title=""):
        s = Step(title)
        s.sub = getattr(self, "sub", "")          # имя узла, который собирается отдельно ("" - основная сборка)
        s.attach = []                            # узлы, которые присоединяются на этом шаге
        self.steps.append(s)
        return s

    def add(self, name, color, pos, rot=I, note=None):
        if not self.steps:
            self.step()
        p = Part(name, color, pos, rot, note if note is not None else getattr(self, "tag", ""))
        self.steps[-1].parts.append(p)
        return p

    def parts(self):
        return [p for s in self.steps for p in s.parts]

    def lines(self):
        out = ["0 FILE %s" % self.name, "0 %s" % self.name, "0 Name: %s" % self.name, "0 Author: Claude for Alexey", ""]
        for i, s in enumerate(self.steps):
            if s.title:
                out.append("0 // %s" % s.title)
            out += [p.line() for p in s.parts]
            out.append("0 STEP")
        return out


def write_mpd(path, main, subs):
    lines = main.lines()
    for m in subs:
        lines.append("")
        lines += m.lines()
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")
