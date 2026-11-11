"""Guardado y carga de ingredientes en un archivo JSON (persistencia local).

* Los datos viven en ``%APPDATA%\\FoodSaver\\ingredientes.json`` en Windows (y en
  ``~/.local/share/FoodSaver`` en otros sistemas). Se pueden cambiar con la variable
  de entorno ``FOODSAVER_DATA`` (útil para pruebas).
* Se guarda de forma atómica: se escribe un archivo temporal y luego se reemplaza el
  original, así un corte de luz o un cierre brusco no deja el JSON a medias.
* Si el archivo está dañado no se pierde en silencio: se renombra a ``.corrupto`` y
  la app arranca vacía avisando al usuario.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .modelo import ErrorValidacion, Ingrediente

VERSION_ARCHIVO = 1


def ruta_por_defecto() -> Path:
    personalizada = os.environ.get("FOODSAVER_DATA")
    if personalizada:
        return Path(personalizada)
    base = os.environ.get("APPDATA")  # existe en Windows
    carpeta = Path(base) if base else Path.home() / ".local" / "share"
    return carpeta / "FoodSaver" / "ingredientes.json"


def guardar(ruta: Path, ingredientes: list[Ingrediente]) -> None:
    """Escribe todos los ingredientes. Lanza OSError si no se puede escribir."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    contenido = {
        "version": VERSION_ARCHIVO,
        "ingredientes": [i.a_dict() for i in ingredientes],
    }
    descriptor, ruta_temporal = tempfile.mkstemp(dir=ruta.parent, prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
            json.dump(contenido, archivo, ensure_ascii=False, indent=2)
        os.replace(ruta_temporal, ruta)  # reemplazo atómico
    except BaseException:
        # Si algo falló, no dejar basura temporal.
        try:
            os.unlink(ruta_temporal)
        except OSError:
            pass
        raise


def cargar(ruta: Path) -> tuple[list[Ingrediente], str | None]:
    """Lee los ingredientes. Devuelve (lista, aviso).

    ``aviso`` es None si todo salió bien, o un texto para mostrar al usuario si hubo
    que descartar algo dañado. Nunca lanza por un archivo malo: la app debe poder abrir.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        return [], None

    try:
        contenido = json.loads(ruta.read_text(encoding="utf-8"))
        entradas = contenido["ingredientes"]
        if not isinstance(entradas, list):
            raise TypeError("'ingredientes' debe ser una lista")
    except (OSError, ValueError, KeyError, TypeError):
        respaldo = ruta.with_suffix(".corrupto")
        try:
            os.replace(ruta, respaldo)
            detalle = f"Se guardó una copia en:\n{respaldo}"
        except OSError:
            detalle = "No se pudo guardar una copia del archivo dañado."
        return [], f"El archivo de datos estaba dañado y la app arrancó vacía.\n{detalle}"

    ingredientes: list[Ingrediente] = []
    descartados = 0
    for entrada in entradas:
        try:
            ingredientes.append(Ingrediente.desde_dict(entrada))
        except (ErrorValidacion, KeyError, TypeError, AttributeError):
            descartados += 1

    aviso = None
    if descartados:
        aviso = f"Se omitieron {descartados} ingrediente(s) con datos inválidos en el archivo guardado."
    return ingredientes, aviso
