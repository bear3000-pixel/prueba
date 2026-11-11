"""Modelo de datos y validaciones de entrada de Food Saver.

Todo lo que el usuario escribe pasa por las funciones ``validar_*`` y
``parsear_fecha`` ANTES de convertirse en un :class:`Ingrediente`. Si algo es
incorrecto se lanza :class:`ErrorValidacion` con un mensaje en español listo
para mostrarse en pantalla (así la interfaz nunca se rompe por un dato malo).

Este módulo no sabe nada de la interfaz gráfica ni de archivos: solo reglas.
"""
from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime

# Unidades que ofrece la lista desplegable (evita que el usuario escriba cualquier cosa).
UNIDADES = ("unidades", "kg", "g", "L", "ml", "tazas", "paquetes", "latas")

# Un ingrediente se marca "por vencer" cuando faltan este número de días o menos.
DIAS_POR_VENCER = 3

CANTIDAD_MAXIMA = 1_000_000
LARGO_MAXIMO_NOMBRE = 50


class ErrorValidacion(ValueError):
    """Dato de entrada inválido. ``campo`` indica qué campo corregir (opcional)."""

    def __init__(self, mensaje: str, campo: str | None = None):
        super().__init__(mensaje)
        self.campo = campo


# --------------------------------------------------------------------------- #
# Validaciones de texto -> valores
# --------------------------------------------------------------------------- #
def validar_nombre(texto: str) -> str:
    """Limpia espacios repetidos y exige un nombre con al menos una letra."""
    nombre = " ".join((texto or "").split())
    if not nombre:
        raise ErrorValidacion("Escribe el nombre del ingrediente.", "nombre")
    if len(nombre) > LARGO_MAXIMO_NOMBRE:
        raise ErrorValidacion(
            f"El nombre es demasiado largo (máximo {LARGO_MAXIMO_NOMBRE} caracteres).", "nombre"
        )
    if not any(caracter.isalpha() for caracter in nombre):
        raise ErrorValidacion("El nombre debe contener letras.", "nombre")
    return nombre


def validar_cantidad(texto: str | float | int) -> float:
    """Convierte el texto a número. Acepta coma o punto decimal ("1,5" o "1.5").

    Rechaza: vacío, letras, negativos, cero, notación científica ("1e3"),
    "nan"/"inf" y valores absurdamente grandes.
    """
    crudo = str(texto).strip().replace(",", ".")
    if not crudo:
        raise ErrorValidacion("Escribe la cantidad.", "cantidad")
    if crudo.startswith("-"):
        raise ErrorValidacion("La cantidad debe ser mayor que cero.", "cantidad")
    # Solo dígitos ASCII con un punto decimal opcional. Esto deja fuera "nan", "inf",
    # "1e5" y "1_000", que Python sí aceptaría con float() a secas.
    if not re.fullmatch(r"[0-9]+(\.[0-9]+)?|\.[0-9]+", crudo):
        raise ErrorValidacion("La cantidad debe ser un número (por ejemplo 2 o 1,5).", "cantidad")
    valor = round(float(crudo), 3)
    if valor <= 0:
        raise ErrorValidacion("La cantidad debe ser mayor que cero.", "cantidad")
    if valor > CANTIDAD_MAXIMA:  # también atrapa el caso float("9999...") == inf
        maximo = f"{CANTIDAD_MAXIMA:,}".replace(",", ".")  # 1.000.000 (separador de miles en español)
        raise ErrorValidacion(f"La cantidad es demasiado grande (máximo {maximo}).", "cantidad")
    return valor


def validar_unidad(texto: str) -> str:
    unidad = (texto or "").strip()
    if unidad not in UNIDADES:
        raise ErrorValidacion("Elige una unidad de la lista.", "unidad")
    return unidad


# Formatos de fecha aceptados al escribir. Internamente todo se guarda como date.
_FORMATOS_FECHA = ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y")


