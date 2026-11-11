"""Recetas creadas por el usuario: validación de lo que escribe y guardado en su propio archivo.

Una receta propia tiene: nombre, ingredientes (cada uno con CANTIDAD y UNIDAD) y pasos de
preparación. Se convierte en el mismo objeto `Receta` que usan las predefinidas, así el motor de
sugerencias (logica.py) las trata igual, pero además compara las cantidades con tu despensa.

Todo pasa por `crear_receta`, que lanza ErrorValidacion con un mensaje en español listo para
mostrar. Reutiliza las validaciones de modelo.py, así que las reglas son las mismas que al agregar
un ingrediente: no se aceptan cantidades vacías, cero, negativas, con letras, en notación
científica ni absurdamente grandes.

Los datos se guardan en `recetas_propias.json`, junto al archivo de ingredientes.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from typing import Iterable

from . import almacenamiento
from .logica import coincide_ingrediente
from .modelo import (
    ErrorValidacion,
    normalizar,
    validar_cantidad,
    validar_nombre,
    validar_unidad,
)
from .recetas import Receta

MAX_INGREDIENTES = 20
MAX_PASOS = 20
LARGO_MAX_NOMBRE = 60
LARGO_MAX_PASO = 300
VERSION_ARCHIVO = 1


# --------------------------------------------------------------------------- #
# Validaciones
# --------------------------------------------------------------------------- #
def validar_nombre_receta(texto: str) -> str:
    nombre = " ".join((texto or "").split())
    if not nombre:
        raise ErrorValidacion("Escribe el nombre de la receta.", "nombre")
    if len(nombre) > LARGO_MAX_NOMBRE:
        raise ErrorValidacion(f"El nombre de la receta es demasiado largo (máximo {LARGO_MAX_NOMBRE} caracteres).", "nombre")
    if not any(caracter.isalpha() for caracter in nombre):
        raise ErrorValidacion("El nombre de la receta debe contener letras.", "nombre")
    return nombre


def validar_ingrediente_receta(nombre: str, cantidad, unidad: str) -> tuple[str, float, str]:
    """Un ingrediente de la receta: nombre con letras, cantidad > 0 y unidad de la lista."""
    nombre_ok = validar_nombre(nombre)
    if str(cantidad).strip() == "":
        raise ErrorValidacion(f"Falta la cantidad de «{nombre_ok}».", "cantidad")
    return nombre_ok, validar_cantidad(cantidad), validar_unidad(unidad)


# Quita la numeración o viñeta que el usuario escriba al inicio ("1. ", "2) ", "- ", "• "),
# porque la pantalla ya numera los pasos. "2 huevos" o "1.5 tazas" NO se tocan.
_PREFIJO_PASO = re.compile(r"^\s*(?:[0-9]+\s*[.)]|[-*•])\s+")


def validar_pasos(pasos: str | Iterable[str]) -> tuple[str, ...]:
    """Convierte el texto de preparación (un paso por línea) en una lista de pasos limpios."""
    lineas = pasos.splitlines() if isinstance(pasos, str) else list(pasos)
    limpios = [_PREFIJO_PASO.sub("", linea).strip() for linea in lineas]
    limpios = [linea for linea in limpios if linea]
    if not limpios:
        raise ErrorValidacion("Escribe al menos un paso de preparación.", "pasos")
    if len(limpios) > MAX_PASOS:
        raise ErrorValidacion(f"Hay demasiados pasos (máximo {MAX_PASOS}).", "pasos")
    for numero, paso in enumerate(limpios, start=1):
        if len(paso) > LARGO_MAX_PASO:
            raise ErrorValidacion(f"El paso {numero} es demasiado largo (máximo {LARGO_MAX_PASO} caracteres).", "pasos")
        if not any(caracter.isalpha() for caracter in paso):
            raise ErrorValidacion(f"El paso {numero} debe contener texto.", "pasos")
    return tuple(limpios)


def crear_receta(
    nombre: str,
    ingredientes: Iterable[tuple[str, object, str]],
    pasos: str | Iterable[str],
    nombres_existentes: Iterable[str] = (),
    id: str | None = None,
) -> Receta:
    """Valida todo y devuelve la Receta lista para guardar.

    `ingredientes`: filas (nombre, cantidad, unidad). `nombres_existentes`: nombres de las demás
    recetas, para no repetir ninguno (se ignoran mayúsculas y acentos).
    """
    nombre_ok = validar_nombre_receta(nombre)
    if normalizar(nombre_ok) in {normalizar(otro) for otro in nombres_existentes}:
        raise ErrorValidacion(f"Ya existe una receta llamada «{nombre_ok}». Elige otro nombre.", "nombre")

    filas = list(ingredientes)
    if not filas:
        raise ErrorValidacion("Agrega al menos un ingrediente a la receta.", "ingredientes")
    if len(filas) > MAX_INGREDIENTES:
        raise ErrorValidacion(f"Hay demasiados ingredientes (máximo {MAX_INGREDIENTES}).", "ingredientes")

    validados: list[tuple[str, float, str]] = []
    for fila in filas:
        ingrediente = validar_ingrediente_receta(*fila)
        for anterior in validados:
            if coincide_ingrediente(ingrediente[0], anterior[0]) and coincide_ingrediente(anterior[0], ingrediente[0]):
                raise ErrorValidacion(f"«{ingrediente[0]}» está repetido en la receta.", "ingredientes")
        validados.append(ingrediente)

    return Receta(
        nombre=nombre_ok,
        ingredientes=tuple(n for n, _, _ in validados),
        instrucciones=validar_pasos(pasos),
        cantidades=tuple((c, u) for _, c, u in validados),
        propia=True,
        id=id or uuid.uuid4().hex,
    )


# --------------------------------------------------------------------------- #
# Guardado en disco
# --------------------------------------------------------------------------- #
def ruta_por_defecto() -> Path:
    """`recetas_propias.json`, en la misma carpeta que el archivo de ingredientes."""
    return almacenamiento.ruta_por_defecto().with_name("recetas_propias.json")


def a_dict(receta: Receta) -> dict:
    return {
        "id": receta.id,
        "nombre": receta.nombre,
        "ingredientes": [
            {"nombre": nombre, "cantidad": cantidad, "unidad": unidad}
            for nombre, (cantidad, unidad) in zip(receta.ingredientes, receta.cantidades)
        ],
        "instrucciones": list(receta.instrucciones),
    }


def desde_dict(datos: dict) -> Receta:
    """Reconstruye una receta leída del disco revalidándola entera (por si el archivo se editó a mano)."""
    filas = [(f["nombre"], f["cantidad"], f["unidad"]) for f in datos["ingredientes"]]
    return crear_receta(datos["nombre"], filas, datos["instrucciones"], id=datos.get("id"))


def guardar(ruta: Path, recetas: Iterable[Receta]) -> None:
    """Escribe las recetas propias. Lanza OSError si no se puede escribir."""
    almacenamiento.escribir_json_atomico(
        ruta, {"version": VERSION_ARCHIVO, "recetas": [a_dict(r) for r in recetas]}
    )


def cargar(ruta: Path) -> tuple[list[Receta], str | None]:
    """Lee las recetas propias. Devuelve (lista, aviso). Nunca lanza por un archivo malo:
    si está dañado lo respalda como `.corrupto`; las recetas inválidas se omiten y se avisa."""
    ruta = Path(ruta)
    if not ruta.exists():
        return [], None
    try:
        entradas = json.loads(ruta.read_text(encoding="utf-8"))["recetas"]
        if not isinstance(entradas, list):
            raise TypeError("'recetas' debe ser una lista")
    except (OSError, ValueError, KeyError, TypeError):
        respaldo = ruta.with_suffix(".corrupto")
        try:
            os.replace(ruta, respaldo)
            detalle = f"Se guardó una copia en:\n{respaldo}"
        except OSError:
            detalle = "No se pudo guardar una copia del archivo dañado."
        return [], f"El archivo de tus recetas estaba dañado y se empezó con la lista vacía.\n{detalle}"

    recetas: list[Receta] = []
    omitidas = 0
    for entrada in entradas:
        try:
            recetas.append(desde_dict(entrada))
        except (ErrorValidacion, KeyError, TypeError, AttributeError, ValueError):
            omitidas += 1
    aviso = f"Se omitieron {omitidas} receta(s) con datos inválidos en el archivo guardado." if omitidas else None
    return recetas, aviso
