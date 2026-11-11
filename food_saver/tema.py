"""Apariencia de Food Saver: paleta de colores, tipografía y estilos de los widgets.

Este módulo SOLO define cómo se ve la aplicación. No contiene reglas de negocio ni
toca datos. La clase que lo aplica es AplicacionFoodSaverVisual (app_visual.py), que
hereda de la aplicación original sin modificar ninguna de sus funciones.

Todos los pares de colores texto/fondo cumplen contraste AA (>= 4,5:1) para que se lea
bien en un proyector o una pantalla con poco brillo.
"""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

# --------------------------------------------------------------------------- #
# Paleta
# --------------------------------------------------------------------------- #
FONDO = "#EEF3EE"          # fondo de la ventana y de las tarjetas (verde grisáceo suave)
TARJETA = "#FFFFFF"        # superficie de tablas, campos de texto y botones
BORDE = "#D7E1D9"
BORDE_TARJETA = "#C9D6CC"   # borde de las tarjetas
BORDE_BOTON = "#B4C5B9"    # un poco más oscuro que BORDE para que los botones se distingan
TEXTO = "#1E2B24"
TEXTO_SUAVE = "#5C6A62"

VERDE = "#2E7D4F"          # color principal (botón principal, foco)
VERDE_HOVER = "#256A42"
VERDE_OSCURO = "#1F5B3A"   # encabezado y títulos
VERDE_TEXTO = "#1B6E2E"    # texto verde sobre fondo claro (mismo verde que usa la app original)
VERDE_CLARO = "#E3F1E7"    # mensajes de éxito, chips
SELECCION = "#CFE8D8"      # fila seleccionada
CABECERA_TABLA = "#E9F1EB"

AMBAR_FONDO = "#FFF1D6"    # por vencer
AMBAR_TEXTO = "#8A4B00"
ROJO = "#B3261E"
ROJO_FONDO = "#FDE4E4"     # vencidos / errores
ROJO_TEXTO = "#9B1C1C"
BORDE_ROJO = "#E8B4B0"

BLANCO = "#FFFFFF"
SUBTITULO_ENCABEZADO = "#CFE6D8"