def parsear_fecha(texto: str) -> date:
    """Acepta DD/MM/AAAA, AAAA-MM-DD o DD-MM-AAAA. Rechaza fechas que no existen."""
    crudo = (texto or "").strip()
    if not crudo:
        raise ErrorValidacion("Escribe la fecha de vencimiento (DD/MM/AAAA).", "vencimiento")
    for formato in _FORMATOS_FECHA:
        try:
            fecha = datetime.strptime(crudo, formato).date()
        except ValueError:
            continue
        # Filtra errores de dedo típicos como 25/12/0226 o 25/12/2926.
        if not 2000 <= fecha.year <= 2100:
            raise ErrorValidacion("El año del vencimiento debe estar entre 2000 y 2100.", "vencimiento")
        return fecha
    raise ErrorValidacion(
        "Fecha no válida. Usa DD/MM/AAAA (por ejemplo 25/12/2026) y verifica que el día exista.",
        "vencimiento",
    )


_DIGITOS = "0123456789"
_SEPARADORES = "/-."


def autoformatear_fecha(texto: str, agregar_barra: bool = False) -> str:
    """Da formato DD/MM/AAAA MIENTRAS se escribe: '02112026' -> '02/11/2026'.

    * Solo acepta dígitos; letras y otros símbolos se descartan.
    * Pone las barras solas. Con ``agregar_barra=True`` (cuando el usuario está escribiendo, no
      borrando) también pone la barra apenas se completa el día o el mes: '02' -> '02/'.
    * Si el usuario escribe un separador (/, - o .) tras un solo dígito, completa el cero:
      '2/' -> '02/', y '2/11/2026' -> '02/11/2026'.
    * Un AAAA-MM-DD pegado completo se convierte: '2026-11-20' -> '20/11/2026'.
    * Ignora todo lo que sobre después del año (máximo 8 dígitos).

    Solo cambia la FORMA del texto. Que la fecha exista (31/02, mes 13…) lo decide
    ``parsear_fecha``, que no se modificó.
    """
    texto = texto or ""
    iso = re.fullmatch(r"\s*([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})\s*", texto)
    if iso:
        anio, mes, dia = iso.groups()
        return f"{int(dia):02d}/{int(mes):02d}/{anio}"

    maximos = (2, 2, 4)  # largo de día, mes y año
    campos = [""]
    for caracter in texto:
        actual = len(campos) - 1
        if caracter in _DIGITOS:
            if len(campos[actual]) == maximos[actual]:
                if actual == 2:
                    break  # el año está completo: lo demás sobra
                campos.append("")  # el campo se llenó: el dígito pasa al siguiente
                actual += 1
            campos[actual] += caracter
        elif caracter in _SEPARADORES:
            if campos[actual] == "":
                continue  # sin barras al comienzo ni dobles
            if actual == 2:
                break
            if len(campos[actual]) == 1:
                campos[actual] = "0" + campos[actual]
            campos.append("")
        # cualquier otro carácter (letras, espacios) se descarta

    resultado = "/".join(campos)
    ultimo = len(campos) - 1
    if agregar_barra and ultimo < 2 and len(campos[ultimo]) == maximos[ultimo]:
        resultado += "/"
    return resultado


# Unidades que se pueden convertir entre sí: familia y cuántas unidades base vale cada una.
_BASE = {"g": ("masa", 1), "kg": ("masa", 1000), "ml": ("volumen", 1), "L": ("volumen", 1000)}


def convertir_cantidad(cantidad: float, de: str, a: str) -> float | None:
    """Convierte entre kg↔g y L↔ml. Devuelve None si las unidades no se pueden comparar
    (por ejemplo 'unidades' con 'g')."""
    if de == a:
        return float(cantidad)
    if de in _BASE and a in _BASE and _BASE[de][0] == _BASE[a][0]:
        return cantidad * _BASE[de][1] / _BASE[a][1]
    return None


