"""Punto de entrada de Food Saver (es lo que empaqueta PyInstaller para crear el .exe).

Para ejecutar sin compilar:  python main.py
"""
from food_saver.app import main

if __name__ == "__main__":
    main()
