"""Genera el icono de Food Saver (una hoja blanca sobre fondo verde).

Herramienta de desarrollo: solo hace falta ejecutarla si se quiere cambiar el icono.
Requiere Pillow (pip install pillow). Desde la carpeta raíz del proyecto:

    python assets/generar_icono.py

Produce:
  * assets/icono.ico        -> icono del .exe (se pasa a PyInstaller con --icon)
  * food_saver/icono.py     -> el mismo dibujo en PNG/base64 para el icono de la ventana,
                               así no hace falta empaquetar archivos sueltos dentro del .exe
"""
import base64
import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from food_saver import tema  # noqa: E402  (se importa la misma hoja que dibuja la app)

TAMANO = 1024  # se dibuja grande y se reduce para que los bordes salgan suaves


def dibujar() -> Image.Image:
    imagen = Image.new("RGBA", (TAMANO, TAMANO), (0, 0, 0, 0))
    lapiz = ImageDraw.Draw(imagen)
    lapiz.rounded_rectangle((0, 0, TAMANO - 1, TAMANO - 1), radius=int(TAMANO * 0.22), fill=tema.VERDE)
    lapiz.polygon(tema.puntos_hoja(TAMANO), fill=tema.BLANCO)
    lapiz.line(tema.nervadura_hoja(TAMANO), fill=tema.VERDE, width=int(TAMANO * 0.035))
    return imagen


def main() -> None:
    grande = dibujar()

    carpeta = RAIZ / "assets"
    carpeta.mkdir(exist_ok=True)
    grande.resize((256, 256), Image.LANCZOS).save(
        carpeta / "icono.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    )

    memoria = io.BytesIO()
    grande.resize((64, 64), Image.LANCZOS).save(memoria, format="PNG", optimize=True)
    codigo = base64.b64encode(memoria.getvalue()).decode("ascii")
    lineas = [codigo[i:i + 96] for i in range(0, len(codigo), 96)]
    contenido = (
        '"""Icono de la ventana (PNG de 64x64 en base64). Generado por assets/generar_icono.py."""\n\n'
        "ICONO_PNG_BASE64 = (\n" + "\n".join(f'    "{linea}"' for linea in lineas) + "\n)\n"
    )
    (RAIZ / "food_saver" / "icono.py").write_text(contenido, encoding="utf-8")
    print("Listo: assets/icono.ico y food_saver/icono.py")


if __name__ == "__main__":
    main()
