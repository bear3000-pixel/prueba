"""Pruebas de la interfaz de las dos funciones nuevas:
  * fecha de vencimiento con barras automáticas (se escribe de verdad en el campo)
  * crear, editar y eliminar recetas propias (ventanas y guardado)

Se ejecutan con la versión original y con la apariencia renovada.
"""
import json
import unittest
from unittest import mock

from food_saver import app as modulo_app
from food_saver import recetas_usuario
from food_saver.app_visual import AplicacionFoodSaverVisual

from test_interfaz import BaseInterfaz, fecha


class PruebasFechaAutomatica(BaseInterfaz):
    def escribir(self, texto):
        """Escribe carácter por carácter en el campo, como lo haría una persona."""
        for caracter in texto:
            self.app.entrada_vence.insert("end", caracter)

    def test_pone_las_barras_mientras_se_escribe(self):
        self.escribir("02")
        self.assertEqual(self.app.var_vence.get(), "02/")
        self.escribir("11")
        self.assertEqual(self.app.var_vence.get(), "02/11/")
        self.escribir("2026")
        self.assertEqual(self.app.var_vence.get(), "02/11/2026")

    def test_escribiendo_solo_numeros_queda_dd_mm_aaaa(self):
        self.escribir("02112026")
        self.assertEqual(self.app.var_vence.get(), "02/11/2026")

    def test_al_borrar_no_reaparece_la_barra(self):
        self.escribir("0211")
        self.assertEqual(self.app.var_vence.get(), "02/11/")
        self.app.entrada_vence.delete(len("02/11/") - 1, "end")  # borra la última barra
        self.assertEqual(self.app.var_vence.get(), "02/11")
        self.app.entrada_vence.delete(2, "end")                  # borra «/11»
        self.assertEqual(self.app.var_vence.get(), "02")
        self.app.entrada_vence.delete(1, "end")
        self.assertEqual(self.app.var_vence.get(), "0")

    def test_no_acepta_letras(self):
        self.escribir("mañana")
        self.assertEqual(self.app.var_vence.get(), "")
        self.escribir("1a2b")
        self.assertEqual(self.app.var_vence.get(), "12/")

    def test_no_pasa_de_ocho_digitos(self):
        self.escribir("0211202699")
        self.assertEqual(self.app.var_vence.get(), "02/11/2026")

    def test_si_el_usuario_escribe_las_barras_tambien_funciona(self):
        self.escribir("2/11/2026")
        self.assertEqual(self.app.var_vence.get(), "02/11/2026")

    def test_pegar_una_fecha_iso(self):
        self.app.var_vence.set("2026-11-20")
        self.assertEqual(self.app.var_vence.get(), "20/11/2026")

    def test_agrega_el_ingrediente_con_la_fecha_escrita_sin_barras(self):
        self.app.var_nombre.set("Leche")
        self.app.var_cantidad.set("1")
        self.escribir("02112026")
        self.app._enviar_formulario()
        (ingrediente,) = self.app.ingredientes
        self.assertEqual(ingrediente.vencimiento.isoformat(), "2026-11-02")
        self.assertEqual(self.app.var_vence.get(), "")  # el formulario queda listo

    def test_avisa_en_vivo_si_la_fecha_completa_no_existe(self):
        self.escribir("31022026")  # 31 de febrero
        self.assertEqual(self.app.var_vence.get(), "31/02/2026")
        self.assertIn("Fecha no válida", self.app.etiqueta_mensaje.cget("text"))
        self.assertEqual(self.app.ingredientes, [])
        # Al corregirla, el aviso desaparece solo
        self.app.entrada_vence.delete(0, "end")
        self.escribir("28022026")
        self.assertEqual(self.app.etiqueta_mensaje.cget("text"), "")

    def test_no_pisa_otros_mensajes(self):
        self.app._mostrar_mensaje("Otro aviso importante")
        self.escribir("0211")  # fecha incompleta, no hay nada que avisar
        self.assertEqual(self.app.etiqueta_mensaje.cget("text"), "Otro aviso importante")

    def test_editar_un_ingrediente_muestra_su_fecha_con_barras(self):
        self.agregar("Leche", "1", "L", fecha(2))
        (iid,) = self.app.tabla_vigentes.get_children()
        self.app.tabla_vigentes.selection_set(iid)
        self.app._editar_seleccionado()
        self.assertEqual(self.app.var_vence.get(), fecha(2))

    def test_el_anio_incompleto_sigue_siendo_rechazado_al_agregar(self):
        self.app.var_nombre.set("Leche")
        self.app.var_cantidad.set("1")
        self.escribir("021126")  # 02/11/26: año de 2 dígitos
        self.app._enviar_formulario()
        self.assertEqual(self.app.ingredientes, [])
        self.assertIn("Fecha no válida", self.app.etiqueta_mensaje.cget("text"))


