"""Инструкция PDF в стиле LEGO под iPad mini 7 (экран 2266x1488 при 326 ppi = 176,6 x 115,9 мм, альбомная).
При просмотре во весь экран 1 мм страницы = 1 мм экрана -> страница «1:1» для сверки длины осей и балок.

Что есть:
- узлы (подсборки) отдельно, в рамке; потом шаг «поставь узел» с картинкой узла в списке деталей;
- неподвижная камера (метки по углам габарита - LDView не сдвигает вид между шагами);
- новые детали шага обведены оранжевым (маска из отдельного кадра «только новые» той же камерой);
- список деталей шага (PLI) в одном масштабе, у осей и балок - длина в кружке;
- значок поворота, если вид меняется; шаги больше 6 деталей делятся по порядку;
- в конце: все детали с количеством и страница 1:1.
Две версии: iPad mini (страница = экран) и A4 альбомный (те же страницы крупнее, листы 1:1 - в натуральную величину).
Запуск: python instructions.py [модель ...] -> <папка модели>/<Модель> - инструкция (iPad mini).pdf и (A4).pdf
"""
import collections
import os
import subprocess

from PIL import Image, ImageChops, ImageFilter
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

import car
import ldr
import render

pdfmetrics.registerFont(TTFont("A", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("AB", r"C:\Windows\Fonts\arialbd.ttf"))
import paths

OUT = paths.folder("багги")
WORK = os.path.join(paths.CACHE, "steps")
PLI = os.path.join(paths.CACHE, "pli4")       # pli3: крупнее (куб от 120 LDU), моторы без кабеля
W, H = 176.6 * mm, 115.9 * mm
MAXN = 6
NOT_PARTS = {"4-4cyli.dat"}     # верёвка (трос) - не деталь набора
BG = (255, 255, 255)
ORANGE = (255, 140, 0)
AXLE_LEN = {v: k for k, v in car.AXLE.items()}
BEAM_LEN = {v: k for k, v in car.BEAM.items()}
# моторы рисуем без кабеля: витой кабель LDraw торчит пружиной и путает (кабели тянуть по шагу «провода»)
BODY = {"58121c01.dat": "58121.dat", "58120c01.dat": "58120.dat"}
# свой ракурс узла: (широта, долгота). Лебёдку видно снизу-спереди-справа: червяк, катушка и направляющая троса
SUB_VIEW = {"Лебёдка": (-18, 35)}
# свой ракурс шага (по началу заголовка): валы вдоль машины видно только сбоку (Алексей 25.11: шаг 7 багги мелкий)
STEP_VIEW = {"Центральный дифференциал и валы": (35, -100)}


def step_view(title):
    return next((v for k, v in STEP_VIEW.items() if title.startswith(k)), None)
# метка вида - крошечный белый треугольник: линии (тип 2) LDView в габарит не берёт и кадрирует по деталям -
# тогда кадр меток стрелок и кадр шага расходились («стрелки мимо», Алексей 25.11)
ANCHOR = ["", "0 FILE anchor.ldr", "0 anchor", "3 15 0 0 0 0.01 0 0 0.02 0 0", ""]


def _write(path, parts, anchors, subs, raw=()):
    """Модель + 2 невидимые метки (белая линия на белом) по углам габарита -> вид не прыгает между шагами."""
    m = ldr.Model(os.path.basename(path))
    m.steps = [ldr.Step("")]
    m.steps[0].parts = [ldr.Part(BODY.get(p.name, p.name), p.color, p.pos, p.rot) for p in parts] +         [ldr.Part("anchor.ldr", 16, a) for a in anchors]
    lines = m.lines()
    lines[-1:-1] = list(raw)                       # стрелки - перед последним 0 STEP
    for s in subs:
        lines += [""] + s.lines()
    lines += ANCHOR
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")


SS = 2              # рендер в SS раз крупнее, потом уменьшение - гладкие рёбра (сглаживание)


def _snap(path, png, w, h, lat, lon, extra=()):
    """Кадр LDView без окна: в SS раз крупнее, затем уменьшение LANCZOS. Рёбра толще, чтобы после уменьшения не пропали."""
    big = os.path.join(WORK, "_ss.png")            # один черновик на всё, перезаписывается
    subprocess.run([render.LDVIEW, path, "-LDrawDir=" + render.LDRAW, "-SaveSnapshot=" + big,
                    "-SaveWidth=%d" % (w * SS), "-SaveHeight=%d" % (h * SS), "-SaveActualSize=0",
                    "-DefaultLatLong=%d,%d" % (lat, lon), "-BackgroundColor3=0xFFFFFF", "-AutoCrop=0", "-SaveAlpha=0",
                    "-EdgeThickness=%d" % (2 * SS), "-LineSmoothing=1", "-QualityLighting=1",
                    # как у LEGO: у чёрных деталей рёбра серые, контуры цилиндров - дырки видно
                    "-ShowHighlightLines=1", "-ConditionalHighlights=1", "-BlackHighlights=0", *extra],
                   check=True, timeout=300, creationflags=0x08000000 | 0x00000080)   # без окна, приоритет «высокий» (Алексей 25.11)
    Image.open(big).convert("RGB").resize((w, h), Image.LANCZOS).save(png)


def _anchors(parts, pad=40):
    # габарит моторов - без кабеля (на картинках кабеля нет, а витой кабель XL раздувал рамку вида вдвое)
    bbs = [b for b in (ldr.Part(BODY.get(p.name, p.name), p.color, p.pos, p.rot).world_bbox() for p in parts) if b]
    if any(p.name.endswith(".ldr") for p in parts):
        x0, y0, z0 = car.ENG
        bbs.append(((x0 - 110, y0 - 70, z0 - 70), (x0 + 110, y0 + 30, z0 + 70)))
    lo = [min(b[0][k] for b in bbs) - pad for k in range(3)]
    hi = [max(b[1][k] for b in bbs) + pad for k in range(3)]
    return [tuple(lo), tuple(hi)]


def _fill_holes(mask):
    """Залить дырки бинарной маски (L, 0/255): всё, куда не дотекает фон от края, - внутри силуэта."""
    from PIL import ImageDraw, ImageOps
    pad = ImageOps.expand(mask, border=1, fill=0)
    ImageDraw.floodfill(pad, (0, 0), 128)
    pad = pad.crop((1, 1, pad.width - 1, pad.height - 1))
    return pad.point(lambda v: 0 if v == 128 else 255)


ARROW = 4           # красные стрелки, как у LEGO
SMALL = {"3713.dat", "3647.dat", "3648b.dat", "3649.dat", "18575.dat", "32270.dat", "6536.dat", "32184.dat", "59443.dat",
         "32014.dat", "6558.dat", "4519.dat"}   # втулки, шестерни, соединители - всегда «подлетают» со стрелкой


def _axis(p):
    """Ось, вдоль которой деталь ставится: самое частое направление её отверстий и штифтов (в мире)."""
    import snaps
    cnt = collections.Counter()
    all_ = snaps.part_snaps(p)
    # дырки и штифты Technic (длина соединения 8+ LDU) важнее шипов (4 LDU): кирпич 1x16 садится на штифты сбоку, а не
    # сверху (Алексей 25.11, шаг 13 багги - кирпич прилетал сверху)
    tech = [c_ for c_ in all_ if sum(x[2] for x in c_.secs) >= 8]
    for c_ in (tech or all_):
        d = c_._raw()
        n = (d[0] ** 2 + d[1] ** 2 + d[2] ** 2) ** 0.5
        if n < 1e-6:
            continue
        d = [v / n for v in d]
        k = max(range(3), key=lambda i: abs(d[i]))
        if d[k] < 0:
            d = [-v for v in d]
        cnt[tuple(round(v, 2) for v in d)] += 1
    return list(cnt.most_common(1)[0][0]) if cnt else None


def _overlap(b, shift, boxes):
    lo = [b[0][i] + shift[i] for i in range(3)]
    hi = [b[1][i] + shift[i] for i in range(3)]
    tot = 0.0
    for q in boxes:
        v = 1.0
        for i in range(3):
            v *= max(0.0, min(hi[i], q[1][i]) - max(lo[i], q[0][i]))
        tot += v
    return tot


def _basis(u):
    t = [1, 0, 0] if abs(u[0]) < 0.9 else [0, 1, 0]
    v = [u[1] * t[2] - u[2] * t[1], u[2] * t[0] - u[0] * t[2], u[0] * t[1] - u[1] * t[0]]
    n = sum(x * x for x in v) ** 0.5
    v = [x / n for x in v]
    return v, [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]


def _arrow(tip, u, length, cam=None, r=1.7, head=13, hr=5.0):
    """Объёмная стрелка-«луч», как деталь (Алексей 25.11: «как 3д, как деталь»): круглый стержень и конус-наконечник
    ярко-красного цвета со светом и тенью, той же камерой - попадает точно в дырку. Остриё в tip, хвост по u."""
    v, w = _basis(u)
    col = "0x2E81E1E"
    f = lambda x: "%.3f" % x
    M = lambda a, b, c: " ".join(f(x) for x in (a[0], b[0], c[0], a[1], b[1], c[1], a[2], b[2], c[2]))
    base = [tip[i] + u[i] * head for i in range(3)]
    L = length - head
    out = ["1 %s %s %s 4-4con0.dat" % (col, " ".join(f(x) for x in base),
                                      M([x * hr for x in v], [-x * head for x in u], [x * hr for x in w])),
           "1 %s %s %s 4-4disc.dat" % (col, " ".join(f(x) for x in base),
                                       M([x * hr for x in v], [x for x in u], [x * hr for x in w]))]
    if L > 2:
        end = [base[i] + u[i] * L for i in range(3)]
        out.append("1 %s %s %s 4-4cyli.dat" % (col, " ".join(f(x) for x in base),
                                               M([x * r for x in v], [x * L for x in u], [x * r for x in w])))
        out.append("1 %s %s %s 4-4disc.dat" % (col, " ".join(f(x) for x in end),
                                               M([x * r for x in v], [x for x in u], [x * r for x in w])))
    return out

def _cam(lat, lon):
    """Направление на камеру LDView (-DefaultLatLong): lon -45 - спереди-слева, y вверх - минус."""
    import math
    la, lo = math.radians(lat), math.radians(lon)
    return [math.sin(lo) * math.cos(la), -math.sin(la), -math.cos(lo) * math.cos(la)]


def _free_side(bb, u, boxes, tol=6):
    """С какой стороны деталь вставляется: туда, где она торчит из уже поставленных деталей, которых касается.
    Штифт, торчащий из балки назад, ставят сзади - стрелка спереди сквозь балку показала бы не ту сторону
    (Алексей 25.11: «должны быть с другой стороны балки»). +1/-1 вдоль u или None, если торчит поровну."""
    k = max(range(3), key=lambda i: abs(u[i]))
    hit = [q for q in boxes if all(min(bb[1][i], q[1][i]) - max(bb[0][i], q[0][i]) > 1 for i in range(3))]
    if not hit:
        return None
    lo = min(q[0][k] for q in hit)
    hi = max(q[1][k] for q in hit)
    plus, minus = bb[1][k] - hi, lo - bb[0][k]
    if abs(plus - minus) <= tol:
        return None
    return (1 if plus > minus else -1) * (1 if u[k] > 0 else -1)


def insert_side(p, bb, u, boxes, new_boxes, mid, off=20):
    """Сторона установки вдоль u (+1/-1) или None: 1) где деталь торчит из старых деталей; 2) где торчит из новых
    этого шага (балка садится на штифты, которые торчат из лонжерона); 3) наружу от середины сборки. Без 2-3 балка,
    не касавшаяся старых, ехала «к камере» - дальняя сквозь раму внутрь (Алексей 25.11: «пины явно не с той стороны»)."""
    side = _free_side(bb, u, boxes)
    if side is None:
        side = _free_side(bb, u, boxes + [b for i, b in new_boxes if i != id(p)])
    if side is None:
        k = max(range(3), key=lambda i: abs(u[i]))
        d = (bb[0][k] + bb[1][k]) / 2 - mid[k]
        if abs(d) > off:
            side = (1 if d > 0 else -1) * (1 if u[k] > 0 else -1)
    return side


def explode(cum, new, lat=28, lon=-40, single=None):
    """Кадр шага как у LEGO: уже поставленные детали на месте, новые - отодвинуты вдоль своей оси наружу
    (туда, где меньше задевают старые), от каждой красная стрелка к месту установки."""
    fresh = {id(p) for p in new}
    old = [p for p in cum if id(p) not in fresh]
    boxes = [p.world_bbox() for p in old if p.world_bbox()]
    parts, raw = list(old), []
    new_boxes = [(id(p), p.world_bbox()) for p in new if p.world_bbox()]
    allb = boxes + [b for _, b in new_boxes]
    mid = [(min(b[0][i] for b in allb) + max(b[1][i] for b in allb)) / 2 for i in range(3)] if allb else [0, 0, 0]
    vol = lambda p: (lambda b: (b[1][0] - b[0][0]) * (b[1][1] - b[0][1]) * (b[1][2] - b[0][2]) if b else 0)(p.world_bbox())
    biggest = max(new, key=vol) if new else None
    group = [p for p in new if single is not None and id(p) not in single]
    if group:                                                   # поставь узел: весь узел над местом, стрелка вниз
        bbs = [p.world_bbox() for p in group if p.world_bbox()]
        lo = [min(b[0][i] for b in bbs) for i in range(3)]
        hi = [max(b[1][i] for b in bbs) for i in range(3)]
        lift = 90
        for p in group:
            parts.append(ldr.Part(p.name, p.color, [p.pos[0], p.pos[1] - lift, p.pos[2]], p.rot))
        top = [(lo[0] + hi[0]) / 2, lo[1] - 6, (lo[2] + hi[2]) / 2]
        raw += _arrow(top, [0, -1, 0], lift - 12, _cam(lat, lon))
    plan = []
    for p in new:
        if group and id(p) not in single:
            continue
        bb = p.world_bbox()
        small = p.name in car.PINS or p.name in AXLE_LEN or p.name in SMALL
        # основу шага не двигаем, если ставить её не на что; но если она садится на новые штифты - она едет за ними:
        # штифт с буртиком сквозь уже стоящую балку не пройдёт (Алексей 25.11)
        on_pins = bb and any(id(q) != id(p) and (q.name in car.PINS or q.name in SMALL) and q.world_bbox() and
                             all(min(bb[1][i], q.world_bbox()[1][i]) - max(bb[0][i], q.world_bbox()[0][i]) > 1 for i in range(3))
                             for q in new)
        move = small or (old and (p is not biggest or on_pins))
        u = _axis(p) if bb and move and not p.name.endswith(".ldr") else None
        if u is None:
            parts.append(p)
            continue
        half = sum(abs(u[i]) * (bb[1][i] - bb[0][i]) for i in range(3)) / 2
        d = min(150, 2 * half + 70)                         # зазор ~80 LDU: стрелка видна и у штифта
        cam = _cam(lat, lon)
        pv = max(1.0, (bb[1][0] - bb[0][0]) * (bb[1][1] - bb[0][1]) * (bb[1][2] - bb[0][2]))
        cand = []
        for sg in (1, -1):
            uu = [sg * x for x in u]
            ov = _overlap(bb, [uu[i] * d for i in range(3)], boxes) / pv
            cand.append((ov > 0.25, -sum(uu[i] * cam[i] for i in range(3)), ov, uu))
        uu = min(cand)[3]          # без больших задеваний, и к камере: место установки видно, деталь не за балкой
        side = insert_side(p, bb, u, boxes, new_boxes, mid)
        if side is not None:       # но сторона, откуда деталь реально ставится, важнее вида
            uu = [side * x for x in u]
        plan.append([p, bb, uu, half, d, cam])
    for p, bb, uu, half, d, cam in stack(plan):
        parts.append(ldr.Part(p.name, p.color, [p.pos[i] + uu[i] * d for i in range(3)], p.rot))
        # как в оригинале LEGO: линия идёт от детали сквозь место установки (видна в дырке) и выходит с другой стороны
        tip = [p.pos[i] - uu[i] * (half + 22) for i in range(3)]
        length = d + 18
        if length > 24:
            raw += _arrow(tip, uu, length, cam)
    return parts, raw


def _along(bb, uu):
    """Отрезок детали вдоль направления uu (по главной оси)."""
    k = max(range(3), key=lambda i: abs(uu[i]))
    return (bb[0][k], bb[1][k]) if uu[k] > 0 else (-bb[1][k], -bb[0][k])


def stack(plan, gap=20, dmax=400):
    """Порядок установки вдоль одного направления: что ставится раньше (ближе к месту), отодвинуто меньше. Деталь,
    которая в собранном виде дальше по направлению и перекрывает другую поперёк, ждёт за ней с зазором: штифты -
    между лонжероном и балкой 11, а не за балкой (иначе штифт с буртиком упрётся в балку)."""
    plan = sorted(plan, key=lambda t: sum(_along(t[1], t[2])))
    for j, (pj, bj, uj, _, dj, _) in enumerate(plan):
        k = max(range(3), key=lambda i: abs(uj[i]))
        for pi, bi, ui, _, di, _ in plan[:j]:
            if sum(ui[x] * uj[x] for x in range(3)) < 0.99:
                continue
            if all(min(bi[1][x], bj[1][x]) - max(bi[0][x], bj[0][x]) > 1 for x in range(3) if x != k):
                dj = max(dj, _along(bi, ui)[1] + di + gap - _along(bj, uj)[0])
        plan[j][4] = min(dmax, dj)
    return plan


def _content_bbox(im):
    """Рамка модели на кадре: без почти белых пикселей (невидимые метки вида после сглаживания)."""
    d = ImageChops.difference(im.convert("RGB"), Image.new("RGB", im.size, BG)).convert("L")
    return d.point(lambda v: 255 if v > 24 else 0).getbbox()


def _crop(png):
    im = Image.open(png).convert("RGB")
    bb = _content_bbox(im)
    if bb:
        im = im.crop((max(0, bb[0] - 4), max(0, bb[1] - 4), min(im.width, bb[2] + 4), min(im.height, bb[3] + 4)))
    im.save(png)
    return im.size


def pli_png(name, color):
    """Картинка детали в ОДНОМ масштабе для всех (куб меток 300 LDU вокруг середины детали), обрезанная по краю."""
    os.makedirs(PLI, exist_ok=True)
    png = os.path.join(PLI, "%s_%d.png" % (name.replace(".dat", ""), color))
    if not os.path.exists(png):
        b = ldr.bbox(BODY.get(name, name))
        c = [(b[0][k] + b[1][k]) / 2 for k in range(3)]
        ext = max(60, max(b[1][k] - b[0][k] for k in range(3)) * 0.6)
        tmp = png[:-4] + ".ldr"
        _write(tmp, [ldr.Part(name, color, (0, 0, 0))],
               [tuple(c[k] - ext for k in range(3)), tuple(c[k] + ext for k in range(3))], [])
        _snap(tmp, png, 600, 600, 30, 45)
        _crop(png)
        im = Image.open(png).convert("RGB")                  # белый фон -> прозрачный: детали без белых плашек
        a_ = ImageChops.difference(im, Image.new("RGB", im.size, BG)).convert("L").point(lambda v: 255 if v > 10 else 0)
        im.putalpha(a_.filter(ImageFilter.GaussianBlur(0.6)))
        im.save(png)
    return png


def _length_badge(c, x, y, n):
    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(0.2, 0.2, 0.2)
    c.setLineWidth(0.6)
    c.circle(x, y, 2.6 * mm, stroke=1, fill=1)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("AB", 8)
    c.drawCentredString(x, y - 1.1 * mm, str(n))


def _draw_pli(c, items, x0, ytop, maxw):
    """Список деталей шага: голубой блок, детали в одном масштабе (0,055 мм на пиксель картинки), «Nx» под деталью."""
    k = 0.055 * mm
    cells = []
    for (name, color), n in items:
        if name.endswith(".ldr") or name.startswith("__sub__"):
            continue
        img = pli_png(name, color)
        w, h = Image.open(img).size
        s = min(1.0, 16 * mm / (h * k), 34 * mm / (w * k))
        cells.append((img, w * k * s, h * k * s, n, name))
    if not cells:
        return 0, 0
    rows, row, rw = [], [], 0
    for cell in cells:
        cw = max(cell[1], 9 * mm) + 3 * mm
        if row and rw + cw > maxw:
            rows.append(row)
            row, rw = [], 0
        row.append(cell)
        rw += cw
    rows.append(row)
    heights = [max(cl[2] for cl in r) + 6 * mm for r in rows]
    width = max(sum(max(cl[1], 9 * mm) + 3 * mm for cl in r) for r in rows) + 3 * mm
    total = sum(heights) + 3 * mm
    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(0.55, 0.55, 0.58)
    c.setLineWidth(0.7)
    c.roundRect(x0, ytop - total, width, total, 2 * mm, stroke=1, fill=1)
    y = ytop - 2 * mm
    for r, hh in zip(rows, heights):
        x = x0 + 3 * mm
        rh = max(cl[2] for cl in r)
        for img, w, h, n, name in r:
            c.drawImage(img, x, y - rh, w, h, mask="auto")          # все детали ряда стоят по одному низу
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.setFont("AB", 8)
            c.drawString(x, y - hh + 1.5 * mm, "%dx" % n)
            L = AXLE_LEN.get(name) or BEAM_LEN.get(name)
            if L:
                _length_badge(c, x + w - 1.5 * mm, y - rh + 2 * mm, L)
            x += max(w, 9 * mm) + 3 * mm
        y -= hh
    return total, width


def _rotate_icon(c, x, y):
    c.setStrokeColorRGB(0.1, 0.1, 0.1)
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(x, y, 12 * mm, 9 * mm, 1.5 * mm, stroke=1, fill=1)
    c.setLineWidth(1.2)
    c.arc(x + 2 * mm, y + 2 * mm, x + 10 * mm, y + 7 * mm, 20, 300)
    c.line(x + 9.5 * mm, y + 5.2 * mm, x + 10.6 * mm, y + 3.6 * mm)
    c.line(x + 9.5 * mm, y + 5.2 * mm, x + 8.0 * mm, y + 4.4 * mm)
    c.setLineWidth(0.6)


def _chunks(parts):
    if len(parts) <= MAXN:
        return [parts]
    n = (len(parts) + MAXN - 1) // MAXN
    k = (len(parts) + n - 1) // n
    return [parts[i:i + k] for i in range(0, len(parts), k)]


def pages(model):
    """Последовательность страниц: (узел, заголовок, все детали кадра, новые детали, метки, вид, PLI-элементы)."""
    steps = [s for s in model.steps if s.parts or s.attach]        # шаг «поставь узел» - и без своих деталей
    full = [p for s in steps for p in s.parts]
    subs = collections.OrderedDict()
    for s in steps:
        if s.sub:
            subs.setdefault(s.sub, []).extend(s.parts)
    out = []
    main_done = []
    sub_done = collections.defaultdict(list)
    for s in steps:
        if s.sub:
            anchors = _anchors(subs[s.sub])
            for ch in _chunks(s.parts):
                sub_done[s.sub] += ch
                lon = SUB_VIEW.get(s.sub, (28, -40))[1]
                out.append((s.sub, s.title, list(sub_done[s.sub]), ch, anchors, lon, ch))
        else:
            first = True
            for ch in (_chunks(s.parts) if s.parts else [[]]):
                new = list(ch)
                pli = list(ch)
                if first:
                    for a in s.attach:
                        new += subs[a]
                        pli.append(ldr.Part("__sub__" + a, 16, (0, 0, 0)))
                first = False
                main_done += new
                rear = sum(p.pos[2] > 60 for p in ch) > len(ch) / 2
                sv = step_view(s.title)
                out.append(("", s.title, list(main_done), new, _anchors(full), sv[1] if sv else (140 if rear else -40), pli))
    return out


def logo(c, x, y, s=1.0):
    """Свой знак проекта (не логотип LEGO): жёлтый квадрат со скруглением, на нём чёрная балка с тремя дырками."""
    c.saveState()
    c.setFillColorRGB(1.0, 0.8, 0.0)
    c.setStrokeColorRGB(0.1, 0.1, 0.1)
    c.setLineWidth(0.8 * s)
    c.roundRect(x, y, 14 * mm * s, 14 * mm * s, 2.5 * mm * s, stroke=1, fill=1)
    c.setFillColorRGB(0.12, 0.12, 0.12)
    c.roundRect(x + 1.5 * mm * s, y + 4.5 * mm * s, 11 * mm * s, 5 * mm * s, 2.5 * mm * s, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    for k in range(3):
        c.circle(x + (3.9 + 3.1 * k) * mm * s, y + 7 * mm * s, 1.15 * mm * s, stroke=0, fill=1)
    c.restoreState()


def build_minutes(n_parts):
    """Время сборки: ~2 детали в минуту (Technic, с поиском деталей), округление до 15 мин."""
    return max(15, int(round(n_parts / 2.0 / 15.0)) * 15)


def _fmt_time(mins):
    h, m_ = divmod(mins, 60)
    return ("%d ч %02d мин" % (h, m_)) if h else ("%d мин" % m_)


def _count_pages(fn, *args):
    import io as _io
    d = canvas.Canvas(_io.BytesIO(), pagesize=(W, H))
    n0 = d.getPageNumber()
    fn(d, *args)
    return d.getPageNumber() - n0


CAPTION_TOP = 9 * mm     # подпись шага внизу страницы (строка на 5 мм) - выше неё ничего из списка деталей


def sub_box_h(y):
    """Высота рамки узла в списке деталей, верх на y: 24 мм, а если места до подписи меньше - сколько есть (не меньше
    12 мм). Раньше рамка шла ниже подписи и «1x Передний мост» наезжал на текст (Алексей 25.11)."""
    return max(12 * mm, min(24 * mm, y - CAPTION_TOP))


def count_parts(model):
    """Сколько деталей покупать/ставить: без V8 Алексея (готовый узел) и без верёвки (NOT_PARTS). Одно число для
    обложки и README."""
    return sum(1 for p in model.parts() if p.name != "v4.ldr" and p.name not in NOT_PARTS)


COVER_COL = 45 * mm     # ширина колонки фактов на обложке (картинка - с 54 мм)


def wrap(text, font, size, width):
    """Строки не шире width: перенос после запятых (пункт списка не рвётся)."""
    out, cur = [], ""
    import re
    for w_ in re.split(r"(?<=, )", text):
        if cur and pdfmetrics.stringWidth(cur + w_, font, size) > width:
            out.append(cur.rstrip())
            cur = w_.lstrip()
        else:
            cur += w_
    if cur:
        out.append(cur.rstrip())
    return out


def cover(c, img, title, subtitle, facts, color):
    c.setFillColorRGB(*color)
    c.rect(0, H - 26 * mm, W, 26 * mm, stroke=0, fill=1)
    logo(c, 6 * mm, H - 21 * mm, 1.15)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("AB", 24)
    c.drawString(26 * mm, H - 13 * mm, title)
    c.setFont("A", 9.5)
    c.drawString(26 * mm, H - 19.5 * mm, subtitle)
    c.setFont("AB", 8)
    c.drawRightString(W - 6 * mm, H - 6.5 * mm, "TechnicLab")
    c.drawImage(img, 54 * mm, 10 * mm, W - 58 * mm, H - 38 * mm, preserveAspectRatio=True)
    y = H - 34 * mm
    for k, v in facts:
        c.setFillColorRGB(0.45, 0.45, 0.45)
        c.setFont("A", 7.5)
        c.drawString(7 * mm, y, k)
        c.setFillColorRGB(0.05, 0.05, 0.05)
        c.setFont("AB", 11)
        for ln in wrap(v, "AB", 11, COVER_COL):        # колонка фактов не заходит под картинку
            c.drawString(7 * mm, y - 4.6 * mm, ln)
            y -= 5 * mm
        y -= 6 * mm
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.setFont("A", 6.5)
    c.drawString(7 * mm, 5 * mm, "Своя модель из деталей Technic. LEGO - товарный знак LEGO Group, проект с ней не связан.")
    c.showPage()


def build_pdf(model, out_pdf, spec):
    """Инструкция одной модели. spec: title, subtitle, color, key (папка кэша), v4 (есть ли V8 Алексея), wiring, remotes."""
    global WORK
    WORK = os.path.join(paths.CACHE, "steps", spec["key"])
    os.makedirs(WORK, exist_ok=True)
    subs_v4 = [car.v4_model()] if spec.get("v4") else []
    title = spec["title"]
    pg = pages(model)
    c = canvas.Canvas(out_pdf, pagesize=(W, H))
    c.setTitle(title + " - инструкция")
    c.setAuthor("TechnicLab")
    full = [p for s in model.steps for p in s.parts]
    n_parts = count_parts(model)
    n_pages = 1 + len(pg) + (1 if spec.get("wiring") else 0) + _count_pages(inventory, full) + _count_pages(scale_page)
    elec = collections.Counter(ELECTRIC[p.name] for p in full if p.name in ELECTRIC)
    facts = [("Деталей", str(n_parts)), ("Шагов / страниц", "%d / %d" % (len(pg), n_pages)),
             ("Сборка", "~" + _fmt_time(build_minutes(n_parts))),
             ("Моторы и питание", ", ".join("%s %d" % (k, v) for k, v in elec.items()) or "без мотора")]
    fp = os.path.join(WORK, "cover.ldr")
    _write(fp, full, _anchors(full), subs_v4)
    _snap(fp, fp[:-4] + ".png", 1600, 1050, 25, -45)
    _crop(fp[:-4] + ".png")
    cover(c, fp[:-4] + ".png", title, spec["subtitle"], facts, spec["color"])
    sub_thumbs = {}
    prev_view = None
    step_no = 0
    sub_no = collections.Counter()
    # проход 1: кадры; проход 2: общая обрезка на вид (узел, поворот) - модель крупнее и не прыгает
    boxes = {}
    for k, (sub, ttl, cum, new, anchors, lon, pli) in enumerate(pg, 1):
        base = os.path.join(WORK, "p%03d" % k)
        _write(base + "c.ldr", cum, anchors, subs_v4)
        lat = (step_view(ttl) or SUB_VIEW.get(sub, (28, 0)))[0]
        ex_parts, ex_raw = explode(cum, new, lat, lon, {id(q) for q in pli})
        # метки вида шага охватывают и отодвинутые детали: кадр шага и кадр меток стрелок кадрируются одинаково
        bx = _anchors(ex_parts, pad=10)
        anc = [tuple(min(bx[0][i], anchors[0][i]) for i in range(3)), tuple(max(bx[1][i], anchors[1][i]) for i in range(3))]
        _write(base + "n.ldr", ex_parts, anc, subs_v4, ex_raw)   # шаг: новые детали в стороне, стрелки
        _snap(base + "c.ldr", base + "c.png", 1500, 980, lat, lon)
        _snap(base + "n.ldr", base + "n.png", 1500, 980, lat, lon)
        Image.open(base + "n.png").save(base + ".png")
        # стрелки - обычные детали сцены: где деталь сплошная, линию закрывает она, в дырке линия видна (как у LEGO)
        im = Image.open(base + ".png").convert("RGB")
        bb = _content_bbox(im)
        if bb:
            o = boxes.get((sub, lon))
            boxes[(sub, lon)] = bb if o is None else (min(o[0], bb[0]), min(o[1], bb[1]), max(o[2], bb[2]), max(o[3], bb[3]))
    for k, (sub, ttl, cum, new, anchors, lon, pli) in enumerate(pg, 1):
        base = os.path.join(WORK, "p%03d" % k)
        bb = boxes.get((sub, lon))
        if bb:
            # окно размера всей группы (один масштаб), центр - по модели этого шага
            im = Image.open(base + ".png").convert("RGB")
            cb = _content_bbox(im) or bb
            # кадр по текущей сборке (как у LEGO), но не мельче половины всей группы - штифт не во весь экран
            gw = max(cb[2] - cb[0], (bb[2] - bb[0]) * 0.35) + 40
            gh = max(cb[3] - cb[1], (bb[3] - bb[1]) * 0.35) + 40
            cx, cy = (cb[0] + cb[2]) / 2, (cb[1] + cb[3]) / 2
            x0 = int(min(max(cx - gw / 2, 0), max(0, im.width - gw)))
            y0 = int(min(max(cy - gh / 2, 0), max(0, im.height - gh)))
            box = (x0, y0, min(im.width, x0 + int(gw)), min(im.height, y0 + int(gh)))
            im = im.crop(box)
            a_ = ImageChops.difference(im, Image.new("RGB", im.size, BG)).convert("L").point(lambda v: 255 if v > 6 else 0)
            im.putalpha(a_)
            im.save(base + "_v.png")
            Image.open(base + "c.png").crop(box).save(base + "c_v.png")
        c.setFillColorRGB(0.92, 0.92, 0.93)
        c.rect(0, 0, W, H, stroke=0, fill=1)
        if sub:
            sub_no[sub] += 1
            sub_thumbs[sub] = base + "c_v.png"
            # рамка узла
            c.setFillColorRGB(0.95, 0.97, 1.0)
            c.setStrokeColorRGB(0.35, 0.55, 0.85)
            c.setLineWidth(1.2)
            c.roundRect(3 * mm, 3 * mm, W - 6 * mm, H - 6 * mm, 3 * mm, stroke=1, fill=1)
            c.setLineWidth(0.6)
            c.setFillColorRGB(0.2, 0.35, 0.6)
            c.setFont("AB", 9)
            c.drawRightString(W - 7 * mm, H - 9 * mm, "Узел: " + sub)
        # номер шага
        c.setFillColorRGB(0.05, 0.05, 0.05)
        if sub:
            c.setFont("AB", 18)
            c.drawString(7 * mm, H - 13 * mm, str(sub_no[sub]))
        else:
            step_no += 1
            c.setFont("AB", 24)
            c.drawString(6 * mm, H - 14 * mm, str(step_no))
        c.setFont("A", 7)
        c.setFillColorRGB(0.35, 0.35, 0.35)
        c.drawString(6 * mm, 5 * mm, ttl[:90])
        # PLI
        cnt = collections.Counter((p.name, p.color) for p in pli if p.name not in NOT_PARTS)
        h, pw = _draw_pli(c, sorted(cnt.items(), key=lambda x: -x[1]), 6 * mm, H - 17 * mm, 62 * mm)
        y = H - 17 * mm - h - 2 * mm
        if any(n_.startswith("__sub__") for n_, _ in cnt):
            pw = max(pw, 34 * mm)
        # картинка справа от списка деталей (не под ним); по вертикали - между заголовком и подписью
        x_img = max(6 * mm + pw + 4 * mm, 30 * mm)
        c.drawImage(base + "_v.png", x_img, 9 * mm, W - x_img - 4 * mm, H - 21 * mm, preserveAspectRatio=True, mask="auto")
        for name, _ in cnt:
            if name.startswith("__sub__"):
                sname = name[7:]
                img = sub_thumbs.get(sname)
                if img:
                    c.setFillColorRGB(0.95, 0.97, 1.0)
                    c.setStrokeColorRGB(0.35, 0.55, 0.85)
                    hb = sub_box_h(y)
                    c.roundRect(6 * mm, y - hb, 34 * mm, hb, 1.5 * mm, stroke=1, fill=1)
                    c.drawImage(img, 7 * mm, y - hb + 3.5 * mm, 32 * mm, hb - 5 * mm, preserveAspectRatio=True)
                    c.setFillColorRGB(0.1, 0.1, 0.1)
                    c.setFont("AB", 8)
                    c.drawString(7.5 * mm, y - hb + 1.2 * mm, "1x " + sname)
                    y -= hb + 2 * mm
        if any(p.name.endswith(".ldr") and not p.name.startswith("__") for p in pli):
            c.setFont("AB", 8)
            c.drawString(6 * mm, y - 4 * mm, "Твой собранный V8")
        if prev_view is not None and (sub, lon) != prev_view and prev_view[0] == sub:
            _rotate_icon(c, W - 20 * mm, H - 24 * mm)
        prev_view = (sub, lon)
        c.setFont("A", 7)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawRightString(W - 6 * mm, 5 * mm, "%d" % (k + 1))
        c.drawRightString(W - 12 * mm, 5 * mm, title)
        c.showPage()
    if spec.get("wiring"):
        wiring_page(c, spec["wiring"], spec.get("remotes", []))
    inventory(c, full)
    n_scale = _count_pages(scale_page)
    scale_page(c)
    c.save()
    return out_pdf, n_scale, n_pages


def to_a4(src, dst, keep_last):
    """A4 альбомный из iPad-версии: каждая страница увеличена на всю ширину листа (шрифты и картинки крупнее в 1,68 раза);
    последние keep_last страниц (1:1) - без увеличения, по центру, чтобы длины оставались натуральными."""
    from pypdf import PdfReader, PdfWriter, Transformation
    a4w, a4h = 297 * mm, 210 * mm
    r = PdfReader(src)
    w = PdfWriter()
    n = len(r.pages)
    for i, pgx in enumerate(r.pages):
        page = w.add_blank_page(a4w, a4h)
        if i >= n - keep_last:
            t = Transformation().translate((a4w - W) / 2, (a4h - H) / 2)
        else:
            k = a4w / W
            t = Transformation().scale(k, k).translate(0, (a4h - H * k) / 2)
        page.merge_transformed_page(pgx, t)
    w.add_metadata(r.metadata or {})
    with open(dst, "wb") as f:
        w.write(f)
    return dst


def inventory(c, parts):
    """Все детали с количеством (как в конце инструкций LEGO)."""
    parts = [p for p in parts if p.name not in NOT_PARTS]
    cnt = collections.Counter((p.name, p.color) for p in parts if p.name.endswith(".dat"))
    items = sorted(cnt.items(), key=lambda x: (x[0][1], ldr.title(x[0][0])))
    k = 0.05 * mm
    x, y, rowh = 6 * mm, H - 14 * mm, 0
    c.setFont("AB", 14)
    c.drawString(6 * mm, H - 9 * mm, "Все детали")
    for (name, color), n in items:
        img = pli_png(name, color)
        w, h = Image.open(img).size
        s = min(1.0, 14 * mm / (h * k), 28 * mm / (w * k))
        w, h = w * k * s, h * k * s
        if x + max(w, 12 * mm) > W - 6 * mm:
            x, y = 6 * mm, y - rowh - 7 * mm
            rowh = 0
        if y - h < 8 * mm:
            c.showPage()
            c.setFont("AB", 14)
            c.drawString(6 * mm, H - 9 * mm, "Все детали (дальше)")
            x, y, rowh = 6 * mm, H - 14 * mm, 0
        c.drawImage(img, x, y - h, w, h)
        c.setFont("AB", 8)
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.drawString(x, y - h - 4 * mm, "%dx" % n)
        c.setFont("A", 5.5)
        c.drawString(x + 6 * mm, y - h - 4 * mm, name.replace(".dat", ""))
        L = AXLE_LEN.get(name) or BEAM_LEN.get(name)
        if L:
            _length_badge(c, x + w, y - h + 2 * mm, L)
        x += max(w, 12 * mm) + 4 * mm
        rowh = max(rowh, h)
    c.showPage()


WIRING = [
    ("Блок батарей 1 (передний)", "провод -> приёмник 1 (правый, у серво)"),
    ("Приёмник 1, канал 1, КРАСНЫЙ", "мотор XL (езда) + сверху на его вилку мотор M двигателя V4"),
    ("Приёмник 1, канал 1, СИНИЙ", "серво (руль)"),
    ("Блок батарей 2 (задний)", "провод -> приёмник 2 (левый); сверху на блок - провод ламп (фары)"),
    ("Приёмник 2, канал 2, КРАСНЫЙ", "мотор L (лебёдка)"),
    ("Приёмник 2, канал 2, СИНИЙ", "мотор M у актуатора (дверь багажника)"),
]
REMOTES = [
    "Пульт со скоростью (8879) на канал 1: левое колесо - газ вперёд/назад, правое - руль. Руль поворачивается ступенями.",
    "Обычный пульт (8885) на канал 2: левый рычаг - лебёдка (мотать/отпускать), правый - дверь (открыть/закрыть).",
    "Переключатель каналов на приёмниках: приёмник 1 - на 1, приёмник 2 - на 2. На пультах - те же номера.",
    "Дверь: актуатор сам останавливается в конце хода (трещит муфта) - отпусти рычаг.",
    "Лебёдка: червяк держит груз и без тока. Трос привяжи к оси барабана справа от шестерни, выведи через отверстие 6536.",
    "Если провод не дотягивается - удлинитель (у тебя их 2). Провода крепи к балкам, чтобы не попали в шестерни и колёса.",
    "Если на подъёме приёмник 1 мигает и отключается - разгрузи его: мотор V4 переставь на третий приёмник (канал 3).",
]


def wiring_page(c, wiring=None, remotes=None):
    """Страница «Провода и пульты»: кто куда включается."""
    wiring = WIRING if wiring is None else wiring
    remotes = REMOTES if remotes is None else remotes
    c.setFont("AB", 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(6 * mm, H - 10 * mm, "Провода и пульты")
    y = H - 20 * mm
    for left, right in wiring:
        col = (0.85, 0.15, 0.1) if "КРАСН" in left else (0.1, 0.3, 0.85) if "СИН" in left else (0.15, 0.15, 0.15)
        c.setFillColorRGB(*col)
        c.setFont("AB", 9)
        c.drawString(8 * mm, y, left)
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.setFont("A", 9)
        c.drawString(72 * mm, y, right)
        y -= 7 * mm
    y -= 3 * mm
    c.setFont("AB", 10)
    c.drawString(6 * mm, y, "Пульты")
    y -= 6 * mm
    c.setFont("A", 8)
    for line in remotes:
        c.drawString(8 * mm, y, "- " + line)
        y -= 5.5 * mm
    c.showPage()


def scale_page(c):
    """1:1 на iPad mini 7 во весь экран: оси 2..12 и балки 3..15 в натуральную длину (1 модуль = 8 мм)."""
    c.setFont("AB", 13)
    c.drawString(6 * mm, H - 9 * mm, "1:1 - положи ось или балку (iPad во весь экран, A4 - печать 100 %)")
    y = H - 18 * mm
    c.setFont("A", 7)
    for n in (2, 3, 4, 5, 6, 7, 8, 10, 12):
        L = n * 8 * mm
        c.setFillColorRGB(0.15, 0.15, 0.15)
        c.rect(14 * mm, y - 1.3 * mm, L, 2.6 * mm, stroke=0, fill=1)
        _length_badge(c, 9 * mm, y, n)
        y -= 9.5 * mm
    _scale_check(c)
    c.showPage()
    c.setFont("AB", 13)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(6 * mm, H - 9 * mm, "1:1 - балки (дырки по 8 мм)")
    y = H - 20 * mm
    x0 = 14 * mm
    c.setStrokeColorRGB(0.15, 0.15, 0.15)
    for n in (3, 5, 7, 9, 11, 13, 15):
        L = n * 8 * mm
        c.roundRect(x0, y - 3.6 * mm, L - 0.8 * mm, 7.2 * mm, 3.6 * mm, stroke=1, fill=0)
        for i in range(n):
            c.circle(x0 + 3.6 * mm + i * 8 * mm, y, 2.4 * mm, stroke=1, fill=0)
        _length_badge(c, x0 - 5 * mm, y, n)
        y -= 12 * mm
    _scale_check(c)
    c.showPage()


def _scale_check(c):
    c.setFont("A", 7)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawString(6 * mm, 5 * mm, "Проверка масштаба: этот отрезок ровно 50 мм ->")
    c.setLineWidth(1)
    c.line(62 * mm, 6 * mm, 112 * mm, 6 * mm)
    c.setLineWidth(0.6)


ELECTRIC = {"58119.dat": "блок", "58123.dat": "приёмник", "58121c01.dat": "XL", "58120c01.dat": "M", "99499.dat": "L",
            "99498.dat": "серво", "61927-f1.dat": "актуатор"}
_CAR_REMOTES = [
    "Пульт со скоростью (8879) на канал 1: левое колесо - газ вперёд/назад, правое - руль.",
    "Обычный пульт (8885) на канал 2. Переключатели каналов на приёмниках - 1 и 2, на пультах те же номера.",
    "Если провод не дотягивается - удлинитель. Провода крепи к балкам, чтобы не попали в шестерни и колёса.",
]
MODELS = collections.OrderedDict([
    ("багги", dict(title="Багги", subtitle="Полный привод, руль от моста, открытый V8, лебёдка и запаска", color=(0.85, 0.55, 0.0),
                   v4=True, wiring=[("Блок батарей", "провод -> приёмник 1, на его вилку - приёмник 2"),
                                    ("Приёмник 1, канал 1, КРАСНЫЙ", "мотор XL (езда) + сверху на его вилку мотор M (V8)"),
                                    ("Приёмник 1, канал 1, СИНИЙ", "серво (руль)"),
                                    ("Приёмник 2, канал 2, КРАСНЫЙ", "мотор L (лебёдка)")],
                   remotes=_CAR_REMOTES + ["Лебёдка: левый рычаг пульта 8885 - мотать и отпускать. Червяк держит груз без тока."])),
    ("самосвал-6x6", dict(title="Самосвал 6x6", subtitle="Шесть колёс, кузов с бортами на петле, V8 и руль", color=(0.75, 0.2, 0.1),
                          v4=True, wiring=[("Блок батарей", "провод -> приёмник 1, на его вилку - приёмник 2"),
                                           ("Приёмник 1, канал 1, КРАСНЫЙ", "мотор XL (езда) + сверху мотор M (V8)"),
                                           ("Приёмник 1, канал 1, СИНИЙ", "серво (руль)"),
                                           ("Приёмник 2, канал 2, КРАСНЫЙ", "мотор L")],
                          remotes=_CAR_REMOTES + ["Кузов поднимается рукой: он на петле сзади."])),
    ("гоночная", dict(title="Гоночная", subtitle="Низкие шины, обтекаемый капот, задний привод с повышающей парой", color=(0.1, 0.35, 0.8),
                      v4=True, wiring=[("Блок батарей", "провод -> приёмник 1, на его вилку - приёмник 2"),
                                       ("Приёмник 1, канал 1, КРАСНЫЙ", "мотор L (езда) + сверху мотор M (V8)"),
                                       ("Приёмник 1, канал 1, СИНИЙ", "серво (руль)"),
                                       ("Приёмник 2", "запасной: сюда можно перенести мотор V8")],
                      remotes=_CAR_REMOTES)),
    ("рука", dict(title="Механическая рука", subtitle="Плечо на актуаторе с мотором M, захват на моторе L, блок - противовес",
                  color=(0.2, 0.55, 0.25), wiring=[("Блок батарей", "провод -> приёмник"),
                                                   ("Приёмник, КРАСНЫЙ", "мотор M у актуатора (плечо вверх и вниз)"),
                                                   ("Приёмник, СИНИЙ", "мотор L (захват: сжать и разжать)")],
                  remotes=["Обычный пульт (8885): левый рычаг - плечо, правый - захват.",
                           "Актуатор сам останавливается в конце хода (трещит муфта) - отпусти рычаг."])),
    ("шагающий", dict(title="Шагающий робот", subtitle="Четыре ноги на механизме Хокенса, мотор XL сверху", color=(0.45, 0.25, 0.65),
                      wiring=[("Блок батарей", "провод -> приёмник"), ("Приёмник, КРАСНЫЙ", "мотор XL (шаг вперёд и назад)")],
                      remotes=["Обычный пульт (8885): левый рычаг - идти вперёд и назад."])),
    ("часы", dict(title="Маятниковые часы", subtitle="Гиря на верёвке, анкер и маятник, минутная стрелка", color=(0.35, 0.35, 0.4))),
])


def build_model(key):
    import body
    if key == "багги":
        m = car.build()
        body.build_body(m)
        return m
    mod = {"самосвал-6x6": "six6", "гоночная": "race", "рука": "arm", "шагающий": "walker", "часы": "clock"}[key]
    m = __import__(mod).build()
    return m[0] if isinstance(m, tuple) else m


def make(key):
    import inventory as inv
    import time
    t0 = time.time()
    m = build_model(key)
    bad, groups = car.check(m, verbose=False)
    assert not bad and len(groups) == 1, "законы красные - инструкцию не делаю: " + key
    assert not car.overlaps(m, verbose=False) and not car.beam_overlaps(m, verbose=False), key
    assert not car.pin_seating(m, verbose=False) and not car.hole_sharing(m, verbose=False), key
    assert not inv.shortage(m.parts()), inv.shortage(m.parts())
    spec = dict(MODELS[key], key=key)
    folder = paths.folder(key)
    ipad = os.path.join(folder, "%s - инструкция (iPad mini).pdf" % spec["title"])
    _, n_scale, n_pages = build_pdf(m, ipad, spec)
    a4 = to_a4(ipad, os.path.join(folder, "%s - инструкция (A4).pdf" % spec["title"]), n_scale)
    print("%s: деталей %d, страниц %d, сборка ~%s, рендер %.0f с -> %s, %s" % (
        key, count_parts(m), n_pages, _fmt_time(build_minutes(count_parts(m))),
        time.time() - t0, os.path.basename(ipad), os.path.basename(a4)), flush=True)


if __name__ == "__main__":
    import sys
    import ctypes
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x80)   # высокий (Алексей 25.11: «верни высокий приоритет»)
    paths.add_models()
    for key in (sys.argv[1:] or list(MODELS)):
        make(key)
