"""Punto de entrada de Food Saver (es lo que empaqueta PyInstaller para crear el .exe).

    python main.py            -> abre la app con la apariencia renovada
    python main.py --clasico  -> abre la versión original (por si hiciera falta volver atrás)
"""
import sys

from food_saver.app_visual import main

if __name__ == "__main__":
    main(clasico="--clasico" in sys.argv[1:])
