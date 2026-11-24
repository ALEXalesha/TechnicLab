"""README.md (en) и README.ru.md из одной таблицы моделей: числа (детали, страницы, время сборки) берутся из кода,
чтобы README не расходился с моделями. Запуск: python tools/make_readme.py (после python ядро/instructions.py)."""
import os
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "ядро"))
import paths  # noqa: E402
paths.add_models()
import instructions as ins  # noqa: E402

PICS = {"багги": "багги-v3.png", "самосвал-6x6": "самосвал-v2.png", "гоночная": "гоночная-v2.png", "рука": "рука-v3.png",
        "шагающий": "шагающий-v2.png", "часы": "часы-v1.png"}
EN = {"багги": ("Buggy", "4x4, steering from the axle, open V8, winch and spare wheel"),
      "самосвал-6x6": ("Dump truck 6x6", "six wheels, a hinged bed with sides, V8 and steering"),
      "гоночная": ("Racer", "low tyres, streamlined hood, rear drive with a step-up gear pair"),
      "рука": ("Robot arm", "shoulder on a linear actuator with an M motor, gripper on an L motor"),
      "шагающий": ("Walker", "four legs on Hoekens linkages driven by one XL motor"),
      "часы": ("Pendulum clock", "a falling weight, an escapement and a pendulum, minute hand")}
BADGES = ("[![Status](https://img.shields.io/badge/status-0.1.0_not_released-orange)](CHANGELOG.md) "
          "[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE) "
          "[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://www.python.org/) "
          "[![LDraw](https://img.shields.io/badge/LDraw-parts-yellow)](https://www.ldraw.org/) "
          "[![Built with Claude Code](https://img.shields.io/badge/Built_with-Claude_Code-D97757?logo=claude&logoColor=white)](https://claude.com/claude-code)")


def link(*parts):
    return "/".join(quote(p) for p in parts)


def stats():
    rows = []
    for key in ins.MODELS:
        m = ins.build_model(key)
        n = sum(1 for p in m.parts() if p.name != "v4.ldr" and p.name not in ins.NOT_PARTS)
        pdf = os.path.join(paths.folder(key), "%s - инструкция (iPad mini).pdf" % ins.MODELS[key]["title"])
        pages = "?"
        if os.path.exists(pdf):
            from pypdf import PdfReader
            pages = len(PdfReader(pdf).pages)
        rows.append((key, n, pages, ins._fmt_time(ins.build_minutes(n))))
    return rows


