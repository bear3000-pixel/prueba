"""Permite ejecutar la app con:  python -m food_saver   (o  python -m food_saver --clasico)"""
import sys

from .app_visual import main

if __name__ == "__main__":
    main(clasico="--clasico" in sys.argv[1:])
