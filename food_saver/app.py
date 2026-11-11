"""Interfaz gráfica de Food Saver (tkinter, incluido con Python: no requiere instalar nada).

Pantalla:
  ┌ Formulario: nombre · cantidad · unidad · vencimiento · [Agregar] ┐
  ├ Izquierda ─────────────────────┬ Derecha ───────────────────────┤
  │ Ingredientes vigentes          │ Recetas sugeridas              │
  │ (ordenados por vencimiento)    │ (usan solo ingredientes no     │
  │ Ingredientes vencidos (aparte) │  vencidos) + detalle de receta │
  └────────────────────────────────┴────────────────────────────────┘

Este archivo SOLO arma la pantalla y conecta botones; las reglas están en modelo.py
y logica.py, y el guardado en almacenamiento.py.
"""
from __future__ import annotations

import sys
import tkinter as tk
import tkinter.font as tkfont
import traceback
from datetime import date
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable

from . import almacenamiento
from .ejemplos import ingredientes_de_ejemplo
from .logica import Sugerencia, clasificar, sugerir_recetas
from .modelo import (
    DIAS_POR_VENCER,
    UNIDADES,
    ErrorValidacion,
    Ingrediente,
    crear_ingrediente,
    describir_vencimiento,
    dias_para_vencer,
    esta_por_vencer,
    formatear_cantidad,
    formatear_fecha,
    texto_cantidad,
)
from .recetas import RECETAS

COLOR_ERROR = "#b00020"
COLOR_OK = "#1b6e2e"
FONDO_POR_VENCER = "#fff3cd"
FONDO_VENCIDO = "#f8d7da"
TEXTO_VENCIDO = "#842029"


