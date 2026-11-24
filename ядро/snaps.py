"""Точки соединения деталей из теневой библиотеки LDCad (SNAP_CYL: штифты, оси, отверстия).
Закон «деталь держится»: у детали есть хотя бы одно соединение «папа в маме» с другой деталью
(оси цилиндров совпадают, отрезки перекрываются, форма подходит).
"""
import os
import re
import ldr

SHADOW = os.environ.get("LDCAD_SHADOW", r"C:\DevCache\lego\dl\shadow\LDCadShadowLibrary-main")
_cache = {}


def _shadow_path(name):
    name = name.replace("\\", os.sep).replace("/", os.sep).lower()
    for d in ("parts", "p", os.path.join("parts", "s")):
        p = os.path.join(SHADOW, d, name)
        if os.path.exists(p):
            return p
    return None


def _kv(line):
    return {m.group(1): m.group(2) for m in re.finditer(r"\[(\w+)=([^\]]*)\]", line)}


def _nums(s):
    return [float(x) for x in s.split()]


def _mat(v):
    return [[v[0], v[1], v[2]], [v[3], v[4], v[5]], [v[6], v[7], v[8]]]


def _grid(spec):
    """[grid=C 3 1 C 1 20 0 20] -> смещения в осях X, Z. C = по центру."""
    t = spec.split()
    vals = []
    i = 0
    flags = []
    nums = []
    while i < len(t):
        if t[i] == "C":
            flags.append(True)
            i += 1
            nums.append(float(t[i]))
        else:
            if len(nums) < 2 and (len(flags) <= len(nums)):
                flags.append(False)
            nums.append(float(t[i]))
        i += 1
    # формат: [C] cntX [C] cntZ stepX stepZ
    cx, cz = int(nums[0]), int(nums[1])
    sx, sz = nums[2], nums[3]
    centX = flags[0] if flags else False
    centZ = flags[1] if len(flags) > 1 else False
    offs = []
    for a in range(cx):
        for b in range(cz):
            x = a * sx - ((cx - 1) * sx / 2 if centX else 0)
            z = b * sz - ((cz - 1) * sz / 2 if centZ else 0)
            offs.append((x, 0.0, z))
    return offs


class Cyl:
    """Цилиндр соединения: точка pos, ось dir (единичная, вдоль Y ori), секции [(форма, радиус, длина)]."""

    def __init__(self, pos, ori, gender, secs, center):
        self.pos, self.ori, self.gender, self.secs, self.center = pos, ori, gender, secs, center

    def transformed(self, m, t):
        p = ldr.mat_vec(m, self.pos)
        return Cyl([p[0] + t[0], p[1] + t[1], p[2] + t[2]], ldr.mat_mul(m, self.ori), self.gender, self.secs, self.center)

    def _raw(self):
        return [self.ori[0][1], self.ori[1][1], self.ori[2][1]]

    def axis(self):
        r = self._raw()
        n = (r[0] ** 2 + r[1] ** 2 + r[2] ** 2) ** 0.5 or 1.0
        return [r[0] / n, r[1] / n, r[2] / n]

    def length(self):
        r = self._raw()
        k = (r[0] ** 2 + r[1] ** 2 + r[2] ** 2) ** 0.5 or 1.0
        return k * sum(s[2] for s in self.secs)

    def span(self):
        """Отрезок вдоль оси: (начало, конец) как числа вдоль axis() от pos."""
        L = self.length()
        # LDCad: нецентрированный цилиндр идёт от pos в сторону -Y своих осей (проверено на оси 4: снап на конце -40, ось Y = (-80,0,0))
        return (-L / 2, L / 2) if self.center else (-L, 0.0)

    def shapes(self):
        return {s[0] for s in self.secs}


def _parse_secs(s):
    t = s.split()
    out = []
    i = 0
    while i + 2 < len(t) + 1 and i < len(t):
        shape = t[i]          # R, A, S, L_, _L, _L_ ... - у каждой секции свои радиус и длина (было: _L пропускали -> штифт 3L короче на треть)
        try:
            r, l = float(t[i + 1]), float(t[i + 2])
        except (IndexError, ValueError):
            break
        out.append((shape, r, l))
        i += 3
    return out


def _shadow_snaps(name, depth=0):
    """Снапы из теневого файла name (с SNAP_INCL). Возвращает (снапы, clear)."""
    p = _shadow_path(name)
    if not p or depth > 10:
        return [], False
    snaps = []
    clear = False
    with open(p, encoding="utf-8", errors="replace") as f:
        for line in f:
            if "!LDCAD" not in line:
                continue
            kv = _kv(line)
            if "SNAP_CLEAR" in line:
                clear = True
            elif "SNAP_CYL" in line:
                pos = _nums(kv.get("pos", "0 0 0"))
                ori = _mat(_nums(kv.get("ori", "1 0 0 0 1 0 0 0 1")))
                c = Cyl(pos, ori, kv.get("gender", "M"), _parse_secs(kv.get("secs", "")), kv.get("center", "false") == "true")
                if "grid" in kv:
                    for o in _grid(kv["grid"]):
                        d = ldr.mat_vec(ori, o)
                        snaps.append(Cyl([pos[0] + d[0], pos[1] + d[1], pos[2] + d[2]], ori, c.gender, c.secs, c.center))
                else:
                    snaps.append(c)
            elif "SNAP_INCL" in line:
                pos = _nums(kv.get("pos", "0 0 0"))
                ori = _mat(_nums(kv.get("ori", "1 0 0 0 1 0 0 0 1")))
                subs, _ = _shadow_snaps(kv.get("ref", ""), depth + 1)
                subs_all = _part_snaps(kv.get("ref", ""), depth + 1) if not subs else subs
                offs = _grid(kv["grid"]) if "grid" in kv else [(0, 0, 0)]
                for o in offs:
                    d = ldr.mat_vec(ori, o)
                    t = [pos[0] + d[0], pos[1] + d[1], pos[2] + d[2]]
                    snaps += [s.transformed(ori, t) for s in subs_all]
    return snaps, clear