# --------------------------------------------------------------------------- #
# Logo: una hoja dibujada con curvas (se usa en el encabezado y en el icono)
# --------------------------------------------------------------------------- #
def _bezier(p0, c, p1, pasos):
    """Puntos de una curva de Bézier cuadrática de p0 a p1 con punto de control c."""
    puntos = []
    for i in range(pasos + 1):
        t = i / pasos
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t ** 2 * p1[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t ** 2 * p1[1]
        puntos.append((x, y))
    return puntos


# Coordenadas normalizadas (0..1) dentro del cuadrado del logo.
_BASE_HOJA = (0.27, 0.75)
_PUNTA_HOJA = (0.75, 0.25)


def puntos_hoja(tamano: float) -> list[tuple[float, float]]:
    """Contorno de la hoja, escalado a un cuadrado de `tamano` píxeles."""
    arriba = _bezier(_BASE_HOJA, (0.20, 0.28), _PUNTA_HOJA, 14)
    abajo = _bezier(_PUNTA_HOJA, (0.72, 0.82), _BASE_HOJA, 14)
    return [(x * tamano, y * tamano) for x, y in arriba + abajo[1:]]


def nervadura_hoja(tamano: float) -> tuple[float, float, float, float]:
    """Línea central de la hoja (x0, y0, x1, y1), escalada a `tamano` píxeles."""
    return (0.20 * tamano, 0.82 * tamano, 0.60 * tamano, 0.40 * tamano)


# --------------------------------------------------------------------------- #
# Tipografía
# --------------------------------------------------------------------------- #
def familia_de_letra(raiz: tk.Misc) -> str:
    """Segoe UI en Windows; si no existe, la letra por defecto del sistema."""
    disponibles = set(tkfont.families(raiz))
    for candidata in ("Segoe UI", "Helvetica Neue", "Noto Sans", "DejaVu Sans"):
        if candidata in disponibles:
            return candidata
    return tkfont.nametofont("TkDefaultFont").actual("family")


def configurar_fuentes(raiz: tk.Misc, familia: str) -> None:
    """Cambia las fuentes con nombre de Tk: todo lo que las use se actualiza solo."""
    for nombre in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont"):
        try:
            tkfont.nametofont(nombre, raiz).configure(family=familia, size=10)
        except tk.TclError:
            pass  # esa fuente con nombre no existe en esta plataforma


# --------------------------------------------------------------------------- #
# Estilos ttk
# --------------------------------------------------------------------------- #
def aplicar_estilos(raiz: tk.Tk, escala: float) -> ttk.Style:
    """Configura el tema 'clam' (el que permite colorear todo igual en cualquier sistema)."""

    def px(n: int) -> int:
        return int(round(n * escala))

    familia = familia_de_letra(raiz)
    configurar_fuentes(raiz, familia)
    negrita = (familia, 10, "bold")

    raiz.configure(background=FONDO)
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")

    estilo.configure(
        ".", background=FONDO, foreground=TEXTO, bordercolor=BORDE,
        lightcolor=BORDE, darkcolor=BORDE, focuscolor=VERDE, troughcolor=FONDO,
    )
    estilo.configure("TFrame", background=FONDO)
    estilo.configure("TLabel", background=FONDO, foreground=TEXTO)

    # --- Tarjetas (superficies blancas con borde fino) ---
    estilo.configure("Tarjeta.TFrame", background=FONDO)
    estilo.configure("Tarjeta.TLabel", background=FONDO, foreground=TEXTO_SUAVE, font=(familia, 9, "bold"))
    estilo.configure(
        "Tarjeta.TLabelframe", background=FONDO, bordercolor=BORDE_TARJETA,
        lightcolor=BORDE_TARJETA, darkcolor=BORDE_TARJETA, borderwidth=1, relief="solid",
    )
    # El título va sobre el fondo de la ventana (no sobre blanco), justo encima de la tarjeta.
    estilo.configure(
        "Tarjeta.TLabelframe.Label", background=FONDO, foreground=VERDE_OSCURO,
        font=(familia, 10, "bold"),
    )
    estilo.configure("Tarjeta.TCheckbutton", background=FONDO, foreground=TEXTO, focuscolor=FONDO)
    estilo.map(
        "Tarjeta.TCheckbutton",
        background=[("active", FONDO)],
        indicatorbackground=[("selected", VERDE), ("!selected", TARJETA)],
        indicatorforeground=[("selected", BLANCO)],
    )

    # --- Botones: principal (verde), normal (blanco) y de peligro (rojo suave) ---
    relleno = (px(16), px(7))
    estilo.configure(
        "TButton", background=TARJETA, foreground=TEXTO, bordercolor=BORDE_BOTON,
        lightcolor=TARJETA, darkcolor=TARJETA, padding=relleno, relief="flat",
        focuscolor=VERDE, anchor="center",
    )
    estilo.map(
        "TButton",
        background=[("disabled", "#E4EBE5"), ("pressed", SELECCION), ("active", VERDE_CLARO)],
        foreground=[("disabled", "#6A7771")],
        bordercolor=[("disabled", BORDE), ("active", VERDE)],
        lightcolor=[("pressed", SELECCION), ("active", VERDE_CLARO)],
        darkcolor=[("pressed", SELECCION), ("active", VERDE_CLARO)],
    )

    estilo.configure(
        "Primario.TButton", background=VERDE, foreground=BLANCO, bordercolor=VERDE,
        lightcolor=VERDE, darkcolor=VERDE, padding=(px(22), px(8)), font=negrita,
    )
    estilo.map(
        "Primario.TButton",
        background=[("disabled", "#A9C7B5"), ("pressed", VERDE_OSCURO), ("active", VERDE_HOVER)],
        foreground=[("disabled", BLANCO)],
        bordercolor=[("pressed", VERDE_OSCURO), ("active", VERDE_HOVER)],
        lightcolor=[("pressed", VERDE_OSCURO), ("active", VERDE_HOVER)],
        darkcolor=[("pressed", VERDE_OSCURO), ("active", VERDE_HOVER)],
    )

    estilo.configure(
        "Peligro.TButton", background=TARJETA, foreground=ROJO, bordercolor=BORDE_ROJO,
        lightcolor=TARJETA, darkcolor=TARJETA, padding=relleno,
    )
    estilo.map(
        "Peligro.TButton",
        background=[("disabled", "#E4EBE5"), ("pressed", "#F8CFCF"), ("active", ROJO_FONDO)],
        foreground=[("disabled", "#6A7771")],
        bordercolor=[("disabled", BORDE), ("active", ROJO)],
        lightcolor=[("pressed", "#F8CFCF"), ("active", ROJO_FONDO)],
        darkcolor=[("pressed", "#F8CFCF"), ("active", ROJO_FONDO)],
    )

    # --- Campos de texto: el borde se pone verde al enfocarlos ---
    estilo.configure(
        "TEntry", fieldbackground=TARJETA, foreground=TEXTO, bordercolor=BORDE,
        lightcolor=BORDE, darkcolor=BORDE, padding=(px(8), px(6)),
        selectbackground=SELECCION, selectforeground=TEXTO, insertcolor=TEXTO,
    )
    estilo.map(
        "TEntry",
        bordercolor=[("focus", VERDE)], lightcolor=[("focus", VERDE)], darkcolor=[("focus", VERDE)],
    )
    estilo.configure(
        "TCombobox", fieldbackground=TARJETA, background=TARJETA, foreground=TEXTO,
        bordercolor=BORDE, lightcolor=BORDE, darkcolor=BORDE, arrowcolor=VERDE_OSCURO,
        padding=(px(8), px(6)), arrowsize=px(16),
        selectbackground=TARJETA, selectforeground=TEXTO,
    )
    estilo.map(
        "TCombobox",
        fieldbackground=[("readonly", TARJETA)],
        selectbackground=[("readonly", TARJETA)],
        selectforeground=[("readonly", TEXTO)],
        background=[("active", VERDE_CLARO), ("readonly", TARJETA)],
        bordercolor=[("focus", VERDE)], lightcolor=[("focus", VERDE)], darkcolor=[("focus", VERDE)],
    )
    # Lista desplegable de la unidad (es un widget clásico de Tk, se colorea por opciones).
    raiz.option_add("*TCombobox*Listbox.background", TARJETA)
    raiz.option_add("*TCombobox*Listbox.foreground", TEXTO)
    raiz.option_add("*TCombobox*Listbox.selectBackground", VERDE)
    raiz.option_add("*TCombobox*Listbox.selectForeground", BLANCO)
    raiz.option_add("*TCombobox*Listbox.font", (familia, 10))

    # --- Tablas ---
    estilo.configure(
        "Treeview", background=TARJETA, fieldbackground=TARJETA, foreground=TEXTO,
        rowheight=px(30), borderwidth=0, bordercolor=TARJETA, lightcolor=TARJETA, darkcolor=TARJETA,
    )
    estilo.map(
        "Treeview",
        background=[("selected", SELECCION)], foreground=[("selected", TEXTO)],
    )
    estilo.configure(
        "Treeview.Heading", background=CABECERA_TABLA, foreground=VERDE_OSCURO, font=negrita,
        relief="flat", borderwidth=0, bordercolor=CABECERA_TABLA,
        lightcolor=CABECERA_TABLA, darkcolor=CABECERA_TABLA, padding=(px(8), px(7)),
    )
    estilo.map("Treeview.Heading", background=[("active", "#DCEBE0")])

    # --- Barras de desplazamiento: delgadas y discretas ---
    estilo.configure(
        "Vertical.TScrollbar", background="#C5D3C9", troughcolor="#EEF3EF", bordercolor="#EEF3EF",
        lightcolor="#C5D3C9", darkcolor="#C5D3C9", arrowcolor=TEXTO_SUAVE,
        gripcount=0, arrowsize=px(14),
    )
    estilo.map("Vertical.TScrollbar", background=[("active", "#9DB5A5")])
    return estilo
