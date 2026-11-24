"""Инструкция PDF в стиле LEGO под iPad mini 7 (экран 2266x1488 при 326 ppi = 176,6 x 115,9 мм, альбомная).
При просмотре во весь экран 1 мм страницы = 1 мм экрана -> страница «1:1» для сверки длины осей и балок.

Что есть:
- узлы (подсборки) отдельно, в рамке; потом шаг «поставь узел» с картинкой узла в списке деталей;
- неподвижная камера (метки по углам габарита - LDView не сдвигает вид между шагами);
- новые детали шага обведены оранжевым (маска из отдельного кадра «только новые» той же камерой);
- список деталей шага (PLI) в одном масштабе, у осей и балок - длина в кружке;
- значок поворота, если вид меняется; шаги больше 6 деталей делятся по порядку;
- в конце: все детали с количеством и страница 1:1.
Запуск: python instructions.py -> out/инструкция-ipad-mini.pdf
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
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
WORK = os.path.join(OUT, "steps")
PLI = os.path.join(OUT, "pli3")       # pli3: крупнее (куб от 120 LDU), моторы без кабеля
W, H = 176.6 * mm, 115.9 * mm
MAXN = 6
BG = (255, 255, 255)
ORANGE = (255, 140, 0)
AXLE_LEN = {v: k for k, v in car.AXLE.items()}
BEAM_LEN = {v: k for k, v in car.BEAM.items()}
# моторы рисуем без кабеля: витой кабель LDraw торчит пружиной и путает (кабели тянуть по шагу «провода»)
BODY = {"58121c01.dat": "58121.dat", "58120c01.dat": "58120.dat"}
# свой ракурс узла: (широта, долгота). Лебёдку видно снизу-спереди-справа: червяк, катушка и направляющая троса
SUB_VIEW = {"Лебёдка": (-18, 35)}
ANCHOR = ["", "0 FILE anchor.ldr", "0 anchor", "2 15 0 0 0 0 0 0.5", ""]


def _write(path, parts, anchors, subs):
    """Модель + 2 невидимые метки (белая линия на белом) по углам габарита -> вид не прыгает между шагами."""
    m = ldr.Model(os.path.basename(path))
    m.steps = [ldr.Step("")]
    m.steps[0].parts = [ldr.Part(BODY.get(p.name, p.name), p.color, p.pos, p.rot) for p in parts] +         [ldr.Part("anchor.ldr", 16, a) for a in anchors]
    lines = m.lines()
    for s in subs:
        lines += [""] + s.lines()
    lines += ANCHOR
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")


SS = 2              # рендер в SS раз крупнее, потом уменьшение - гладкие рёбра (сглаживание)


def _snap(path, png, w, h, lat, lon):
    """Кадр LDView без окна: в SS раз крупнее, затем уменьшение LANCZOS. Рёбра толще, чтобы после уменьшения не пропали."""
    big = os.path.join(WORK, "_ss.png")            # один черновик на всё, перезаписывается
    subprocess.run([render.LDVIEW, path, "-LDrawDir=" + render.LDRAW, "-SaveSnapshot=" + big,
                    "-SaveWidth=%d" % (w * SS), "-SaveHeight=%d" % (h * SS), "-SaveActualSize=0",
                    "-DefaultLatLong=%d,%d" % (lat, lon), "-BackgroundColor3=0xFFFFFF", "-AutoCrop=0", "-SaveAlpha=0",
                    "-EdgeThickness=%d" % (2 * SS), "-LineSmoothing=1", "-QualityLighting=1"],
                   check=True, timeout=300, creationflags=0x08000000)
    Image.open(big).convert("RGB").resize((w, h), Image.LANCZOS).save(png)


def _anchors(parts, pad=20):
    bbs = [p.world_bbox() for p in parts if p.world_bbox()]
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


def _highlight(cum_png, new_png, out_png):
    """Подсветка новых деталей, как в инструкциях LEGO: ровный оранжевый контур только по внешнему силуэту видимой
    части новых деталей (дырки маски залиты - внутренние рёбра не обводятся), сглаженный."""
    a = Image.open(cum_png).convert("RGB")
    n = Image.open(new_png).convert("RGB")
    new = ImageChops.difference(n, Image.new("RGB", n.size, BG)).convert("L").point(lambda v: 255 if v > 18 else 0)
    same = ImageChops.difference(n, a).convert("L").point(lambda v: 255 if v < 40 else 0)
    vis = ImageChops.multiply(new, same)
    vis = vis.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))      # без одиночных пикселей
    vis = vis.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(7))      # склеить щели между гранями
    vis = _fill_holes(vis)
    ring = ImageChops.subtract(vis.filter(ImageFilter.MaxFilter(9)), vis.filter(ImageFilter.MaxFilter(3)))
    ring = ring.filter(ImageFilter.GaussianBlur(0.9)).point(lambda v: min(255, int(v * 1.7)))
    a.paste(Image.new("RGB", a.size, ORANGE), (0, 0), ring)
    a.save(out_png)


def _crop(png):
    im = Image.open(png).convert("RGB")
    bb = ImageChops.difference(im, Image.new("RGB", im.size, BG)).getbbox()
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
    c.setFillColorRGB(0.86, 0.93, 0.98)
    c.setStrokeColorRGB(0.55, 0.72, 0.86)
    c.roundRect(x0, ytop - total, width, total, 2 * mm, stroke=1, fill=1)
    y = ytop - 2 * mm
    for r, hh in zip(rows, heights):
        x = x0 + 3 * mm
        for img, w, h, n, name in r:
            c.drawImage(img, x, y - h, w, h)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.setFont("AB", 8)
            c.drawString(x, y - hh + 1.5 * mm, "%dx" % n)
            L = AXLE_LEN.get(name) or BEAM_LEN.get(name)
            if L:
                _length_badge(c, x + w - 1.5 * mm, y - h + 2 * mm, L)
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
    steps = [s for s in model.steps if s.parts]
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
            for ch in _chunks(s.parts):
                new = list(ch)
                pli = list(ch)
                if first:
                    for a in s.attach:
                        new += subs[a]
                        pli.append(ldr.Part("__sub__" + a, 16, (0, 0, 0)))
                first = False
                main_done += new
                rear = sum(p.pos[2] > 60 for p in ch) > len(ch) / 2
                out.append(("", s.title, list(main_done), new, _anchors(full), 140 if rear else -40, pli))
    return out


def build_pdf(model, out_pdf, title):
    os.makedirs(WORK, exist_ok=True)
    subs_v4 = [car.v4_model()]
    pg = pages(model)
    c = canvas.Canvas(out_pdf, pagesize=(W, H))
    c.setTitle(title)
    # обложка
    full = [p for s in model.steps for p in s.parts]
    fp = os.path.join(WORK, "cover.ldr")
    _write(fp, full, _anchors(full), subs_v4)
    _snap(fp, fp[:-4] + ".png", 1600, 1050, 25, -45)
    c.drawImage(fp[:-4] + ".png", 4 * mm, 4 * mm, W - 8 * mm, H - 22 * mm, preserveAspectRatio=True)
    c.setFont("AB", 20)
    c.drawString(8 * mm, H - 13 * mm, title)
    c.setFont("A", 9)
    c.drawString(8 * mm, H - 18 * mm, "Шагов: %d. Деталей: %d. Открой во весь экран: страница = экран iPad mini 7." % (len(pg), len(full)))
    c.drawString(8 * mm, H - 22 * mm, "Кабели моторов на картинках не показаны - их протянем отдельным шагом.")
    c.showPage()
    sub_thumbs = {}
    prev_view = None
    step_no = 0
    sub_no = collections.Counter()
    # проход 1: кадры; проход 2: общая обрезка на вид (узел, поворот) - модель крупнее и не прыгает
    boxes = {}
    for k, (sub, ttl, cum, new, anchors, lon, pli) in enumerate(pg, 1):
        base = os.path.join(WORK, "p%03d" % k)
        _write(base + "c.ldr", cum, anchors, subs_v4)
        _write(base + "n.ldr", new, anchors, subs_v4)
        lat = SUB_VIEW.get(sub, (28, 0))[0]
        _snap(base + "c.ldr", base + "c.png", 1500, 980, lat, lon)
        _snap(base + "n.ldr", base + "n.png", 1500, 980, lat, lon)
        _highlight(base + "c.png", base + "n.png", base + ".png")
        im = Image.open(base + ".png").convert("RGB")
        bb = ImageChops.difference(im, Image.new("RGB", im.size, BG)).getbbox()
        if bb:
            o = boxes.get((sub, lon))
            boxes[(sub, lon)] = bb if o is None else (min(o[0], bb[0]), min(o[1], bb[1]), max(o[2], bb[2]), max(o[3], bb[3]))
    for k, (sub, ttl, cum, new, anchors, lon, pli) in enumerate(pg, 1):
        base = os.path.join(WORK, "p%03d" % k)
        bb = boxes.get((sub, lon))
        if bb:
            # окно размера всей группы (один масштаб), центр - по модели этого шага
            im = Image.open(base + ".png").convert("RGB")
            cb = ImageChops.difference(im, Image.new("RGB", im.size, BG)).getbbox() or bb
            gw, gh = bb[2] - bb[0] + 40, bb[3] - bb[1] + 40
            cx, cy = (cb[0] + cb[2]) / 2, (cb[1] + cb[3]) / 2
            x0 = int(min(max(cx - gw / 2, 0), max(0, im.width - gw)))
            y0 = int(min(max(cy - gh / 2, 0), max(0, im.height - gh)))
            box = (x0, y0, min(im.width, x0 + int(gw)), min(im.height, y0 + int(gh)))
            im = im.crop(box)
            a_ = ImageChops.difference(im, Image.new("RGB", im.size, BG)).convert("L").point(lambda v: 255 if v > 6 else 0)
            im.putalpha(a_)
            im.save(base + "_v.png")
            Image.open(base + "c.png").crop(box).save(base + "c_v.png")
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
        cnt = collections.Counter((p.name, p.color) for p in pli)
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
                    c.roundRect(6 * mm, y - 24 * mm, 34 * mm, 24 * mm, 1.5 * mm, stroke=1, fill=1)
                    c.drawImage(img, 7 * mm, y - 21 * mm, 32 * mm, 19 * mm, preserveAspectRatio=True)
                    c.setFillColorRGB(0.1, 0.1, 0.1)
                    c.setFont("AB", 8)
                    c.drawString(7.5 * mm, y - 23.3 * mm, "1x " + sname)
                    y -= 26 * mm
        if any(p.name.endswith(".ldr") for p in pli):
            c.setFont("AB", 8)
            c.drawString(6 * mm, y - 4 * mm, "Твой собранный V4")
        if prev_view is not None and (sub, lon) != prev_view and prev_view[0] == sub:
            _rotate_icon(c, W - 20 * mm, H - 24 * mm)
        prev_view = (sub, lon)
        c.setFont("A", 7)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawRightString(W - 6 * mm, 5 * mm, "%d" % (k + 1))
        c.showPage()
    wiring_page(c)
    inventory(c, full)
    scale_page(c)
    c.save()
    return out_pdf


def inventory(c, parts):
    """Все детали с количеством (как в конце инструкций LEGO)."""
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


def wiring_page(c):
    """Страница «Провода и пульты»: кто куда включается."""
    c.setFont("AB", 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(6 * mm, H - 10 * mm, "Провода и пульты")
    y = H - 20 * mm
    for left, right in WIRING:
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
    for line in REMOTES:
        c.drawString(8 * mm, y, "- " + line)
        y -= 5.5 * mm
    c.showPage()


def scale_page(c):
    """1:1 на iPad mini 7 во весь экран: оси 2..12 и балки 3..15 в натуральную длину (1 модуль = 8 мм)."""
    c.setFont("AB", 13)
    c.drawString(6 * mm, H - 9 * mm, "1:1 - положи ось или балку на экран (iPad mini 7, страница во весь экран)")
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


if __name__ == "__main__":
    import body
    m = car.build()
    body.build_body(m)
    bad, groups = car.check(m, verbose=False)
    assert not bad and len(groups) == 1, "законы красные - инструкцию не делаю"
    assert not car.overlaps(m, verbose=False)
    assert not car.beam_overlaps(m, verbose=False) and not car.pin_seating(m, verbose=False)
    assert not car.hole_sharing(m, verbose=False) and not car.steer_clearance(m, verbose=False)
    assert not body.hood_clearance(m, verbose=False) and not body.cab_door_clearance(m, verbose=False)
    import inventory
    assert not inventory.shortage(m.parts()), inventory.shortage(m.parts())
    print(build_pdf(m, os.path.join(OUT, "инструкция-ipad-mini.pdf"), "Внедорожник Lego Technic"))
