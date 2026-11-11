"""Ventanas para crear y administrar las recetas propias del usuario.

* DialogoReceta: crear o editar UNA receta (nombre, ingredientes con cantidad y unidad, pasos).
* AdministradorRecetas: la lista «Mis recetas» con Nueva / Editar / Eliminar.

Las ventanas solo piden y muestran datos. TODA la validación está en recetas_usuario.py (que a su
vez reutiliza las reglas de modelo.py), y el guardado lo hace la aplicación principal
(`guardar_receta_propia`, `eliminar_receta_propia`), de modo que aquí no hay lógica de negocio.

Se ven igual que el resto de la app: usan los estilos ttk que ya estén configurados (con la
apariencia renovada o con la clásica).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from . import tema
from .logica import coincide_ingrediente
from .modelo import UNIDADES, ErrorValidacion, formatear_cantidad, texto_cantidad
from .recetas import Receta
from .recetas_usuario import MAX_INGREDIENTES, crear_receta, validar_ingrediente_receta


def _fondo() -> str:
    """Color de fondo de la ventana principal (para que los cuadros combinen con ella)."""
    return ttk.Style().lookup("TFrame", "background") or tema.FONDO


def _estilo_de(boton: tk.Misc) -> str:
    """Estilo (ttk) que usa un botón de la ventana principal; '' = el normal."""
    return str(boton.cget("style"))


class _VentanaBase(tk.Toplevel):
    """Ventana secundaria: centrada sobre la principal y, si se pide, bloqueando la de atrás."""

    def __init__(self, app, titulo: str, ancho: int, alto: int, modal: bool):
        super().__init__(app.raiz)
        self.app = app
        self.title(titulo)
        self.configure(background=_fondo())
        self.transient(app.raiz)
        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.bind("<Escape>", lambda _e: self._cerrar())
        self._ancho, self._alto, self._modal = ancho, alto, modal

    def _cerrar(self) -> None:
        """Esc, la X de la ventana y el botón Cancelar/Cerrar llegan aquí."""
        self.destroy()

    def _mostrar(self) -> None:
        """Se llama al terminar de construir: tamaño, posición y (opcional) modo modal."""
        px = self.app._px
        raiz = self.app.raiz
        raiz.update_idletasks()
        ancho = min(max(px(self._ancho), self.winfo_reqwidth()), self.winfo_screenwidth() - 40)
        alto = min(max(px(self._alto), self.winfo_reqheight()), self.winfo_screenheight() - 80)
        x = max(0, raiz.winfo_rootx() + (raiz.winfo_width() - ancho) // 2)
        y = max(0, raiz.winfo_rooty() + max(0, (raiz.winfo_height() - alto) // 3))
        self.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.minsize(min(px(560), ancho), min(px(440), alto))
        if self._modal:
            try:  # bloquea la ventana de atrás hasta cerrar esta
                self.wait_visibility()
                self.grab_set()
            except tk.TclError:
                pass  # si el sistema no lo permite, la ventana funciona igual (solo no es modal)

    def _caja_de_mensaje(self, padre: tk.Misc) -> ttk.Label:
        return ttk.Label(padre, text="", wraplength=self.app._px(560))

    def _mostrar_mensaje(self, etiqueta: ttk.Label, texto: str, error: bool = False) -> None:
        if texto:
            etiqueta.configure(
                text=texto,
                foreground=tema.ROJO_TEXTO if error else tema.VERDE_TEXTO,
                background=tema.ROJO_FONDO if error else tema.VERDE_CLARO,
                padding=(self.app._px(10), self.app._px(6)),
            )
        else:
            etiqueta.configure(text="", background=_fondo(), padding=0)


# --------------------------------------------------------------------------- #
# Crear / editar una receta
# --------------------------------------------------------------------------- #
class DialogoReceta(_VentanaBase):
    """Formulario de una receta. Si `receta` es None se crea una nueva; si no, se edita esa."""

    def __init__(self, app, receta: Receta | None = None, modal: bool = True):
        super().__init__(
            app, "Editar mi receta" if receta else "Crear mi receta", ancho=700, alto=700, modal=modal
        )
        self.receta = receta
        # Ingredientes ya agregados a la receta: (nombre, cantidad, unidad)
        self.filas: list[tuple[str, float, str]] = (
            [(n, c, u) for n, (c, u) in zip(receta.ingredientes, receta.cantidades)] if receta else []
        )
        self._fila_en_edicion: int | None = None

        self.var_nombre = tk.StringVar(value=receta.nombre if receta else "")
        self.var_ingrediente = tk.StringVar()
        self.var_cantidad = tk.StringVar()
        self.var_unidad = tk.StringVar(value=UNIDADES[0])
        self._construir()
        self._llenar_tabla()
        if receta:
            self.texto_pasos.insert("1.0", "\n".join(receta.instrucciones))
        self.entrada_nombre.focus_set()
        self._mostrar()

    # ---------------- construcción ---------------- #
    def _construir(self) -> None:
        px = self.app._px
        tarjeta = _estilo_de(self.app.marco_form)            # mismo estilo de marco que la ventana principal
        rotulo = _estilo_de(self.app.etiqueta_mensaje)       # y mismo estilo de rótulo de campo
        contenido = ttk.Frame(self, padding=px(16))
        contenido.pack(fill="both", expand=True)
        contenido.columnconfigure(0, weight=1)
        contenido.rowconfigure(2, weight=3)
        contenido.rowconfigure(3, weight=2)

        # --- Nombre ---
        marco_nombre = ttk.LabelFrame(contenido, text="Nombre de la receta", padding=px(10), style=tarjeta)
        marco_nombre.grid(row=0, column=0, sticky="ew")
        marco_nombre.columnconfigure(0, weight=1)
        self.entrada_nombre = ttk.Entry(marco_nombre, textvariable=self.var_nombre)
        self.entrada_nombre.grid(row=0, column=0, sticky="ew")

        # --- Ingredientes ---
        marco_ing = ttk.LabelFrame(contenido, text="Ingredientes necesarios", padding=px(10), style=tarjeta)
        marco_ing.grid(row=2, column=0, sticky="nsew", pady=(px(10), 0))
        marco_ing.columnconfigure(0, weight=1)
        marco_ing.rowconfigure(2, weight=1)

        fila = ttk.Frame(marco_ing)
        fila.grid(row=0, column=0, columnspan=2, sticky="ew")
        fila.columnconfigure(0, weight=1)
        ttk.Label(fila, text="Ingrediente", style=rotulo).grid(row=0, column=0, sticky="w")
        ttk.Label(fila, text="Cantidad", style=rotulo).grid(row=0, column=1, sticky="w", padx=(px(8), 0))
        ttk.Label(fila, text="Unidad", style=rotulo).grid(row=0, column=2, sticky="w", padx=(px(8), 0))
        self.entrada_ingrediente = ttk.Entry(fila, textvariable=self.var_ingrediente)
        self.entrada_cantidad = ttk.Entry(fila, textvariable=self.var_cantidad, width=9)
        self.combo_unidad = ttk.Combobox(
            fila, textvariable=self.var_unidad, values=UNIDADES, state="readonly", width=10
        )
        self.entrada_ingrediente.grid(row=1, column=0, sticky="ew")
        self.entrada_cantidad.grid(row=1, column=1, padx=(px(8), 0))
        self.combo_unidad.grid(row=1, column=2, padx=(px(8), 0))
        self.boton_agregar = ttk.Button(fila, text="Agregar ingrediente", command=self._agregar_ingrediente)
        self.boton_agregar.grid(row=1, column=3, padx=(px(8), 0))
        for campo in (self.entrada_ingrediente, self.entrada_cantidad, self.combo_unidad):
            campo.bind("<Return>", lambda _e: self._agregar_ingrediente())
        self._campos = {
            "nombre": self.entrada_nombre,
            "ingredientes": self.entrada_ingrediente,
            "cantidad": self.entrada_cantidad,
            "unidad": self.combo_unidad,
        }

        ttk.Label(
            marco_ing, text="Doble clic sobre un ingrediente de la lista para editarlo."
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(px(6), px(4)))

        self.tabla = ttk.Treeview(
            marco_ing, columns=("nombre", "cantidad"), show="headings", selectmode="browse", height=5
        )
        self.tabla.heading("nombre", text="Ingrediente", anchor="w")
        self.tabla.heading("cantidad", text="Cantidad", anchor="e")
        self.tabla.column("nombre", width=px(300), anchor="w", stretch=True)
        self.tabla.column("cantidad", width=px(140), anchor="e", stretch=False)
        barra = ttk.Scrollbar(marco_ing, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.grid(row=2, column=0, sticky="nsew")
        barra.grid(row=2, column=1, sticky="ns")
        self.tabla.bind("<Double-1>", lambda _e: self._editar_ingrediente())
        self.tabla.bind("<Delete>", lambda _e: self._quitar_ingrediente())
        self.boton_quitar = ttk.Button(marco_ing, text="Quitar seleccionado", command=self._quitar_ingrediente)
        self.boton_quitar.grid(row=3, column=0, sticky="e", pady=(px(6), 0))

        # --- Preparación ---
        marco_pasos = ttk.LabelFrame(
            contenido, text="Preparación (un paso por línea)", padding=px(10), style=tarjeta
        )
        marco_pasos.grid(row=3, column=0, sticky="nsew", pady=(px(10), 0))
        marco_pasos.columnconfigure(0, weight=1)
        marco_pasos.rowconfigure(0, weight=1)
        self.texto_pasos = tk.Text(
            marco_pasos, wrap="word", height=6, padx=px(8), pady=px(6), font="TkDefaultFont",
            relief="flat", borderwidth=0, highlightthickness=1,
            highlightbackground=tema.BORDE_BOTON, highlightcolor=tema.VERDE,
        )
        barra_pasos = ttk.Scrollbar(marco_pasos, orient="vertical", command=self.texto_pasos.yview)
        self.texto_pasos.configure(yscrollcommand=barra_pasos.set)
        self.texto_pasos.grid(row=0, column=0, sticky="nsew")
        barra_pasos.grid(row=0, column=1, sticky="ns")
        self._campos["pasos"] = self.texto_pasos

        # --- Mensaje y botones ---
        self.etiqueta_mensaje = self._caja_de_mensaje(contenido)
        self.etiqueta_mensaje.grid(row=4, column=0, sticky="w", pady=(px(10), 0))
        botones = ttk.Frame(contenido)
        botones.grid(row=5, column=0, sticky="e", pady=(px(12), 0))
        ttk.Button(botones, text="Cancelar", command=self._cerrar).pack(side="right")
        self.boton_guardar = ttk.Button(
            botones, text="Guardar receta", style=_estilo_de(self.app.boton_guardar), command=self._guardar
        )
        self.boton_guardar.pack(side="right", padx=(0, px(8)))

    def _aviso(self, texto: str, error: bool = False) -> None:
        self._mostrar_mensaje(self.etiqueta_mensaje, texto, error)

    # ---------------- ingredientes de la receta ---------------- #
    def _llenar_tabla(self) -> None:
        self.tabla.delete(*self.tabla.get_children())
        for indice, (nombre, cantidad, unidad) in enumerate(self.filas):
            self.tabla.insert("", "end", iid=str(indice), values=(nombre, texto_cantidad(cantidad, unidad)))

    def _agregar_ingrediente(self) -> None:
        try:
            fila = validar_ingrediente_receta(
                self.var_ingrediente.get(), self.var_cantidad.get(), self.var_unidad.get()
            )
        except ErrorValidacion as error:
            self._aviso(str(error), error=True)
            self._campos.get(error.campo, self.entrada_ingrediente).focus_set()
            return
        for indice, otra in enumerate(self.filas):
            if indice != self._fila_en_edicion and coincide_ingrediente(fila[0], otra[0]) \
                    and coincide_ingrediente(otra[0], fila[0]):
                self._aviso(f"«{fila[0]}» ya está en la lista de ingredientes.", error=True)
                self.entrada_ingrediente.focus_set()
                return
        if self._fila_en_edicion is None and len(self.filas) >= MAX_INGREDIENTES:
            self._aviso(f"Una receta puede tener como máximo {MAX_INGREDIENTES} ingredientes.", error=True)
            return

        if self._fila_en_edicion is None:
            self.filas.append(fila)
            self._aviso(f"«{fila[0]}» agregado a la receta.")
        else:
            self.filas[self._fila_en_edicion] = fila
            self._aviso(f"«{fila[0]}» actualizado.")
            self._salir_de_edicion()
        self.var_ingrediente.set("")
        self.var_cantidad.set("")
        self._llenar_tabla()
        self.entrada_ingrediente.focus_set()

    def _indice_seleccionado(self) -> int | None:
        seleccion = self.tabla.selection()
        return int(seleccion[0]) if seleccion else None

    def _quitar_ingrediente(self) -> None:
        indice = self._indice_seleccionado()
        if indice is None:
            self._aviso("Selecciona un ingrediente de la lista para quitarlo.", error=True)
            return
        nombre = self.filas.pop(indice)[0]
        self._salir_de_edicion()
        self._llenar_tabla()
        self._aviso(f"«{nombre}» quitado de la receta.")

    def _editar_ingrediente(self) -> None:
        indice = self._indice_seleccionado()
        if indice is None:
            return
        nombre, cantidad, unidad = self.filas[indice]
        self.var_ingrediente.set(nombre)
        self.var_cantidad.set(formatear_cantidad(cantidad))
        self.var_unidad.set(unidad)
        self._fila_en_edicion = indice
        self.boton_agregar.configure(text="Guardar cambio")
        self._aviso(f"Editando «{nombre}». Cambia lo que necesites y pulsa «Guardar cambio».")
        self.entrada_ingrediente.focus_set()

    def _salir_de_edicion(self) -> None:
        self._fila_en_edicion = None
        self.boton_agregar.configure(text="Agregar ingrediente")

    # ---------------- cerrar sin guardar ---------------- #
    def _hay_cambios(self) -> bool:
        """¿Hay algo escrito que se perdería al cerrar? (compara con la receta original si se edita)"""
        nombre = self.var_nombre.get().strip()
        pasos = self.texto_pasos.get("1.0", "end").strip()
        sin_agregar = bool(self.var_ingrediente.get().strip() or self.var_cantidad.get().strip())
        if self.receta is None:
            return bool(nombre or self.filas or pasos or sin_agregar)
        originales = [(n, c, u) for n, (c, u) in zip(self.receta.ingredientes, self.receta.cantidades)]
        return (
            sin_agregar
            or nombre != self.receta.nombre
            or self.filas != originales
            or pasos != "\n".join(self.receta.instrucciones).strip()
        )

    def _cerrar(self) -> None:
        if self._hay_cambios() and not messagebox.askyesno(
            "Cerrar sin guardar", "Tienes cambios sin guardar en esta receta.\n¿Quieres cerrar y perderlos?"
        ):
            return
        self.destroy()

    # ---------------- guardar ---------------- #
    def _guardar(self) -> None:
        # Lo escrito en el mini formulario de ingredientes y no agregado se perdería sin avisar.
        if self.var_ingrediente.get().strip() or self.var_cantidad.get().strip():
            self._aviso(
                "Tienes un ingrediente escrito que no has agregado. "
                "Pulsa «Agregar ingrediente» o borra lo escrito.",
                error=True,
            )
            self.entrada_ingrediente.focus_set()
            return
        try:
            receta = crear_receta(
                self.var_nombre.get(),
                self.filas,
                self.texto_pasos.get("1.0", "end"),
                nombres_existentes=self.app.nombres_de_recetas(excluir_id=self.receta.id if self.receta else None),
                id=self.receta.id if self.receta else None,
            )
        except ErrorValidacion as error:
            self._aviso(str(error), error=True)
            self._campos.get(error.campo, self.entrada_nombre).focus_set()
            return
        if self.app.guardar_receta_propia(receta):
            self.destroy()


# --------------------------------------------------------------------------- #
# Lista «Mis recetas»
# --------------------------------------------------------------------------- #
class AdministradorRecetas(_VentanaBase):
    """Todas las recetas del usuario, con Nueva / Editar / Eliminar."""

    def __init__(self, app, modal: bool = False):
        super().__init__(app, "Mis recetas", ancho=620, alto=460, modal=modal)
        px = app._px
        contenido = ttk.Frame(self, padding=px(16))
        contenido.pack(fill="both", expand=True)
        contenido.columnconfigure(0, weight=1)
        contenido.rowconfigure(1, weight=1)

        ttk.Label(
            contenido,
            text="Estas son las recetas que creaste. Aparecen entre las sugerencias cuando tienes "
                 "alguno de sus ingredientes en la despensa.",
            wraplength=px(560),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, px(10)))

        self.tabla = ttk.Treeview(
            contenido, columns=("nombre", "ingredientes", "pasos"), show="headings",
            selectmode="browse", height=8,
        )
        for columna, titulo, ancho, ancla in (
            ("nombre", "Receta", 280, "w"), ("ingredientes", "Ingredientes", 110, "center"),
            ("pasos", "Pasos", 80, "center"),
        ):
            self.tabla.heading(columna, text=titulo, anchor=ancla)
            self.tabla.column(columna, width=px(ancho), anchor=ancla, stretch=(columna == "nombre"))
        barra = ttk.Scrollbar(contenido, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.grid(row=1, column=0, sticky="nsew")
        barra.grid(row=1, column=1, sticky="ns")
        self.tabla.bind("<<TreeviewSelect>>", lambda _e: self._actualizar_botones())
        self.tabla.bind("<Double-1>", lambda _e: self._editar())

        self.etiqueta_vacio = ttk.Label(contenido, text="")
        self.etiqueta_vacio.grid(row=2, column=0, columnspan=2, sticky="w", pady=(px(8), 0))

        botones = ttk.Frame(contenido)
        botones.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(px(12), 0))
        self.boton_nueva = ttk.Button(
            botones, text="+ Nueva receta", style=_estilo_de(app.boton_guardar), command=self._nueva
        )
        self.boton_editar = ttk.Button(botones, text="Editar", command=self._editar)
        self.boton_eliminar = ttk.Button(
            botones, text="Eliminar", style=_estilo_de(app.boton_eliminar), command=self._eliminar
        )
        self.boton_nueva.pack(side="left")
        self.boton_editar.pack(side="left", padx=(px(8), 0))
        self.boton_eliminar.pack(side="left", padx=(px(8), 0))
        ttk.Button(botones, text="Cerrar", command=self.destroy).pack(side="right")

        self.refrescar()
        self._mostrar()

    def refrescar(self) -> None:
        seleccionada = self._id_seleccionado()
        self.tabla.delete(*self.tabla.get_children())
        recetas = sorted(self.app.recetas_propias, key=lambda r: r.nombre.lower())
        for receta in recetas:
            self.tabla.insert(
                "", "end", iid=receta.id,
                values=(receta.nombre, len(receta.ingredientes), len(receta.instrucciones)),
            )
        if seleccionada and self.tabla.exists(seleccionada):
            self.tabla.selection_set(seleccionada)
        self.etiqueta_vacio.configure(
            text="" if recetas else "Todavía no has creado ninguna receta. Pulsa «+ Nueva receta» para empezar."
        )
        self._actualizar_botones()

    def _id_seleccionado(self) -> str | None:
        seleccion = self.tabla.selection()
        return seleccion[0] if seleccion else None

    def _receta_seleccionada(self) -> Receta | None:
        id_ = self._id_seleccionado()
        return next((r for r in self.app.recetas_propias if r.id == id_), None)

    def _actualizar_botones(self) -> None:
        estado = "normal" if self._id_seleccionado() else "disabled"
        self.boton_editar.configure(state=estado)
        self.boton_eliminar.configure(state=estado)

    def _nueva(self) -> None:
        self.app.abrir_creador_de_recetas()

    def _editar(self) -> None:
        receta = self._receta_seleccionada()
        if receta:
            self.app.abrir_creador_de_recetas(receta)

    def _eliminar(self) -> None:
        receta = self._receta_seleccionada()
        if receta and messagebox.askyesno("Eliminar receta", f"¿Eliminar tu receta «{receta.nombre}»?"):
            self.app.eliminar_receta_propia(receta.id)
