"""Genera el icono de Food Saver (una hoja blanca sobre fondo verde).

Herramienta de desarrollo: solo hace falta ejecutarla si se quiere cambiar el icono.
Requiere Pillow (pip install pillow). Desde la carpeta raíz del proyecto:

    python assets/generar_icono.py

Produce:
  * assets/icono.ico        -> icono del .exe (se pasa a PyInstaller con --icon)
  * food_saver/icono.py     -> el mismo dibujo en PNG/base64 para el icono de la ventana,
                               así no hace falta empaquetar archivos sueltos dentro del .exe
  * web/iconos/*.png        -> iconos de la versión web / Android (instalable en el celular)
  * android-app/assets/*.png-> iconos de origen para el APK (los convierte @capacitor/assets)
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


def dibujar_adaptable(fondo: bool) -> Image.Image:
    """Icono «adaptable» de Android: la hoja ocupa ~66 % del centro (zona segura, porque el sistema
    recorta el borde con la forma que elija cada celular). Con fondo=False es solo la hoja, transparente."""
    imagen = Image.new("RGBA", (TAMANO, TAMANO), (0, 0, 0, 0))
    lapiz = ImageDraw.Draw(imagen)
    if fondo:
        lapiz.rectangle((0, 0, TAMANO, TAMANO), fill=tema.VERDE)
    lado = TAMANO * 0.66
    desplazamiento = (TAMANO - lado) / 2
    hoja = [(x + desplazamiento, y + desplazamiento) for x, y in tema.puntos_hoja(lado)]
    lapiz.polygon(hoja, fill=tema.BLANCO)
    x0, y0, x1, y1 = tema.nervadura_hoja(lado)
    lapiz.line((x0 + desplazamiento, y0 + desplazamiento, x1 + desplazamiento, y1 + desplazamiento),
               fill=tema.VERDE, width=int(TAMANO * 0.03))
    return imagen


def _guardar_png(imagen: Image.Image, ruta: Path, lado: int) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    imagen.resize((lado, lado), Image.LANCZOS).save(ruta, format="PNG", optimize=True)


def generar_iconos_web_y_android(grande: Image.Image) -> None:
    web = RAIZ / "web" / "iconos"
    adaptable = dibujar_adaptable(fondo=True)
    _guardar_png(grande, web / "icono-192.png", 192)
    _guardar_png(grande, web / "icono-512.png", 512)
    _guardar_png(adaptable, web / "icono-maskable-512.png", 512)  # «maskable»: se recorta con cualquier forma
    _guardar_png(adaptable, web / "apple-touch-icon.png", 180)    # iOS no recorta: va con fondo
    _guardar_png(grande, web / "favicon.png", 48)
    origen = RAIZ / "android-app" / "assets"
    _guardar_png(grande, origen / "icon-only.png", 1024)
    _guardar_png(dibujar_adaptable(fondo=True), origen / "icon-background.png", 1024)
    _guardar_png(dibujar_adaptable(fondo=False), origen / "icon-foreground.png", 1024)


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
    generar_iconos_web_y_android(grande)
    print("Listo: assets/icono.ico, food_saver/icono.py, web/iconos/ y android-app/assets/")


if __name__ == "__main__":
    main()