class PruebasRecetasPropias(BaseInterfaz):
    def setUp(self):
        super().setUp()
        self.app.dialogos_modales = False  # no bloquear las pruebas

    # --- ayudas ---
    def agregar_ingrediente(self, dialogo, nombre, cantidad, unidad="g"):
        dialogo.var_ingrediente.set(nombre)
        dialogo.var_cantidad.set(cantidad)
        dialogo.var_unidad.set(unidad)
        dialogo._agregar_ingrediente()

    def pasos(self, dialogo, texto):
        dialogo.texto_pasos.delete("1.0", "end")
        dialogo.texto_pasos.insert("1.0", texto)

    def crear(self, nombre="Pan casero", filas=(("Harina", "500", "g"), ("Agua", "300", "ml")),
              pasos="Mezclar todo\nAmasar\nHornear 30 minutos"):
        dialogo = self.app.abrir_creador_de_recetas()
        dialogo.var_nombre.set(nombre)
        for fila in filas:
            self.agregar_ingrediente(dialogo, *fila)
        self.pasos(dialogo, pasos)
        dialogo._guardar()
        return dialogo

    def mensaje(self, dialogo):
        return dialogo.etiqueta_mensaje.cget("text")

    # --- crear ---
    def test_crear_una_receta(self):
        dialogo = self.crear()
        self.assertFalse(dialogo.winfo_exists(), "el cuadro se cierra al guardar")
        (receta,) = self.app.recetas_propias
        self.assertEqual(receta.nombre, "Pan casero")
        self.assertEqual(receta.cantidades, ((500.0, "g"), (300.0, "ml")))
        self.assertEqual(receta.instrucciones, ("Mezclar todo", "Amasar", "Hornear 30 minutos"))
        self.assertTrue(self.app.ruta_recetas.exists())
        self.assertIn("guardada", self.app.etiqueta_mensaje.cget("text"))

    def test_las_cantidades_invalidas_no_se_agregan_a_la_receta(self):
        dialogo = self.app.abrir_creador_de_recetas()
        for cantidad in ["", "0", "-5", "abc", "1e3", "nan", "5000000"]:
            with self.subTest(cantidad=cantidad):
                self.agregar_ingrediente(dialogo, "Harina", cantidad)
                self.assertEqual(dialogo.filas, [])
                self.assertEqual(dialogo.tabla.get_children(), ())
                self.assertTrue(self.mensaje(dialogo), "debe explicar el problema")
        self.assertIn("cantidad", self.mensaje(dialogo).lower())

    def test_cantidad_vacia_dice_de_que_ingrediente_falta(self):
        dialogo = self.app.abrir_creador_de_recetas()
        self.agregar_ingrediente(dialogo, "Harina", "")
        self.assertIn("Harina", self.mensaje(dialogo))

    def test_ingredientes_invalidos_y_repetidos(self):
        dialogo = self.app.abrir_creador_de_recetas()
        self.agregar_ingrediente(dialogo, "", "5")
        self.assertIn("nombre", self.mensaje(dialogo).lower())
        self.agregar_ingrediente(dialogo, "123", "5")
        self.assertIn("letras", self.mensaje(dialogo))
        self.agregar_ingrediente(dialogo, "Harina", "5")
        self.agregar_ingrediente(dialogo, "HARINAS", "2")  # mismo ingrediente
        self.assertEqual(len(dialogo.filas), 1)
        self.assertIn("ya está", self.mensaje(dialogo))

    def test_guardar_exige_nombre_ingredientes_y_pasos(self):
        dialogo = self.app.abrir_creador_de_recetas()
        dialogo._guardar()
        self.assertIn("nombre de la receta", self.mensaje(dialogo))
        dialogo.var_nombre.set("Mi receta")
        dialogo._guardar()
        self.assertIn("al menos un ingrediente", self.mensaje(dialogo))
        self.agregar_ingrediente(dialogo, "Harina", "100")
        dialogo._guardar()
        self.assertIn("al menos un paso", self.mensaje(dialogo))
        self.assertEqual(self.app.recetas_propias, [])
        self.assertTrue(dialogo.winfo_exists(), "sigue abierto para corregir")
        self.pasos(dialogo, "Mezclar")
        dialogo._guardar()
        self.assertEqual(len(self.app.recetas_propias), 1)

    def test_no_permite_repetir_el_nombre_de_otra_receta(self):
        dialogo = self.app.abrir_creador_de_recetas()
        dialogo.var_nombre.set("omelette de queso y tomate")  # una predefinida, con otras mayúsculas
        self.agregar_ingrediente(dialogo, "Huevo", "2", "unidades")
        self.pasos(dialogo, "Cocinar")
        dialogo._guardar()
        self.assertIn("Ya existe", self.mensaje(dialogo))
        self.assertEqual(self.app.recetas_propias, [])

    def test_no_se_pierde_un_ingrediente_escrito_y_sin_agregar(self):
        dialogo = self.app.abrir_creador_de_recetas()
        dialogo.var_nombre.set("Mi receta")
        self.agregar_ingrediente(dialogo, "Harina", "100")
        self.pasos(dialogo, "Mezclar")
        dialogo.var_ingrediente.set("Azúcar")
        dialogo.var_cantidad.set("50")  # escrito, pero sin pulsar «Agregar ingrediente»
        dialogo._guardar()
        self.assertIn("no has agregado", self.mensaje(dialogo))
        self.assertEqual(self.app.recetas_propias, [])

    def test_cerrar_con_cambios_pide_confirmacion(self):
        dialogo = self.app.abrir_creador_de_recetas()
        dialogo.var_nombre.set("Receta a medias")
        modulo_app.messagebox.askyesno.reset_mock()
        modulo_app.messagebox.askyesno.return_value = False  # «no quiero perderla»
        dialogo._cerrar()
        modulo_app.messagebox.askyesno.assert_called_once()
        self.assertTrue(dialogo.winfo_exists())
        modulo_app.messagebox.askyesno.return_value = True
        dialogo._cerrar()
        self.assertFalse(dialogo.winfo_exists())
        self.assertEqual(self.app.recetas_propias, [])

    def test_cerrar_sin_cambios_no_pregunta(self):
        modulo_app.messagebox.askyesno.reset_mock()
        dialogo = self.app.abrir_creador_de_recetas()
        dialogo._cerrar()
        self.assertFalse(dialogo.winfo_exists())
        # También al abrir una receta para editarla y no tocar nada
        self.crear()
        (receta,) = self.app.recetas_propias
        modulo_app.messagebox.askyesno.reset_mock()
        dialogo = self.app.abrir_creador_de_recetas(receta)
        dialogo._cerrar()
        self.assertFalse(dialogo.winfo_exists())
        modulo_app.messagebox.askyesno.assert_not_called()

    def test_editar_y_cerrar_con_cambios_pregunta(self):
        self.crear()
        (receta,) = self.app.recetas_propias
        dialogo = self.app.abrir_creador_de_recetas(receta)
        modulo_app.messagebox.askyesno.reset_mock()
        modulo_app.messagebox.askyesno.return_value = False
        dialogo.var_nombre.set("Otro nombre")
        dialogo._cerrar()
        modulo_app.messagebox.askyesno.assert_called_once()
        self.assertTrue(dialogo.winfo_exists())

    def test_quitar_y_editar_ingredientes_de_la_receta(self):
        dialogo = self.app.abrir_creador_de_recetas()
        self.agregar_ingrediente(dialogo, "Harina", "500")
        self.agregar_ingrediente(dialogo, "Azúcar", "50")
        dialogo.tabla.selection_set("0")
        dialogo._editar_ingrediente()
        self.assertEqual((dialogo.var_ingrediente.get(), dialogo.var_cantidad.get()), ("Harina", "500"))
        self.assertEqual(dialogo.boton_agregar.cget("text"), "Guardar cambio")
        dialogo.var_cantidad.set("0")  # un cambio inválido no se aplica
        dialogo._agregar_ingrediente()
        self.assertEqual(dialogo.filas[0], ("Harina", 500.0, "g"))
        dialogo.var_cantidad.set("750")
        dialogo._agregar_ingrediente()
        self.assertEqual(dialogo.filas, [("Harina", 750.0, "g"), ("Azúcar", 50.0, "g")])
        self.assertEqual(dialogo.boton_agregar.cget("text"), "Agregar ingrediente")
        dialogo.tabla.selection_set("1")
        dialogo._quitar_ingrediente()
        self.assertEqual([f[0] for f in dialogo.filas], ["Harina"])

    # --- en las sugerencias ---
    def test_la_receta_propia_aparece_en_las_sugerencias_cuando_hay_ingredientes(self):
        self.agregar("Harina", "1", "kg", fecha(2))
        self.agregar("Agua", "1", "L", fecha(30))
        self.crear()
        filas = self.filas(self.app.tabla_recetas)
        self.assertEqual(filas[0][0], "★ Pan casero")  # además es la que aprovecha lo que vence antes
        self.assertEqual(filas[0][1], "2 de 2")
        detalle = self.app.texto_detalle.get("1.0", "end")
        self.assertIn("Receta creada por ti", detalle)
        self.assertIn("la receta pide 500 g", detalle)
        self.assertIn("Hornear 30 minutos", detalle)
        self.assertIn("Ya aparece", self.app.etiqueta_mensaje.cget("text"))

    def test_si_no_hay_ingredientes_avisa_cuando_aparecera(self):
        self.crear()
        self.assertEqual(self.filas(self.app.tabla_recetas), [])
        self.assertIn("Aparecerá en las sugerencias", self.app.etiqueta_mensaje.cget("text"))

    def test_se_compara_la_cantidad_con_la_despensa(self):
        self.agregar("Harina", "300", "g", fecha(4))
        self.agregar("Agua", "1", "L", fecha(4))
        self.crear()  # pide 500 g de harina y 300 ml de agua
        self.raiz.update()
        (fila,) = [f for f in self.filas(self.app.tabla_recetas) if "Pan casero" in f[0]]
        self.assertEqual(fila[1], "1 de 2")  # el agua alcanza (1 L ≥ 300 ml), la harina no
        detalle = self.app.texto_detalle.get("1.0", "end")
        self.assertIn("Te faltan 1 ingrediente(s).", detalle)
        self.assertIn("Harina: pide 500 g, tienes 300 g (te faltan 200 g)", detalle)
        self.assertNotIn("puedes cocinarla ya", detalle)
        # y con el filtro «solo las que puedo cocinar ya» ya no aparece
        self.app.var_solo_completas.set(True)
        self.app._refrescar_recetas()
        self.assertEqual(self.filas(self.app.tabla_recetas), [])

    def test_ingrediente_vencido_de_una_receta_propia_cuenta_como_faltante_con_su_cantidad(self):
        self.agregar("Harina", "1", "kg", fecha(-2))   # vencida
        self.agregar("Agua", "1", "L", fecha(10))
        self.crear()
        self.raiz.update()
        detalle = self.app.texto_detalle.get("1.0", "end")
        self.assertIn("Harina — pide 500 g (lo tienes, pero está vencido)", detalle)

    # --- guardar / editar / eliminar ---
    def test_las_recetas_propias_sobreviven_al_reabrir(self):
        self.crear()
        otra = self._abrir_app()
        (receta,) = otra.recetas_propias
        self.assertEqual(receta.nombre, "Pan casero")
        self.assertTrue(receta.propia)

    def test_editar_una_receta(self):
        self.crear()
        (original,) = self.app.recetas_propias
        dialogo = self.app.abrir_creador_de_recetas(original)
        self.assertEqual(dialogo.var_nombre.get(), "Pan casero")
        self.assertEqual([f[0] for f in dialogo.filas], ["Harina", "Agua"])
        self.assertIn("Amasar", dialogo.texto_pasos.get("1.0", "end"))
        dialogo.var_nombre.set("Pan de la abuela")
        dialogo.tabla.selection_set("0")
        dialogo._editar_ingrediente()
        dialogo.var_cantidad.set("600")
        dialogo._agregar_ingrediente()
        dialogo._guardar()
        (editada,) = self.app.recetas_propias  # no se duplicó
        self.assertEqual(editada.id, original.id)
        self.assertEqual(editada.nombre, "Pan de la abuela")
        self.assertEqual(editada.cantidades[0], (600.0, "g"))
        self.assertIn("actualizada", self.app.etiqueta_mensaje.cget("text"))

    def test_al_editar_se_puede_conservar_el_mismo_nombre_pero_no_tomar_el_de_otra(self):
        self.crear()
        self.crear(nombre="Galletas", filas=(("Harina", "200", "g"),), pasos="Hornear")
        galletas = next(r for r in self.app.recetas_propias if r.nombre == "Galletas")
        dialogo = self.app.abrir_creador_de_recetas(galletas)
        dialogo._guardar()  # sin cambios: su propio nombre no cuenta como repetido
        self.assertFalse(dialogo.winfo_exists())
        dialogo = self.app.abrir_creador_de_recetas(galletas)
        dialogo.var_nombre.set("pan casero")
        dialogo._guardar()
        self.assertIn("Ya existe", self.mensaje(dialogo))

    def test_eliminar_una_receta(self):
        self.crear()
        (receta,) = self.app.recetas_propias
        self.app.eliminar_receta_propia(receta.id)
        self.assertEqual(self.app.recetas_propias, [])
        self.assertEqual(self._abrir_app().recetas_propias, [])  # tampoco queda guardada
        self.assertIn("eliminada", self.app.etiqueta_mensaje.cget("text"))

    def test_administrador_lista_edita_y_elimina(self):
        self.crear()
        admin = self.app.abrir_administrador_de_recetas()
        self.assertIs(self.app.abrir_administrador_de_recetas(), admin, "no abre dos ventanas")
        (iid,) = admin.tabla.get_children()
        self.assertEqual(admin.tabla.item(iid, "values"), ("Pan casero", "2", "3"))
        self.assertEqual(str(admin.boton_editar.cget("state")), "disabled")
        admin.tabla.selection_set(iid)
        self.raiz.update()
        self.assertEqual(str(admin.boton_editar.cget("state")), "normal")

        # Se actualiza solo cuando se crea otra receta
        self.crear(nombre="Galletas", filas=(("Harina", "200", "g"),), pasos="Hornear")
        self.assertEqual(len(admin.tabla.get_children()), 2)

        # Eliminar pide confirmación
        modulo_app.messagebox.askyesno.return_value = False
        admin._eliminar()
        self.assertEqual(len(self.app.recetas_propias), 2)
        modulo_app.messagebox.askyesno.return_value = True
        admin._eliminar()
        self.assertEqual([r.nombre for r in self.app.recetas_propias], ["Galletas"])
        self.assertEqual(len(admin.tabla.get_children()), 1)

    def test_administrador_vacio_explica_que_hacer(self):
        admin = self.app.abrir_administrador_de_recetas()
        self.assertIn("Todavía no has creado", admin.etiqueta_vacio.cget("text"))

    def test_los_botones_estan_en_el_panel_de_recetas(self):
        self.assertEqual(self.app.boton_crear_receta.cget("text"), "+ Crear mi receta")
        self.assertEqual(self.app.boton_mis_recetas.cget("text"), "Mis recetas")

    def test_archivo_de_recetas_danado_no_impide_abrir_la_app(self):
        self.app.ruta_recetas.parent.mkdir(parents=True, exist_ok=True)
        self.app.ruta_recetas.write_text("{{ no es json", encoding="utf-8")
        modulo_app.messagebox.showwarning.reset_mock()
        ventana = self._abrir_app()
        self.raiz.after(150)
        self.raiz.update()
        self.assertEqual(ventana.recetas_propias, [])
        modulo_app.messagebox.showwarning.assert_called_once()
        self.assertIn("recetas", modulo_app.messagebox.showwarning.call_args.args[1])
        self.assertTrue(ventana.ruta_recetas.with_suffix(".corrupto").exists())

    def test_las_recetas_predefinidas_siguen_igual(self):
        self.agregar("Huevos", "6", "unidades", fecha(5))
        self.agregar("Queso", "200", "g", fecha(10))
        self.agregar("Tomates", "4", "unidades", fecha(2))
        filas = self.filas(self.app.tabla_recetas)
        self.assertEqual(filas[0], ("Omelette de queso y tomate", "3 de 3", "Tomates (en 2 días)"))
        self.assertTrue(all(not f[0].startswith("★") for f in filas))


# Las mismas pruebas con la apariencia renovada
for _original in (PruebasFechaAutomatica, PruebasRecetasPropias):
    _nombre = _original.__name__ + "ConAparienciaNueva"
    globals()[_nombre] = type(_nombre, (_original,), {"CLASE_APP": AplicacionFoodSaverVisual})
del _original, _nombre


if __name__ == "__main__":
    unittest.main()