class AplicacionFoodSaver:
    """Ventana principal. ``hoy_fn`` permite fijar la fecha en las pruebas."""

    def __init__(
        self,
        raiz: tk.Tk,
        ruta_datos: Path | None = None,
        hoy_fn: Callable[[], date] = date.today,
    ):
        self.raiz = raiz
        self.hoy_fn = hoy_fn
        self.ruta = Path(ruta_datos) if ruta_datos else almacenamiento.ruta_por_defecto()

        self.ingredientes, aviso_carga = almacenamiento.cargar(self.ruta)
        self.id_en_edicion: str | None = None      # id del ingrediente que se está editando
        self._sugerencias: dict[str, Sugerencia] = {}  # iid de la tabla de recetas -> sugerencia
        self._dia_mostrado = hoy_fn()

        self._configurar_ventana()
        self._construir_formulario()
        self._construir_columna_ingredientes()
        self._construir_columna_recetas()
        self.refrescar()

        if aviso_carga:
            # Después de dibujar la ventana, para que el aviso aparezca encima de ella.
            self.raiz.after(100, lambda: messagebox.showwarning("Datos guardados", aviso_carga))
        # Si la app queda abierta pasada la medianoche, los "días restantes" cambian.
        self.raiz.after(60_000, self._vigilar_cambio_de_dia)

    # ------------------------------------------------------------------ #
    # Construcción de la pantalla
    # ------------------------------------------------------------------ #
    def _configurar_ventana(self) -> None:
        self.raiz.title("Food Saver — aprovecha tus ingredientes antes de que venzan")
        # Factor de zoom de la pantalla (1.0 = 100 %, 1.5 = 150 %...). Las fuentes de Tk ya
        # escalan solas; los tamaños en píxeles (columnas, alturas) los escalamos con _px().
        self.escala = max(1.0, self.raiz.winfo_fpixels("1i") / 96)
        # La ventana nunca debe ser más grande que la pantalla (laptops de 1366x768, etc.).
        ancho = min(self._px(1200), self.raiz.winfo_screenwidth() - 40)
        alto = min(self._px(720), self.raiz.winfo_screenheight() - 100)
        self.raiz.geometry(f"{ancho}x{alto}")
        self.raiz.minsize(min(self._px(980), ancho), min(self._px(600), alto))
        self.raiz.columnconfigure(0, weight=1, uniform="columnas")
        self.raiz.columnconfigure(1, weight=1, uniform="columnas")
        self.raiz.rowconfigure(1, weight=1)

        estilo = ttk.Style(self.raiz)
        estilo.theme_use("vista" if "vista" in estilo.theme_names() else "clam")
        estilo.configure("Treeview", rowheight=self._px(26))
        estilo.configure("Accion.TButton", padding=(14, 4))

        base = tkfont.nametofont("TkDefaultFont")
        self.fuente_negrita = base.copy()
        self.fuente_negrita.configure(weight="bold")
        self.fuente_titulo = base.copy()
        self.fuente_titulo.configure(weight="bold", size=base.cget("size") + 3)

        # En un .exe sin consola los errores inesperados serían invisibles: los mostramos.
        self.raiz.report_callback_exception = self._reportar_error_inesperado

    def _px(self, pixeles: int) -> int:
        """Escala un tamaño en píxeles según el zoom de la pantalla."""
        return int(round(pixeles * self.escala))

    def _construir_formulario(self) -> None:
        self.marco_form = ttk.LabelFrame(self.raiz, text="Agregar ingrediente", padding=10)
        self.marco_form.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        self.var_nombre = tk.StringVar()
        self.var_cantidad = tk.StringVar()
        self.var_unidad = tk.StringVar(value=UNIDADES[0])
        self.var_vence = tk.StringVar()

        ttk.Label(self.marco_form, text="Ingrediente").grid(row=0, column=0, sticky="w")
        ttk.Label(self.marco_form, text="Cantidad").grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Label(self.marco_form, text="Unidad").grid(row=0, column=2, sticky="w", padx=(10, 0))
        ttk.Label(self.marco_form, text="Vence (DD/MM/AAAA)").grid(
            row=0, column=3, sticky="w", padx=(10, 0)
        )

        self.entrada_nombre = ttk.Entry(self.marco_form, textvariable=self.var_nombre, width=30)
        self.entrada_cantidad = ttk.Entry(self.marco_form, textvariable=self.var_cantidad, width=9)
        self.combo_unidad = ttk.Combobox(
            self.marco_form, textvariable=self.var_unidad, values=UNIDADES, state="readonly", width=10
        )
        self.entrada_vence = ttk.Entry(self.marco_form, textvariable=self.var_vence, width=14)

        self.entrada_nombre.grid(row=1, column=0, sticky="ew")
        self.entrada_cantidad.grid(row=1, column=1, sticky="w", padx=(10, 0))
        self.combo_unidad.grid(row=1, column=2, sticky="w", padx=(10, 0))
        self.entrada_vence.grid(row=1, column=3, sticky="w", padx=(10, 0))

        self.boton_guardar = ttk.Button(
            self.marco_form, text="Agregar", style="Accion.TButton", command=self._enviar_formulario
        )
        self.boton_guardar.grid(row=1, column=4, padx=(16, 0))
        self.boton_cancelar = ttk.Button(
            self.marco_form, text="Cancelar edición", command=self._cancelar_edicion
        )
        self.boton_cancelar.grid(row=1, column=5, padx=(6, 0))
        self.boton_cancelar.grid_remove()  # solo se ve mientras se edita

        self.etiqueta_mensaje = ttk.Label(self.marco_form, text="", wraplength=self._px(950))
        self.etiqueta_mensaje.grid(row=2, column=0, columnspan=6, sticky="w", pady=(8, 0))
        self.marco_form.columnconfigure(0, weight=1)

        # Enter en cualquier campo equivale a pulsar el botón.
        for entrada in (self.entrada_nombre, self.entrada_cantidad, self.entrada_vence):
            entrada.bind("<Return>", self._enviar_formulario)
        self.combo_unidad.bind("<Return>", self._enviar_formulario)

        self._campos = {
            "nombre": self.entrada_nombre,
            "cantidad": self.entrada_cantidad,
            "unidad": self.combo_unidad,
            "vencimiento": self.entrada_vence,
        }
        self.entrada_nombre.focus_set()

    def _construir_columna_ingredientes(self) -> None:
        izquierda = ttk.Frame(self.raiz)
        izquierda.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 10))
        izquierda.columnconfigure(0, weight=1)
        izquierda.rowconfigure(0, weight=3)
        izquierda.rowconfigure(1, weight=2)

        self.marco_vigentes, self.tabla_vigentes = self._crear_tabla(izquierda, fila=0)
        self.marco_vencidos, self.tabla_vencidos = self._crear_tabla(izquierda, fila=1)

        # Colores por estado (el texto de la columna "Estado" también lo indica, no solo el color).
        self.tabla_vigentes.tag_configure("por_vencer", background=FONDO_POR_VENCER)
        self.tabla_vencidos.tag_configure(
            "vencido", background=FONDO_VENCIDO, foreground=TEXTO_VENCIDO
        )

        barra = ttk.Frame(izquierda)
        barra.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.boton_editar = ttk.Button(barra, text="Editar", command=self._editar_seleccionado)
        self.boton_eliminar = ttk.Button(barra, text="Eliminar", command=self._eliminar_seleccionado)
        self.boton_editar.pack(side="left")
        self.boton_eliminar.pack(side="left", padx=(6, 0))
        ttk.Button(barra, text="Borrar todo", command=self._borrar_todo).pack(side="right")
        ttk.Button(barra, text="Cargar ejemplo", command=self._cargar_ejemplo).pack(
            side="right", padx=(0, 6)
        )
        self._actualizar_botones()

    def _crear_tabla(self, padre: ttk.Frame, fila: int) -> tuple[ttk.LabelFrame, ttk.Treeview]:
        marco = ttk.LabelFrame(padre, padding=6)
        marco.grid(row=fila, column=0, sticky="nsew", pady=(0, 6))
        marco.columnconfigure(0, weight=1)
        marco.rowconfigure(0, weight=1)

        columnas = ("nombre", "cantidad", "vence", "estado")
        tabla = ttk.Treeview(marco, columns=columnas, show="headings", selectmode="browse", height=6)
        for columna, titulo, ancho, ancla in (
            ("nombre", "Ingrediente", 140, "w"),
            ("cantidad", "Cantidad", 100, "e"),
            ("vence", "Vence", 90, "center"),
            ("estado", "Estado", 180, "w"),
        ):
            tabla.heading(columna, text=titulo)
            tabla.column(
                columna, width=self._px(ancho), anchor=ancla, stretch=(columna in ("nombre", "estado"))
            )
        barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        tabla.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")

        tabla.bind("<<TreeviewSelect>>", lambda _e, t=tabla: self._al_seleccionar(t))
        tabla.bind("<Double-1>", lambda _e: self._editar_seleccionado())
        tabla.bind("<Delete>", lambda _e: self._eliminar_seleccionado())
        return marco, tabla

    def _construir_columna_recetas(self) -> None:
        derecha = ttk.LabelFrame(self.raiz, text="Recetas sugeridas", padding=6)
        derecha.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=(0, 10))
        derecha.columnconfigure(0, weight=1)
        derecha.rowconfigure(1, weight=2)
        derecha.rowconfigure(2, weight=3)

        self.var_solo_completas = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            derecha,
            text="Mostrar solo recetas que puedo cocinar ya (sin ingredientes faltantes)",
            variable=self.var_solo_completas,
            command=self._refrescar_recetas,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        self.tabla_recetas = ttk.Treeview(
            derecha, columns=("receta", "tienes", "urgente"), show="headings",
            selectmode="browse", height=5,
        )
        for columna, titulo, ancho, ancla in (
            ("receta", "Receta", 200, "w"),
            ("tienes", "Tienes", 75, "center"),
            ("urgente", "Aprovecha", 200, "w"),
        ):
            self.tabla_recetas.heading(columna, text=titulo)
            self.tabla_recetas.column(
                columna, width=self._px(ancho), anchor=ancla, stretch=(columna in ("receta", "urgente"))
            )
        self.tabla_recetas.tag_configure("urgente", background=FONDO_POR_VENCER)
        barra_recetas = ttk.Scrollbar(derecha, orient="vertical", command=self.tabla_recetas.yview)
        self.tabla_recetas.configure(yscrollcommand=barra_recetas.set)
        self.tabla_recetas.grid(row=1, column=0, sticky="nsew")
        barra_recetas.grid(row=1, column=1, sticky="ns")
        self.tabla_recetas.bind("<<TreeviewSelect>>", lambda _e: self._mostrar_detalle())

        self.texto_detalle = tk.Text(
            derecha, wrap="word", height=12, relief="flat", padx=8, pady=8,
            background="#fafafa", state="disabled", cursor="arrow",
            font="TkDefaultFont",  # por defecto Text usa una letra monoespaciada
        )
        barra_detalle = ttk.Scrollbar(derecha, orient="vertical", command=self.texto_detalle.yview)
        self.texto_detalle.configure(yscrollcommand=barra_detalle.set)
        self.texto_detalle.tag_configure("titulo", font=self.fuente_titulo, spacing3=4)
        self.texto_detalle.tag_configure("negrita", font=self.fuente_negrita, spacing1=8)
        self.texto_detalle.tag_configure("bueno", foreground=COLOR_OK, font=self.fuente_negrita)
        self.texto_detalle.tag_configure("alerta", foreground="#9a5b00", font=self.fuente_negrita)
        self.texto_detalle.tag_configure("falta", foreground=COLOR_ERROR)
        self.texto_detalle.tag_configure("suave", foreground="#666666")
        self.texto_detalle.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        barra_detalle.grid(row=2, column=1, sticky="ns", pady=(8, 0))

    # ------------------------------------------------------------------ #
    # Mensajes y foco
    # ------------------------------------------------------------------ #
    def _mostrar_mensaje(self, texto: str, error: bool = False) -> None:
        self.etiqueta_mensaje.configure(text=texto, foreground=COLOR_ERROR if error else COLOR_OK)

    def _reportar_error_inesperado(self, tipo, valor, rastro) -> None:
        detalle = "".join(traceback.format_exception(tipo, valor, rastro))
        try:  # guardamos el detalle técnico para poder depurar después
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(self.ruta.parent / "errores.log", "a", encoding="utf-8") as archivo:
                archivo.write(f"--- {date.today()} ---\n{detalle}\n")
        except OSError:
            pass
        messagebox.showerror(
            "Error inesperado",
            f"Algo salió mal, pero tus datos guardados no se perdieron.\n\n{valor}",
        )

    # ------------------------------------------------------------------ #
    # Formulario: agregar / editar
    # ------------------------------------------------------------------ #
    def _enviar_formulario(self, _evento=None) -> None:
        try:
            ingrediente = crear_ingrediente(
                self.var_nombre.get(),
                self.var_cantidad.get(),
                self.var_unidad.get(),
                self.var_vence.get(),
                id=self.id_en_edicion,  # None al agregar -> se genera un id nuevo
            )
        except ErrorValidacion as error:
            # Dato inválido: no se guarda nada, se explica qué corregir y se enfoca ese campo.
            self._mostrar_mensaje(str(error), error=True)
            self._campos.get(error.campo, self.entrada_nombre).focus_set()
            return

        if self.id_en_edicion:
            self.ingredientes = [
                ingrediente if i.id == self.id_en_edicion else i for i in self.ingredientes
            ]
            mensaje = f"«{ingrediente.nombre}» actualizado."
        else:
            self.ingredientes.append(ingrediente)
            mensaje = f"«{ingrediente.nombre}» agregado."

        self._guardar()
        self._salir_de_edicion()
        self._limpiar_formulario()
        self.refrescar(seleccionar=ingrediente.id)
        self._mostrar_mensaje(mensaje)
        self.entrada_nombre.focus_set()

    def _limpiar_formulario(self) -> None:
        self.var_nombre.set("")
        self.var_cantidad.set("")
        self.var_unidad.set(UNIDADES[0])
        self.var_vence.set("")

    def _entrar_en_edicion(self, ingrediente: Ingrediente) -> None:
        self.id_en_edicion = ingrediente.id
        self.var_nombre.set(ingrediente.nombre)
        self.var_cantidad.set(formatear_cantidad(ingrediente.cantidad))
        self.var_unidad.set(ingrediente.unidad)
        self.var_vence.set(formatear_fecha(ingrediente.vencimiento))
        self.marco_form.configure(text=f"Editando «{ingrediente.nombre}»")
        self.boton_guardar.configure(text="Guardar cambios")
        self.boton_cancelar.grid()
        self._mostrar_mensaje("")
        self.entrada_nombre.focus_set()

    def _salir_de_edicion(self) -> None:
        self.id_en_edicion = None
        self.marco_form.configure(text="Agregar ingrediente")
        self.boton_guardar.configure(text="Agregar")
        self.boton_cancelar.grid_remove()

    def _cancelar_edicion(self) -> None:
        self._salir_de_edicion()
        self._limpiar_formulario()
        self._mostrar_mensaje("")

    # ------------------------------------------------------------------ #
    # Selección y acciones sobre la lista
    # ------------------------------------------------------------------ #
    def _al_seleccionar(self, tabla: ttk.Treeview) -> None:
        if not tabla.selection():
            return
        otra = self.tabla_vencidos if tabla is self.tabla_vigentes else self.tabla_vigentes
        if otra.selection():  # una sola selección a la vez entre las dos tablas
            otra.selection_remove(otra.selection())
        self._actualizar_botones()

    def _id_seleccionado(self) -> str | None:
        for tabla in (self.tabla_vigentes, self.tabla_vencidos):
            seleccion = tabla.selection()
            if seleccion:
                return seleccion[0]
        return None

    def _ingrediente_por_id(self, id_: str | None) -> Ingrediente | None:
        return next((i for i in self.ingredientes if i.id == id_), None)

    def _actualizar_botones(self) -> None:
        estado = "normal" if self._id_seleccionado() else "disabled"
        self.boton_editar.configure(state=estado)
        self.boton_eliminar.configure(state=estado)

    def _editar_seleccionado(self) -> None:
        ingrediente = self._ingrediente_por_id(self._id_seleccionado())
        if ingrediente:
            self._entrar_en_edicion(ingrediente)

    def _eliminar_seleccionado(self) -> None:
        ingrediente = self._ingrediente_por_id(self._id_seleccionado())
        if not ingrediente:
            return
        if not messagebox.askyesno("Eliminar ingrediente", f"¿Eliminar «{ingrediente.nombre}»?"):
            return
        self.ingredientes = [i for i in self.ingredientes if i.id != ingrediente.id]
        if self.id_en_edicion == ingrediente.id:
            self._cancelar_edicion()
        self._guardar()
        self.refrescar()
        self._mostrar_mensaje(f"«{ingrediente.nombre}» eliminado.")

    def _cargar_ejemplo(self) -> None:
        nuevos = ingredientes_de_ejemplo(self.hoy_fn())
        self.ingredientes.extend(nuevos)
        self._guardar()
        self.refrescar()
        self._mostrar_mensaje(f"Se agregaron {len(nuevos)} ingredientes de ejemplo.")

    def _borrar_todo(self) -> None:
        if not self.ingredientes:
            return
        if not messagebox.askyesno(
            "Borrar todo", f"¿Borrar los {len(self.ingredientes)} ingredientes guardados?"
        ):
            return
        self.ingredientes = []
        self._cancelar_edicion()
        self._guardar()
        self.refrescar()
        self._mostrar_mensaje("Se borraron todos los ingredientes.")

    # ------------------------------------------------------------------ #
    # Guardado
    # ------------------------------------------------------------------ #
    def _guardar(self) -> bool:
        try:
            almacenamiento.guardar(self.ruta, self.ingredientes)
            return True
        except OSError as error:
            messagebox.showerror(
                "No se pudo guardar",
                f"No se pudieron guardar los datos en:\n{self.ruta}\n\n{error}\n\n"
                "Los cambios siguen en pantalla mientras no cierres la aplicación.",
            )
            return False

    # ------------------------------------------------------------------ #
    # Dibujar tablas y recetas
    # ------------------------------------------------------------------ #
    def refrescar(self, seleccionar: str | None = None) -> None:
        """Redibuja todo a partir de self.ingredientes (única fuente de verdad)."""
        hoy = self.hoy_fn()
        self._dia_mostrado = hoy
        id_a_seleccionar = seleccionar or self._id_seleccionado()
        vigentes, vencidos = clasificar(self.ingredientes, hoy)

        self.marco_vigentes.configure(
            text=f"Ingredientes vigentes ({len(vigentes)}) — ordenados: el que vence primero, arriba"
        )
        self.marco_vencidos.configure(
            text=f"Vencidos ({len(vencidos)}) — no se usan en las recetas"
        )
        self._llenar_tabla(self.tabla_vigentes, vigentes, hoy)
        self._llenar_tabla(self.tabla_vencidos, vencidos, hoy)

        for tabla in (self.tabla_vigentes, self.tabla_vencidos):
            if id_a_seleccionar and tabla.exists(id_a_seleccionar):
                tabla.selection_set(id_a_seleccionar)
                tabla.see(id_a_seleccionar)
        self._actualizar_botones()
        self._refrescar_recetas()

    def _llenar_tabla(self, tabla: ttk.Treeview, ingredientes: list[Ingrediente], hoy: date) -> None:
        tabla.delete(*tabla.get_children())
        for ing in ingredientes:
            dias = dias_para_vencer(ing, hoy)
            estado = describir_vencimiento(dias).capitalize()
            etiquetas: tuple[str, ...] = ()
            if dias < 0:
                etiquetas = ("vencido",)
            elif esta_por_vencer(ing, hoy):
                estado = f"⚠ {estado}"
                etiquetas = ("por_vencer",)
            tabla.insert(
                "", "end", iid=ing.id, tags=etiquetas,
                values=(
                    ing.nombre,
                    texto_cantidad(ing.cantidad, ing.unidad),
                    formatear_fecha(ing.vencimiento),
                    estado,
                ),
            )

    def _refrescar_recetas(self) -> None:
        hoy = self.hoy_fn()
        sugerencias = sugerir_recetas(
            self.ingredientes, RECETAS, hoy, solo_completas=self.var_solo_completas.get()
        )
        recordada = self._nombre_receta_seleccionada()

        self.tabla_recetas.delete(*self.tabla_recetas.get_children())
        self._sugerencias = {}
        for numero, sug in enumerate(sugerencias):
            iid = f"receta{numero}"
            self._sugerencias[iid] = sug
            urgente = ""
            if sug.dias_mas_urgente <= DIAS_POR_VENCER:
                uso = sug.uso_mas_urgente
                urgente = f"{uso.lote.nombre} ({describir_vencimiento(uso.dias).replace('vence ', '')})"
            self.tabla_recetas.insert(
                "", "end", iid=iid, tags=("urgente",) if urgente else (),
                values=(
                    sug.receta.nombre,
                    f"{len(sug.usados)} de {len(sug.usados) + len(sug.faltantes)}",
                    urgente,
                ),
            )

        # Mantener la receta que se estaba viendo; si no existe, mostrar la primera.
        elegida = next(
            (iid for iid, s in self._sugerencias.items() if s.receta.nombre == recordada),
            next(iter(self._sugerencias), None),
        )
        if elegida:
            self.tabla_recetas.selection_set(elegida)
        self._mostrar_detalle()

    def _nombre_receta_seleccionada(self) -> str | None:
        seleccion = self.tabla_recetas.selection()
        sug = self._sugerencias.get(seleccion[0]) if seleccion else None
        return sug.receta.nombre if sug else None

    def _escribir_detalle(self, partes: list[tuple[str, str]]) -> None:
        """Reemplaza el contenido del panel de detalle. partes = [(texto, etiqueta), ...]."""
        self.texto_detalle.configure(state="normal")
        self.texto_detalle.delete("1.0", "end")
        for texto, etiqueta in partes:
            self.texto_detalle.insert("end", texto, etiqueta)
        self.texto_detalle.configure(state="disabled")

    def _mostrar_detalle(self) -> None:
        seleccion = self.tabla_recetas.selection()
        sug = self._sugerencias.get(seleccion[0]) if seleccion else None

        if sug is None:
            if not self.ingredientes:
                mensaje = "Agrega ingredientes (o pulsa «Cargar ejemplo») para ver recetas sugeridas."
            elif self.var_solo_completas.get():
                mensaje = "Ninguna receta se puede cocinar completa con lo que tienes vigente.\nDesmarca la casilla para ver recetas con ingredientes faltantes."
            else:
                mensaje = "Ninguna receta usa tus ingredientes vigentes.\nRevisa la lista de vencidos o agrega más ingredientes."
            self._escribir_detalle([(mensaje, "suave")])
            return

        partes: list[tuple[str, str]] = [(sug.receta.nombre + "\n", "titulo")]
        if sug.completa:
            partes.append(("✔ Tienes todos los ingredientes: puedes cocinarla ya.\n", "bueno"))
        else:
            partes.append((f"Te faltan {len(sug.faltantes)} ingrediente(s).\n", "alerta"))

        partes.append(("\nLo que usarías de tu despensa\n", "negrita"))
        for uso in sorted(sug.usados, key=lambda u: u.dias):
            lote = uso.lote
            partes.append((
                f"  • {lote.nombre} ({texto_cantidad(lote.cantidad, lote.unidad)}) "
                f"— {describir_vencimiento(uso.dias)}\n",
                "alerta" if uso.dias <= DIAS_POR_VENCER else "",
            ))

        if sug.faltantes:
            partes.append(("\nTe faltan\n", "negrita"))
            for nombre in sug.faltantes:
                nota = "  (lo tienes, pero está vencido)" if nombre in sug.descartados_por_vencidos else ""
                partes.append((f"  • {nombre.capitalize()}{nota}\n", "falta"))

        partes.append(("\nPreparación\n", "negrita"))
        for numero, paso in enumerate(sug.receta.instrucciones, start=1):
            partes.append((f"  {numero}. {paso}\n", ""))
        self._escribir_detalle(partes)

    # ------------------------------------------------------------------ #
    # Cambio de día con la app abierta
    # ------------------------------------------------------------------ #
    def _vigilar_cambio_de_dia(self) -> None:
        if self.hoy_fn() != self._dia_mostrado:
            self.refrescar()
        self.raiz.after(60_000, self._vigilar_cambio_de_dia)


def _activar_dpi_alto() -> None:
    """En Windows evita que la ventana se vea borrosa en pantallas de alta resolución."""
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:  # noqa: BLE001 - es solo cosmético, nunca debe impedir abrir la app
            pass


def main() -> None:
    _activar_dpi_alto()
    raiz = tk.Tk()
    AplicacionFoodSaver(raiz)
    raiz.mainloop()
