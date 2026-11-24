"""Пути проекта: модель/ядро - общий код и законы, модель/<модель>/ - скрипт модели, её картинки и .ldr,
модель/_кэш - картинки деталей и шагов для инструкций, модель/архив - старые версии и эскизы."""
import os
import sys

CORE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(CORE)
CACHE = os.path.join(ROOT, "_кэш")
MODELS = ("багги", "самосвал-6x6", "гоночная", "рука", "шагающий", "часы", "архив")


def folder(name):
    return os.path.join(ROOT, name)


def add_models():
    """Скрипты моделей - в sys.path (для законов, которые строят все модели)."""
    for n in MODELS:
        p = folder(n)
        if p not in sys.path:
            sys.path.append(p)
