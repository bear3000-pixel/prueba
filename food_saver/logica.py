"""Lógica de Food Saver: clasificar ingredientes y sugerir recetas.

Son funciones puras (sin interfaz, sin archivos, y la fecha de "hoy" entra como
parámetro), por eso se pueden probar fácilmente en tests/test_logica.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, NamedTuple

from .modelo import (
    DIAS_POR_VENCER,
    Ingrediente,
    convertir_cantidad,
    dias_para_vencer,
    esta_vencido,
    normalizar,
)
from .recetas import Receta

# Puntos que aporta a una receta cada ingrediente que SÍ tienes, según qué tan
# cerca esté de vencer. Más puntos = la receta ayuda más a evitar desperdicio.
PUNTOS_URGENTE = 5      # vence en DIAS_POR_VENCER días o menos (o sea, hoy..3 días)
PUNTOS_PRONTO = 3       # vence en 7 días o menos
PUNTOS_NORMAL = 1       # el resto
DIAS_PRONTO = 7


# --------------------------------------------------------------------------- #
# Ordenar y separar vencidos
# --------------------------------------------------------------------------- #
def ordenar_por_vencimiento(ingredientes: Iterable[Ingrediente]) -> list[Ingrediente]:
    """Del que vence primero al que vence último; empata por nombre."""
    return sorted(ingredientes, key=lambda i: (i.vencimiento, normalizar(i.nombre)))


def clasificar(
    ingredientes: Iterable[Ingrediente], hoy: date
) -> tuple[list[Ingrediente], list[Ingrediente]]:
    """Devuelve (vigentes, vencidos), cada lista ordenada por fecha de vencimiento."""
    ingredientes = list(ingredientes)
    vigentes = [i for i in ingredientes if not esta_vencido(i, hoy)]
    vencidos = [i for i in ingredientes if esta_vencido(i, hoy)]
    return ordenar_por_vencimiento(vigentes), ordenar_por_vencimiento(vencidos)


# --------------------------------------------------------------------------- #
# Coincidencia de nombres
# --------------------------------------------------------------------------- #
def _variantes(palabra: str) -> set[str]:
    """Formas singulares posibles de una palabra: 'tomates'->'tomate', 'limones'->'limon',
    'frijoles'->'frijol'. Se guardan varias porque en español el plural puede ser -s o -es."""
    variantes = {palabra}
    if len(palabra) > 3 and palabra.endswith("es"):
        variantes.add(palabra[:-2])
    if len(palabra) > 2 and palabra.endswith("s"):
        variantes.add(palabra[:-1])
    return variantes


def coincide_ingrediente(requerido: str, disponible: str) -> bool:
    """¿El ingrediente que pide la receta ('tomate') es el que tiene el usuario ('Tomates cherry')?

    Se ignoran mayúsculas, acentos y plurales. Cada palabra del nombre de la receta
    debe aparecer en el nombre del usuario, así 'Leche entera' sirve para 'leche'.
    (Limitación conocida: 'pasta de tomate' también coincidiría con 'tomate'.)
    """
    palabras_disponibles = [_variantes(p) for p in normalizar(disponible).split()]
    for palabra in normalizar(requerido).split():
        if not any(_variantes(palabra) & variantes for variantes in palabras_disponibles):
            return False
    return True


# --------------------------------------------------------------------------- #
# Sugerencia de recetas
# --------------------------------------------------------------------------- #
class Uso(NamedTuple):
    """Un ingrediente de la receta cubierto por un lote concreto del usuario."""

    requerido: str      # como lo pide la receta, p. ej. "tomate"
    lote: Ingrediente   # el lote que se usaría (el que vence primero)
    dias: int           # días que le quedan a ese lote
    necesita: tuple[float, str] | None = None  # (cantidad, unidad) que pide la receta, si la indica


class Insuficiente(NamedTuple):
    """Ingrediente que SÍ tienes (vigente) pero en menor cantidad de la que pide la receta."""

    requerido: str
    lote: Ingrediente   # el lote que vence primero
    dias: int
    necesita: tuple[float, str]  # lo que pide la receta
    tienes: tuple[float, str]    # lo que hay en total, expresado en la unidad de la receta


@dataclass(frozen=True)
class Sugerencia:
    receta: Receta
    usados: tuple[Uso, ...]                  # lo que ya tienes (en cantidad suficiente)
    faltantes: tuple[str, ...]               # lo que no tienes (o solo tienes vencido)
    descartados_por_vencidos: tuple[str, ...]  # subconjunto de faltantes: lo tienes pero VENCIDO
    puntaje: int
    dias_mas_urgente: int                    # días del lote que vence primero entre los que usarías
    insuficientes: tuple[Insuficiente, ...] = ()  # lo tienes, pero en poca cantidad (solo recetas con cantidades)

    @property
    def completa(self) -> bool:
        return not self.faltantes and not self.insuficientes

    @property
    def total_ingredientes(self) -> int:
        return len(self.usados) + len(self.insuficientes) + len(self.faltantes)

    @property
    def uso_mas_urgente(self):
        """El ingrediente (suficiente o no) cuyo lote vence primero. Tiene .lote y .dias."""
        return min(self.usados + self.insuficientes, key=lambda u: u.dias)


def _cantidad_total(lotes: list[Ingrediente], unidad: str) -> float | None:
    """Suma lo que hay de un ingrediente expresado en `unidad` (convierte kg↔g y L↔ml).
    Devuelve None si ninguna de las unidades que tienes se puede comparar con esa."""
    total, comparable = 0.0, False
    for lote in lotes:
        convertida = convertir_cantidad(lote.cantidad, lote.unidad, unidad)
        if convertida is not None:
            total += convertida
            comparable = True
    return total if comparable else None


def _puntos(dias: int) -> int:
    if dias <= DIAS_POR_VENCER:
        return PUNTOS_URGENTE
    if dias <= DIAS_PRONTO:
        return PUNTOS_PRONTO
    return PUNTOS_NORMAL


def sugerir_recetas(
    ingredientes: Iterable[Ingrediente],
    recetas: Iterable[Receta],
    hoy: date,
    solo_completas: bool = False,
) -> list[Sugerencia]:
    """Recetas que se pueden armar (total o parcialmente) con ingredientes NO vencidos.

    Reglas:
    * Los ingredientes vencidos se excluyen: no cuentan como disponibles. Si una receta
      los pide, se listan como faltantes y se avisa que lo que tienes está vencido.
    * Si hay varios lotes del mismo ingrediente se usa el que vence primero.
    * Solo se sugieren recetas donde tengas al menos un ingrediente.
    * Si la receta indica cantidades (las recetas propias del usuario), se compara con lo que
      hay sumando todos los lotes vigentes: si falta cantidad, el ingrediente se reporta como
      «insuficiente». Si las unidades no se pueden comparar (p. ej. «2 unidades» contra
      «500 g») no se puede saber y se da por disponible. Las recetas predefinidas no indican
      cantidades, así que se comportan exactamente igual que antes.
    * Orden: más puntaje primero (privilegia ingredientes próximos a vencer), luego
      las que menos ingredientes faltan, luego alfabético.
    """
    ingredientes = list(ingredientes)
    vigentes = [i for i in ingredientes if not esta_vencido(i, hoy)]
    vencidos = [i for i in ingredientes if esta_vencido(i, hoy)]

    sugerencias: list[Sugerencia] = []
    for receta in recetas:
        usados: list[Uso] = []
        insuficientes: list[Insuficiente] = []
        faltantes: list[str] = []
        descartados: list[str] = []

        for indice, requerido in enumerate(receta.ingredientes):
            necesita = receta.cantidades[indice] if indice < len(receta.cantidades) else None
            lotes = [i for i in vigentes if coincide_ingrediente(requerido, i.nombre)]
            if lotes:
                # FIFO: gasta primero el lote que vence antes.
                lote = min(lotes, key=lambda i: (i.vencimiento, normalizar(i.nombre)))
                dias = dias_para_vencer(lote, hoy)
                if necesita is not None:
                    tiene = _cantidad_total(lotes, necesita[1])
                    if tiene is not None and tiene + 1e-9 < necesita[0]:
                        insuficientes.append(
                            Insuficiente(requerido, lote, dias, necesita, (tiene, necesita[1]))
                        )
                        continue
                usados.append(Uso(requerido, lote, dias, necesita))
            else:
                faltantes.append(requerido)
                if any(coincide_ingrediente(requerido, i.nombre) for i in vencidos):
                    descartados.append(requerido)

        if not usados and not insuficientes:
            continue  # no tienes nada para esta receta: no tiene sentido sugerirla
        if solo_completas and (faltantes or insuficientes):
            continue

        aprovechados = usados + insuficientes  # los dos usarían algo de tu despensa
        sugerencias.append(
            Sugerencia(
                receta=receta,
                usados=tuple(usados),
                faltantes=tuple(faltantes),
                descartados_por_vencidos=tuple(descartados),
                puntaje=sum(_puntos(u.dias) for u in aprovechados),
                dias_mas_urgente=min(u.dias for u in aprovechados),
                insuficientes=tuple(insuficientes),
            )
        )

    sugerencias.sort(
        key=lambda s: (-s.puntaje, len(s.faltantes) + len(s.insuficientes), normalizar(s.receta.nombre))
    )
    return sugerencias
