"""Food Saver con la apariencia renovada.

IMPORTANTE: la clase de abajo HEREDA de AplicacionFoodSaver (app.py) y no reemplaza ninguna
de sus funciones: agregar, editar, eliminar, validar, ordenar, sugerir recetas y guardar
funcionan exactamente igual, porque es el mismo código. Lo único que hace es, una vez
construida la ventana original, cambiar cómo se ve:

  * paleta de colores y tipografía (tema.py)
  * encabezado con el logo y un resumen: cuántos ingredientes hay, por vencer y vencidos
  * tarjetas blancas, botones con jerarquía (principal / normal / peligro) y tablas más aireadas
  * mensajes de éxito y de error en una caja de color, más visibles que el texto suelto

Los únicos métodos que se extienden son `refrescar` (para actualizar el resumen del
encabezado) y `_mostrar_mensaje` (para colorear la caja del mensaje); ambos llaman primero a
la versión original con `super()`. app.py no se modifica: si algo de la apariencia fallara,
se puede abrir la versión original con `python main.py --clasico`.
"""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from datetime import date
from pathlib import Path
from typing import Callable

from . import tema
from .app import AplicacionFoodSaver, _activar_dpi_alto
from .icono import ICONO_PNG_BASE64
from .modelo import esta_por_vencer, esta_vencido


def _plural(cantidad: int, singular: str, plural: str) -> str:
    return f"{cantidad} {singular if cantidad == 1 else plural}"


