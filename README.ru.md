<div align="center">

# TechnicLab

**Модели Lego Technic, написанные на Python. Законы проверяют, что каждая деталь держится, каждый штифт сидит
в двух деталях и у каждого мотора есть питание; потом код рисует пошаговые инструкции PDF для iPad mini и A4.**

[English](README.md)

[![Status](https://img.shields.io/badge/status-0.1.0-brightgreen)](CHANGELOG.md) [![Release](https://img.shields.io/github/v/release/ALEXalesha/TechnicLab)](https://github.com/ALEXalesha/TechnicLab/releases/latest) [![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE) [![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![LDraw](https://img.shields.io/badge/LDraw-parts-yellow)](https://www.ldraw.org/) [![Built with Claude Code](https://img.shields.io/badge/Built_with-Claude_Code-D97757?logo=claude&logoColor=white)](https://claude.com/claude-code)

</div>

Код, тесты и документацию написал Claude (Anthropic) в Claude Code; идеи, проверка и решения - Алексея.

Все модели собраны только из деталей одного настоящего набора Technic (`ядро/inventory.py`). Фанатский проект:
LEGO - товарный знак LEGO Group, она его не спонсирует и не одобряет.

## Модели

| | Модель | Деталей | Страниц | Сборка |
| --- | --- | --- | --- | --- |
| <img src="%D0%B1%D0%B0%D0%B3%D0%B3%D0%B8/%D0%B1%D0%B0%D0%B3%D0%B3%D0%B8-v3.png" width="220"> | **Багги** - полный привод, руль от моста, открытый V8, лебёдка и запаска | 285 | 76 | ~2 ч 30 мин |
| <img src="%D1%81%D0%B0%D0%BC%D0%BE%D1%81%D0%B2%D0%B0%D0%BB-6x6/%D1%81%D0%B0%D0%BC%D0%BE%D1%81%D0%B2%D0%B0%D0%BB-v2.png" width="220"> | **Самосвал 6x6** - шесть колёс, кузов с бортами на петле, V8 и руль | 372 | 98 | ~3 ч 00 мин |
| <img src="%D0%B3%D0%BE%D0%BD%D0%BE%D1%87%D0%BD%D0%B0%D1%8F/%D0%B3%D0%BE%D0%BD%D0%BE%D1%87%D0%BD%D0%B0%D1%8F-v2.png" width="220"> | **Гоночная** - низкие шины, обтекаемый капот, задний привод с повышающей парой | 229 | 59 | ~2 ч 00 мин |
| <img src="%D1%80%D1%83%D0%BA%D0%B0/%D1%80%D1%83%D0%BA%D0%B0-v3.png" width="220"> | **Механическая рука** - плечо на актуаторе с мотором M, захват на моторе L, блок - противовес | 44 | 15 | ~15 мин |
| <img src="%D1%88%D0%B0%D0%B3%D0%B0%D1%8E%D1%89%D0%B8%D0%B9/%D1%88%D0%B0%D0%B3%D0%B0%D1%8E%D1%89%D0%B8%D0%B9-v2.png" width="220"> | **Шагающий робот** - четыре ноги на механизме Хокенса, мотор XL сверху | 80 | 19 | ~45 мин |
| <img src="%D1%87%D0%B0%D1%81%D1%8B/%D1%87%D0%B0%D1%81%D1%8B-v1.png" width="220"> | **Маятниковые часы** - гиря на верёвке, анкер и маятник, минутная стрелка | 28 | 11 | ~15 мин |

Всего 1038 деталей в 6 моделях. Время сборки - примерно 2 детали в минуту.

## Инструкции

Готовые PDF (12 файлов, шесть моделей в двух размерах) - в [Releases](https://github.com/ALEXalesha/TechnicLab/releases/latest).

`python ядро/instructions.py` кладёт в папку каждой модели два PDF:
- **iPad mini** - страница ровно равна экрану iPad mini 7 во весь экран, поэтому листы 1:1 в конце показывают
  оси и балки в натуральную длину;
- **A4** (альбомный) - те же страницы в 1,68 раза крупнее для печати; листы 1:1 остаются 1:1 (печать 100 %).

Как у LEGO: список деталей на каждом шаге, новые детали «подлетают» к месту с красными стрелками, узлы в рамке,
значок поворота при смене вида, в конце все детали и провода.

![Страница инструкции](docs/instruction-page.png)

## Запуск

Нужны Python 3.11+, `pip install pillow numpy reportlab pypdf pymupdf pytest`, библиотека LDraw
(`LDRAWDIR`), теневая библиотека LDCad с точками соединения (`LDCAD_SHADOW`) и LDView для картинок.

| Что | Команда |
| --- | --- |
| Законы всех моделей | `python -m pytest -q ядро/test_laws.py` |
| Законы одной модели | `python рука/arm.py` (так же в остальных папках) |
| Инструкции (все или одна модель) | `python ядро/instructions.py [багги]` |

## Внутри

- `ядро/` - детали и сцепления (`ldr.py`, `snaps.py`), набор (`inventory.py`), законы и база багги (`car.py`,
  `body.py`), картинки (`render.py`), инструкции (`instructions.py`), тесты (`test_laws.py`).
- папка на модель - её скрипт, картинки и файл `.ldr` (открывается в LDCad, LeoCAD, Studio).
- `архив/` - прошлые версии и эскизы. Журнал решений - `СХЕМА.md`.

## Лицензия

[MIT](LICENSE)