# --------------------------------------------------------------------------- #
# Ingrediente
# --------------------------------------------------------------------------- #
@dataclass
class Ingrediente:
    """Un "lote" de un ingrediente. Dos compras del mismo producto con distinto
    vencimiento son dos Ingredientes distintos (así se usa primero el que vence antes)."""

    nombre: str
    cantidad: float
    unidad: str
    vencimiento: date
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def a_dict(self) -> dict:
        """Forma serializable a JSON (la fecha se guarda en ISO: AAAA-MM-DD)."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "cantidad": self.cantidad,
            "unidad": self.unidad,
            "vencimiento": self.vencimiento.isoformat(),
        }

    @classmethod
    def desde_dict(cls, datos: dict) -> "Ingrediente":
        """Reconstruye un ingrediente leído del disco, revalidando todo.

        Si el archivo fue editado a mano o está dañado, lanza ErrorValidacion
        (o KeyError/TypeError) y el llamador decide qué hacer con esa entrada.
        """
        return crear_ingrediente(
            datos["nombre"],
            datos["cantidad"],
            datos["unidad"],
            datos["vencimiento"],
            id=datos.get("id"),
        )


def crear_ingrediente(
    nombre: str,
    cantidad: str | float | int,
    unidad: str,
    vencimiento: str | date,
    id: str | None = None,
) -> Ingrediente:
    """Valida los cuatro campos (en el orden en que aparecen en el formulario)."""
    nombre_ok = validar_nombre(nombre)
    cantidad_ok = validar_cantidad(cantidad)
    unidad_ok = validar_unidad(unidad)
    fecha_ok = vencimiento if isinstance(vencimiento, date) else parsear_fecha(vencimiento)
    if id:
        return Ingrediente(nombre_ok, cantidad_ok, unidad_ok, fecha_ok, id)
    return Ingrediente(nombre_ok, cantidad_ok, unidad_ok, fecha_ok)


# --------------------------------------------------------------------------- #
# Estado respecto a la fecha de hoy
# --------------------------------------------------------------------------- #
def dias_para_vencer(ingrediente: Ingrediente, hoy: date) -> int:
    """Días que faltan para vencer. 0 = vence hoy; negativo = ya venció."""
    return (ingrediente.vencimiento - hoy).days


def esta_vencido(ingrediente: Ingrediente, hoy: date) -> bool:
    """Vencido = su fecha es ANTERIOR a hoy. Un producto que vence hoy aún se puede usar."""
    return dias_para_vencer(ingrediente, hoy) < 0


def esta_por_vencer(ingrediente: Ingrediente, hoy: date) -> bool:
    return 0 <= dias_para_vencer(ingrediente, hoy) <= DIAS_POR_VENCER


# --------------------------------------------------------------------------- #
# Texto para mostrar
# --------------------------------------------------------------------------- #
def describir_vencimiento(dias: int) -> str:
    """'vence hoy', 'vence mañana', 'vence en 5 días', 'vencido hace 2 días'."""
    if dias < 0:
        atras = -dias
        return "vencido hace 1 día" if atras == 1 else f"vencido hace {atras} días"
    if dias == 0:
        return "vence hoy"
    if dias == 1:
        return "vence mañana"
    return f"vence en {dias} días"


def formatear_cantidad(cantidad: float) -> str:
    """2.0 -> '2'; 1.5 -> '1,5'; 0.25 -> '0,25' (coma decimal, como se escribe en español)."""
    if float(cantidad).is_integer():
        return str(int(cantidad))
    return f"{cantidad:.3f}".rstrip("0").rstrip(".").replace(".", ",")


_SINGULAR = {"unidades": "unidad", "paquetes": "paquete", "tazas": "taza", "latas": "lata"}


def texto_cantidad(cantidad: float, unidad: str) -> str:
    """'1 paquete', '2 paquetes', '1,5 L': concuerda la unidad con la cantidad."""
    if cantidad == 1:
        unidad = _SINGULAR.get(unidad, unidad)
    return f"{formatear_cantidad(cantidad)} {unidad}"


def formatear_fecha(fecha: date) -> str:
    return fecha.strftime("%d/%m/%Y")


def normalizar(texto: str) -> str:
    """Minúsculas, sin acentos y con espacios simples: 'Limón  ' -> 'limon'."""
    sin_acentos = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )
    return " ".join(sin_acentos.lower().split())