class AplicacionFoodSaverVisual(AplicacionFoodSaver):
    """La misma aplicación (hereda todo su comportamiento) con la apariencia nueva."""

    _chips: dict[str, tk.Label] | None = None  # se crean al armar el encabezado

    def __init__(
        self,
        raiz: tk.Tk,
        ruta_datos: Path | None = None,
        hoy_fn: Callable[[], date] = date.today,
    ):
        # 1) Se construye y se llena la ventana ORIGINAL, tal cual.
        super().__init__(raiz, ruta_datos=ruta_datos, hoy_fn=hoy_fn)
        # 2) Encima se aplica la apariencia nueva.
        self._aplicar_apariencia()
        self._actualizar_resumen()

    # ------------------------------------------------------------------ #
    # Funciones originales que se extienden (siempre llamando a la original)
    # ------------------------------------------------------------------ #
    def refrescar(self, seleccionar: str | None = None) -> None:
        super().refrescar(seleccionar)
        self._actualizar_resumen()

    def _mostrar_mensaje(self, texto: str, error: bool = False) -> None:
        super()._mostrar_mensaje(texto, error)  # pone el texto y el color de letra, como antes
        # Además, el mensaje va en una caja de color para que no pase desapercibido.
        if texto:
            fondo = tema.ROJO_FONDO if error else tema.VERDE_CLARO
            self.etiqueta_mensaje.configure(
                background=fondo, padding=(self._px(12), self._px(7))
            )
        else:
            self.etiqueta_mensaje.configure(background=tema.FONDO, padding=0)

    # ------------------------------------------------------------------ #
    # Apariencia
    # ------------------------------------------------------------------ #
    def _aplicar_apariencia(self) -> None:
        px = self._px
        tema.aplicar_estilos(self.raiz, self.escala)
        self._crear_fuentes()
        self._poner_icono()

        # Tarjetas: el formulario, las dos tablas de ingredientes y el panel de recetas.
        panel_recetas = self.tabla_recetas.master
        panel_ingredientes = self.marco_vigentes.master
        tarjetas = (self.marco_form, self.marco_vigentes, self.marco_vencidos, panel_recetas)
        for tarjeta in tarjetas:
            self._pintar_tarjeta(tarjeta)
        self.marco_form.configure(padding=(px(16), px(10), px(16), px(14)))
        self.marco_vigentes.configure(padding=px(10))
        self.marco_vencidos.configure(padding=px(10))
        panel_recetas.configure(padding=px(10))

        # Botones con jerarquía visual: uno principal, los demás normales y los de borrar en rojo.
        self.boton_guardar.configure(style="Primario.TButton")
        self.boton_eliminar.configure(style="Peligro.TButton")
        for boton in self.boton_editar.master.winfo_children():
            if boton.cget("text") == "Borrar todo":
                boton.configure(style="Peligro.TButton")

        # El mensaje bajo el formulario: más grande y en negrita.
        self.etiqueta_mensaje.configure(font=self.fuente_negrita)
        self._mostrar_mensaje("")

        # Colores de las filas (por vencer / vencido / receta que aprovecha algo urgente).
        self.tabla_vigentes.tag_configure(
            "por_vencer", background=tema.AMBAR_FONDO, foreground=tema.AMBAR_TEXTO
        )
        self.tabla_vencidos.tag_configure(
            "vencido", background=tema.ROJO_FONDO, foreground=tema.ROJO_TEXTO
        )
        self.tabla_recetas.tag_configure(
            "urgente", background=tema.AMBAR_FONDO, foreground=tema.AMBAR_TEXTO
        )

        # Panel de detalle de la receta.
        detalle = self.texto_detalle
        detalle.configure(
            background=tema.TARJETA, padx=px(16), pady=px(14), selectbackground=tema.SELECCION,
            selectforeground=tema.TEXTO, foreground=tema.TEXTO, spacing2=px(2),
        )
        detalle.tag_configure("titulo", foreground=tema.VERDE_OSCURO, spacing3=px(6))
        detalle.tag_configure("negrita", foreground=tema.VERDE_OSCURO, spacing1=px(12), spacing3=px(2))
        detalle.tag_configure("bueno", foreground=tema.VERDE_TEXTO)
        detalle.tag_configure("alerta", foreground=tema.AMBAR_TEXTO)
        detalle.tag_configure("falta", foreground=tema.ROJO_TEXTO)
        detalle.tag_configure("suave", foreground=tema.TEXTO_SUAVE)

        # Encabezados de columna alineados con sus datos (texto a la izquierda, números a la derecha).
        for tabla in (self.tabla_vigentes, self.tabla_vencidos):
            for columna, ancla in (("nombre", "w"), ("cantidad", "e"), ("vence", "center"), ("estado", "w")):
                tabla.heading(columna, anchor=ancla)
        for columna, ancla in (("receta", "w"), ("tienes", "center"), ("urgente", "w")):
            self.tabla_recetas.heading(columna, anchor=ancla)

        self._construir_encabezado()
        self._acomodar_ventana(panel_ingredientes, panel_recetas)

    def _crear_fuentes(self) -> None:
        """Las fuentes con nombre ya cambiaron de familia; las copias que hizo la app
        original (negrita y título) se ajustan aquí. Las etiquetas que las usan se actualizan solas."""
        familia = tkfont.nametofont("TkDefaultFont").actual("family")
        self.fuente_negrita.configure(family=familia, size=10, weight="bold")
        self.fuente_titulo.configure(family=familia, size=15, weight="bold")
        # Fuentes propias del encabezado (se guardan en atributos para que no se pierdan).
        self.fuente_marca = tkfont.Font(family=familia, size=19, weight="bold")
        self.fuente_subtitulo = tkfont.Font(family=familia, size=10)
        self.fuente_chip = tkfont.Font(family=familia, size=10, weight="bold")

    def _poner_icono(self) -> None:
        """Icono de la ventana. Es solo estético: si no se puede cargar, se sigue sin él."""
        try:
            self._icono = tk.PhotoImage(data=ICONO_PNG_BASE64)
            self.raiz.iconphoto(True, self._icono)
        except tk.TclError:
            pass

    def _pintar_tarjeta(self, widget: tk.Misc) -> None:
        """Pasa un marco y todo lo que contiene a los estilos 'Tarjeta' (fondo blanco)."""
        estilos = {
            "TLabelframe": "Tarjeta.TLabelframe",
            "TFrame": "Tarjeta.TFrame",
            "TLabel": "Tarjeta.TLabel",
            "TCheckbutton": "Tarjeta.TCheckbutton",
        }
        estilo = estilos.get(widget.winfo_class())
        if estilo:
            widget.configure(style=estilo)
        for hijo in widget.winfo_children():
            self._pintar_tarjeta(hijo)

    # ------------------------------------------------------------------ #
    # Encabezado con logo y resumen
    # ------------------------------------------------------------------ #
    def _construir_encabezado(self) -> None:
        px = self._px
        encabezado = tk.Frame(self.raiz, background=tema.VERDE_OSCURO)
        encabezado.columnconfigure(2, weight=1)  # empuja el resumen hacia la derecha

        lado = px(42)
        logo = tk.Canvas(
            encabezado, width=lado, height=lado, background=tema.VERDE_OSCURO, highlightthickness=0
        )
        logo.create_oval(1, 1, lado - 1, lado - 1, fill=tema.VERDE, outline="#4C9A6C", width=1)
        logo.create_polygon(tema.puntos_hoja(lado), fill=tema.BLANCO, outline=tema.BLANCO)
        logo.create_line(*tema.nervadura_hoja(lado), fill=tema.VERDE, width=max(1, px(2)))
        logo.grid(row=0, column=0, rowspan=2, padx=(px(18), px(12)), pady=px(10))

        tk.Label(
            encabezado, text="Food Saver", font=self.fuente_marca,
            background=tema.VERDE_OSCURO, foreground=tema.BLANCO,
        ).grid(row=0, column=1, sticky="sw", pady=(px(8), 0))
        tk.Label(
            encabezado, text="Aprovecha tus ingredientes antes de que venzan",
            font=self.fuente_subtitulo, background=tema.VERDE_OSCURO, foreground=tema.SUBTITULO_ENCABEZADO,
        ).grid(row=1, column=1, sticky="nw", pady=(0, px(8)))

        # Resumen: tres «chips» que se actualizan cada vez que cambian los datos.
        resumen = tk.Frame(encabezado, background=tema.VERDE_OSCURO)
        resumen.grid(row=0, column=3, rowspan=2, padx=(0, px(18)))
        self._chips = {}
        for numero, (clave, fondo, letra) in enumerate((
            ("vigentes", tema.VERDE_CLARO, tema.VERDE_OSCURO),
            ("por_vencer", tema.AMBAR_FONDO, tema.AMBAR_TEXTO),
            ("vencidos", tema.ROJO_FONDO, tema.ROJO_TEXTO),
        )):
            chip = tk.Label(
                resumen, text="", font=self.fuente_chip, background=fondo, foreground=letra,
                padx=px(14), pady=px(6),
            )
            chip.grid(row=0, column=numero, padx=(0 if numero == 0 else px(8), 0))
            self._chips[clave] = chip

        self.encabezado = encabezado  # _acomodar_ventana lo coloca en la fila 0

    def _actualizar_resumen(self) -> None:
        if self._chips is None:  # la app original llama a refrescar() antes de existir el encabezado
            return
        hoy = self.hoy_fn()
        vigentes = [i for i in self.ingredientes if not esta_vencido(i, hoy)]
        por_vencer = [i for i in vigentes if esta_por_vencer(i, hoy)]
        vencidos = len(self.ingredientes) - len(vigentes)
        self._chips["vigentes"].configure(text=_plural(len(vigentes), "vigente", "vigentes"))
        self._chips["por_vencer"].configure(text=_plural(len(por_vencer), "por vencer", "por vencer"))
        self._chips["vencidos"].configure(text=_plural(vencidos, "vencido", "vencidos"))

    # ------------------------------------------------------------------ #
    # Distribución general
    # ------------------------------------------------------------------ #
    def _acomodar_ventana(self, panel_ingredientes: tk.Misc, panel_recetas: tk.Misc) -> None:
        """Baja una fila todo lo que ya estaba en la ventana y pone el encabezado arriba."""
        px = self._px
        # El encabezado ocupa altura: la ventana inicial es un poco más alta que la original
        # (sin pasarse del tamaño de la pantalla).
        ancho = min(px(1240), self.raiz.winfo_screenwidth() - 40)
        alto = min(px(860), self.raiz.winfo_screenheight() - 90)
        self.raiz.geometry(f"{ancho}x{alto}")
        self.raiz.minsize(min(px(1000), ancho), min(px(640), alto))

        for widget in self.raiz.grid_slaves():
            widget.grid_configure(row=int(widget.grid_info()["row"]) + 1)
        self.raiz.rowconfigure(1, weight=0)
        self.raiz.rowconfigure(2, weight=1)  # el contenido es lo que crece al agrandar la ventana

        self.encabezado.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.marco_form.grid_configure(padx=px(16), pady=(px(14), px(10)))
        panel_ingredientes.grid_configure(padx=(px(16), px(8)), pady=(0, px(16)))
        panel_recetas.grid_configure(padx=(px(8), px(16)), pady=(0, px(16)))


def main(clasico: bool = False) -> None:
    """Abre la app. Con clasico=True abre la versión original, sin la apariencia nueva."""
    _activar_dpi_alto()
    raiz = tk.Tk()
    (AplicacionFoodSaver if clasico else AplicacionFoodSaverVisual)(raiz)
    raiz.mainloop()