def main():
    rows = stats()
    total_p = sum(r[1] for r in rows)
    en = ["<div align=\"center\">", "", "# TechnicLab", "",
          "**Lego Technic models written in Python. Laws check that every part holds, every pin sits in two parts and",
          "every motor has power; then the code renders step-by-step PDF instructions for an iPad mini and for A4.**", "",
          "[Русский](README.ru.md)", "", BADGES, "", "</div>", "",
          "Code, tests and docs were written by Claude (Anthropic) in Claude Code; ideas, review and decisions are Alexey's.", "",
          "Every model uses only parts from one real Technic collection (`ядро/inventory.py`). This is a fan project: LEGO is a",
          "trademark of the LEGO Group, which does not sponsor or endorse it.", "",
          "## Models", "", "| | Model | Parts | Pages | Build time |", "| --- | --- | --- | --- | --- |"]
    ru = ["<div align=\"center\">", "", "# TechnicLab", "",
          "**Модели Lego Technic, написанные на Python. Законы проверяют, что каждая деталь держится, каждый штифт сидит",
          "в двух деталях и у каждого мотора есть питание; потом код рисует пошаговые инструкции PDF для iPad mini и A4.**", "",
          "[English](README.md)", "", BADGES, "", "</div>", "",
          "Код, тесты и документацию написал Claude (Anthropic) в Claude Code; идеи, проверка и решения - Алексея.", "",
          "Все модели собраны только из деталей одного настоящего набора Technic (`ядро/inventory.py`). Фанатский проект:",
          "LEGO - товарный знак LEGO Group, она его не спонсирует и не одобряет.", "",
          "## Модели", "", "| | Модель | Деталей | Страниц | Сборка |", "| --- | --- | --- | --- | --- |"]
    for key, n, pages, t in rows:
        img = "<img src=\"%s\" width=\"220\">" % link(key, PICS[key])
        name_en, what_en = EN[key]
        spec = ins.MODELS[key]
        en.append("| %s | **%s** - %s | %d | %s | ~%s |" % (img, name_en, what_en, n, pages, t.replace(" ч ", " h ").replace(" мин", " min")))
        ru.append("| %s | **%s** - %s | %d | %s | ~%s |" % (img, spec["title"], spec["subtitle"][0].lower() + spec["subtitle"][1:], n, pages, t))
    en += ["", "Total: %d parts in %d models. Build time assumes about 2 parts a minute." % (total_p, len(rows)), "",
           "## Instructions", "",
           "`python ядро/instructions.py` builds two PDFs per model into its folder:",
           "- **iPad mini** - one page is exactly the iPad mini 7 screen in full-screen view, so the 1:1 pages at the end",
           "  show axles and beams at their real length;",
           "- **A4** (landscape) - the same pages 1.68 times larger for print; the 1:1 pages stay 1:1 (print at 100 %).", "",
           "Like LEGO instructions: a list of parts for each step, new parts float next to their place with red arrows,",
           "sub-assemblies in a frame, a rotate sign when the view turns, all parts and wiring at the end.", "",
           "![Instruction page](docs/instruction-page.png)", "",
           "## Run", "", "Needs Python 3.11+, `pip install pillow numpy reportlab pypdf pymupdf pytest`, the LDraw library",
           "(`LDRAWDIR`), the LDCad shadow library with connection points (`LDCAD_SHADOW`) and LDView for pictures.", "",
           "| What | Command |", "| --- | --- |",
           "| All laws of all models | `python -m pytest -q ядро/test_laws.py` |",
           "| Laws of one model | `python рука/arm.py` (the same for the other folders) |",
           "| Instructions (all or one model) | `python ядро/instructions.py [багги]` |", "",
           "## Inside", "",
           "- `ядро/` - parts and connections (`ldr.py`, `snaps.py`), the collection (`inventory.py`), the laws and the buggy",
           "  base (`car.py`, `body.py`), pictures (`render.py`), instructions (`instructions.py`), tests (`test_laws.py`).",
           "- one folder per model - its script, pictures and `.ldr` file (opens in LDCad, LeoCAD, Studio).",
           "- `архив/` - earlier versions and sketches.", "", "## License", "", "[MIT](LICENSE)", ""]
    ru += ["", "Всего %d деталей в %d моделях. Время сборки - примерно 2 детали в минуту." % (total_p, len(rows)), "",
           "## Инструкции", "",
           "`python ядро/instructions.py` кладёт в папку каждой модели два PDF:",
           "- **iPad mini** - страница ровно равна экрану iPad mini 7 во весь экран, поэтому листы 1:1 в конце показывают",
           "  оси и балки в натуральную длину;",
           "- **A4** (альбомный) - те же страницы в 1,68 раза крупнее для печати; листы 1:1 остаются 1:1 (печать 100 %).", "",
           "Как у LEGO: список деталей на каждом шаге, новые детали «подлетают» к месту с красными стрелками, узлы в рамке,",
           "значок поворота при смене вида, в конце все детали и провода.", "",
           "![Страница инструкции](docs/instruction-page.png)", "",
           "## Запуск", "", "Нужны Python 3.11+, `pip install pillow numpy reportlab pypdf pymupdf pytest`, библиотека LDraw",
           "(`LDRAWDIR`), теневая библиотека LDCad с точками соединения (`LDCAD_SHADOW`) и LDView для картинок.", "",
           "| Что | Команда |", "| --- | --- |",
           "| Законы всех моделей | `python -m pytest -q ядро/test_laws.py` |",
           "| Законы одной модели | `python рука/arm.py` (так же в остальных папках) |",
           "| Инструкции (все или одна модель) | `python ядро/instructions.py [багги]` |", "",
           "## Внутри", "",
           "- `ядро/` - детали и сцепления (`ldr.py`, `snaps.py`), набор (`inventory.py`), законы и база багги (`car.py`,",
           "  `body.py`), картинки (`render.py`), инструкции (`instructions.py`), тесты (`test_laws.py`).",
           "- папка на модель - её скрипт, картинки и файл `.ldr` (открывается в LDCad, LeoCAD, Studio).",
           "- `архив/` - прошлые версии и эскизы. Журнал решений - `СХЕМА.md`.", "", "## Лицензия", "", "[MIT](LICENSE)", ""]
    for name, lines in (("README.md", en), ("README.ru.md", ru)):
        with open(os.path.join(ROOT, name), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines))
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