def _part_snaps(name, depth=0):
    key = name.lower()
    if key in _cache:
        return _cache[key]
    own, clear = _shadow_snaps(name, depth)
    snaps = list(own)
    if not clear:
        p = ldr.find(name)
        if p and depth < 12:
            with open(p, encoding="utf-8", errors="replace") as f:
                for line in f:
                    t = line.split()
                    if len(t) >= 15 and t[0] == "1":
                        x, y, z = map(float, t[2:5])
                        m = _mat(list(map(float, t[5:14])))
                        sub = " ".join(t[14:])
                        snaps += [s.transformed(m, [x, y, z]) for s in _part_snaps(sub, depth + 1)]
    _cache[key] = snaps
    return snaps


def part_snaps(part):
    """Снапы детали модели в мировых осях."""
    return [s.transformed(part.rot, part.pos) for s in _part_snaps(part.name)]


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


SHOCK_PRELOAD = 10.5   # амортизатор 6.5L под весом сжат: отверстие верха может стоять ниже на 10


def overlap_len(a, b, tol=0.6, slack=0.0):
    """Длина общего отрезка двух соосных цилиндров (0, если не соосны)."""
    ua, ub = a.axis(), b.axis()
    if abs(abs(_dot(ua, ub)) - 1) > 1e-3:
        return 0.0
    d = [b.pos[i] - a.pos[i] for i in range(3)]
    along = _dot(d, ua)
    perp = [d[i] - along * ua[i] for i in range(3)]
    if _dot(perp, perp) > max(tol, slack) ** 2:
        return 0.0
    a0, a1 = a.span()
    b0, b1 = b.span()
    s = 1 if _dot(ua, ub) > 0 else -1
    bb = sorted((along + s * b0, along + s * b1))
    return max(0.0, min(a1, bb[1]) - max(a0, bb[0]))


def connects(a, b, tol=0.6, slack=0.0):
    """Цилиндры a и b соединены: разный пол, оси совпадают, отрезки перекрываются, форма подходит."""
    if a.gender == b.gender:
        return False
    overlap = overlap_len(a, b, tol, slack)
    if overlap <= 0.5:
        return False
    m, f = (a, b) if a.gender == "M" else (b, a)
    # круглый штифт не входит в крестовое отверстие
    if m.shapes() <= {"R"} and f.shapes() <= {"A"}:
        return False
    return True


TYRES = {"55976.dat", "44309.dat"}       # шины Алексея: «баллон» 56x26 и низкие 43x22 (гоночная)
RIMS = {"56145.dat", "56904.dat"}


def _tyre_on_rim(t, r):
    """Шина надета на диск: та же точка и та же ось."""
    if t.name not in TYRES or r.name not in RIMS:
        return False
    d = sum((t.pos[i] - r.pos[i]) ** 2 for i in range(3)) ** 0.5
    at = [t.rot[0][2], t.rot[1][2], t.rot[2][2]]
    ar = [r.rot[0][2], r.rot[1][2], r.rot[2][2]]
    return d < 1 and abs(abs(_dot(at, ar)) - 1) < 1e-3


def _sub_on_axle(sub, ax):
    """Собранный заранее узел (подмодель .ldr, например V4) сидит на оси, проходящей через его начало координат вдоль X."""
    if not sub.name.endswith(".ldr") or "Axle" not in ldr.title(ax.name):
        return False
    a = [ax.rot[0][0], ax.rot[1][0], ax.rot[2][0]]
    return abs(abs(a[0]) - 1) < 1e-3 and abs(ax.pos[1] - sub.pos[1]) < 1 and abs(ax.pos[2] - sub.pos[2]) < 1


def connections(parts):
    """Список пар (i, j) деталей, у которых есть соединение."""
    S = [part_snaps(p) for p in parts]
    pairs = set()
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            if _sub_on_axle(parts[i], parts[j]) or _sub_on_axle(parts[j], parts[i]):
                pairs.add((i, j))
                continue
            sl = SHOCK_PRELOAD if "73129.dat" in (parts[i].name, parts[j].name) else 0.0
            if _tyre_on_rim(parts[i], parts[j]) or _tyre_on_rim(parts[j], parts[i])                     or any(connects(a, b, slack=sl) for a in S[i] for b in S[j]):
                pairs.add((i, j))
    return pairs


def components(parts, pairs):
    """Группы деталей, сцепленных друг с другом (вся модель должна быть одной группой)."""
    parent = list(range(len(parts)))

    def f(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for i, j in pairs:
        parent[f(i)] = f(j)
    groups = {}
    for i in range(len(parts)):
        groups.setdefault(f(i), []).append(i)
    return sorted(groups.values(), key=len, reverse=True)
