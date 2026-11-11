"""Pruebas de la interfaz real (tkinter): se crea la ventana y se simula al usuario.

Si el equipo no tiene pantalla (p. ej. un servidor Linux sin entorno gráfico) estas
pruebas se omiten solas; en Windows o con `xvfb-run python -m unittest ...` se ejecutan.
"""
import tempfile
import tkinter as tk
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from food_saver import almacenamiento, app as modulo_app
from food_saver.app import AplicacionFoodSaver
from food_saver.modelo import formatear_fecha

HOY = date(2026, 6, 15)


def fecha(dias: int) -> str:
    """Texto DD/MM/AAAA de dentro de `dias` días respecto a HOY (negativo = pasado)."""
    return formatear_fecha(HOY + timedelta(days=dias))


class BaseInterfaz(unittest.TestCase):
    def setUp(self):
        try:
            self.raiz = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"No hay pantalla disponible para tkinter: {error}")
        self.addCleanup(self.raiz.destroy)
        self._carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(self._carpeta.cleanup)
        self.ruta = Path(self._carpeta.name) / "ingredientes.json"
        self.app = self._abrir_app()

        # Los cuadros de diálogo bloquean la prueba: los sustituimos por simulacros.
        for nombre in ("showerror", "showwarning", "showinfo"):
            parche = mock.patch.object(modulo_app.messagebox, nombre)
            parche.start()
            self.addCleanup(parche.stop)
        self.confirmar = mock.patch.object(modulo_app.messagebox, "askyesno", return_value=True)
        self.confirmar.start()
        self.addCleanup(self.confirmar.stop)

    def _abrir_app(self):
        return AplicacionFoodSaver(self.raiz, ruta_datos=self.ruta, hoy_fn=lambda: HOY)

    # --- ayudas para "escribir" en el formulario y leer las tablas ---
    def agregar(self, nombre, cantidad, unidad, vence):
        self.app.var_nombre.set(nombre)
        self.app.var_cantidad.set(cantidad)
        self.app.var_unidad.set(unidad)
        self.app.var_vence.set(vence)
        self.app._enviar_formulario()

    @staticmethod
    def filas(tabla):
        return [tabla.item(iid, "values") for iid in tabla.get_children()]

    def nombres(self, tabla):
        return [fila[0] for fila in self.filas(tabla)]


class PruebasFormulario(BaseInterfaz):
    def test_agregar_ingrediente_valido(self):
        self.agregar("Leche", "1,5", "L", fecha(2))
        self.assertEqual(self.nombres(self.app.tabla_vigentes), ["Leche"])
        fila = self.filas(self.app.tabla_vigentes)[0]
        self.assertEqual(fila[1], "1,5 L")
        self.assertIn("2 días", fila[3])
        self.assertEqual(self.app.var_nombre.get(), "")  # el formulario queda listo para el siguiente

    def test_cantidades_invalidas_se_rechazan_con_mensaje(self):
        for cantidad in ["", "0", "-3", "abc", "1e3", "nan"]:
            with self.subTest(cantidad=cantidad):
                self.agregar("Leche", cantidad, "L", fecha(2))
                self.assertEqual(self.app.ingredientes, [])
                self.assertEqual(self.filas(self.app.tabla_vigentes), [])
                self.assertIn("cantidad", self.app.etiqueta_mensaje.cget("text").lower())
                self.assertEqual(str(self.app.etiqueta_mensaje.cget("foreground")), modulo_app.COLOR_ERROR)
                self.assertEqual(self.app.var_nombre.get(), "Leche")  # no borra lo escrito
        self.assertFalse(self.ruta.exists(), "no debe guardarse nada si todo fue inválido")

    def test_nombre_y_fecha_invalidos(self):
        self.agregar("", "1", "L", fecha(2))
        self.assertIn("nombre", self.app.etiqueta_mensaje.cget("text").lower())
        self.agregar("Leche", "1", "L", "31/02/2026")
        self.assertIn("fecha", self.app.etiqueta_mensaje.cget("text").lower())
        self.agregar("Leche", "1", "L", "")
        self.assertEqual(self.app.ingredientes, [])

    def test_se_guarda_en_disco_y_sobrevive_al_reabrir(self):
        self.agregar("Leche", "1", "L", fecha(2))
        self.agregar("Huevos", "6", "unidades", fecha(5))
        otra_ventana = self._abrir_app()  # simula cerrar y volver a abrir el programa
        self.assertEqual(self.nombres(otra_ventana.tabla_vigentes), ["Leche", "Huevos"])
        _, aviso = almacenamiento.cargar(self.ruta)
        self.assertIsNone(aviso)


class PruebasListas(BaseInterfaz):
    def test_orden_por_vencimiento_y_vencidos_aparte(self):
        self.agregar("Arroz", "1", "kg", fecha(200))
        self.agregar("Pollo", "500", "g", fecha(-1))     # vencido
        self.agregar("Leche", "1", "L", fecha(2))
        self.agregar("Yogur", "2", "unidades", fecha(0))  # vence hoy: sigue vigente
        self.assertEqual(self.nombres(self.app.tabla_vigentes), ["Yogur", "Leche", "Arroz"])
        self.assertEqual(self.nombres(self.app.tabla_vencidos), ["Pollo"])
        self.assertIn("Vencido hace 1 día", self.filas(self.app.tabla_vencidos)[0][3])
        self.assertIn("Vence hoy", self.filas(self.app.tabla_vigentes)[0][3])

    def test_por_vencer_se_marca(self):
        self.agregar("Leche", "1", "L", fecha(2))
        self.agregar("Arroz", "1", "kg", fecha(200))
        iid_leche, iid_arroz = self.app.tabla_vigentes.get_children()
        self.assertIn("por_vencer", self.app.tabla_vigentes.item(iid_leche, "tags"))
        self.assertNotIn("por_vencer", self.app.tabla_vigentes.item(iid_arroz, "tags"))

    def test_editar_actualiza_en_lugar_de_duplicar(self):
        self.agregar("Leche", "1", "L", fecha(2))
        (iid,) = self.app.tabla_vigentes.get_children()
        self.app.tabla_vigentes.selection_set(iid)
        self.app._editar_seleccionado()
        self.assertEqual(self.app.var_nombre.get(), "Leche")
        self.assertEqual(self.app.boton_guardar.cget("text"), "Guardar cambios")
        self.app.var_cantidad.set("3")
        self.app.var_vence.set(fecha(-2))  # ahora está vencida: debe pasar a la otra tabla
        self.app._enviar_formulario()
        self.assertEqual(len(self.app.ingredientes), 1)
        self.assertEqual(self.nombres(self.app.tabla_vigentes), [])
        self.assertEqual(self.filas(self.app.tabla_vencidos)[0][:2], ("Leche", "3 L"))
        self.assertEqual(self.app.boton_guardar.cget("text"), "Agregar")

    def test_editar_con_dato_invalido_no_cambia_nada(self):
        self.agregar("Leche", "1", "L", fecha(2))
        (iid,) = self.app.tabla_vigentes.get_children()
        self.app.tabla_vigentes.selection_set(iid)
        self.app._editar_seleccionado()
        self.app.var_cantidad.set("0")
        self.app._enviar_formulario()
        self.assertEqual(self.app.ingredientes[0].cantidad, 1)
        self.assertEqual(self.app.boton_guardar.cget("text"), "Guardar cambios")  # sigue editando

    def test_eliminar_pide_confirmacion(self):
        self.agregar("Leche", "1", "L", fecha(2))
        (iid,) = self.app.tabla_vigentes.get_children()
        self.app.tabla_vigentes.selection_set(iid)

        modulo_app.messagebox.askyesno.return_value = False
        self.app._eliminar_seleccionado()
        self.assertEqual(len(self.app.ingredientes), 1)  # dijo que no

        modulo_app.messagebox.askyesno.return_value = True
        self.app._eliminar_seleccionado()
        self.assertEqual(self.app.ingredientes, [])
        self.assertEqual(self.filas(self.app.tabla_vigentes), [])

    def test_borrar_todo_concuerda_singular_y_plural(self):
        self.agregar("Leche", "1", "L", fecha(2))
        self.app._borrar_todo()
        self.assertEqual(modulo_app.messagebox.askyesno.call_args.args[1], "¿Borrar el ingrediente guardado?")
        self.agregar("Leche", "1", "L", fecha(2))
        self.agregar("Huevos", "6", "unidades", fecha(5))
        self.app._borrar_todo()
        self.assertEqual(
            modulo_app.messagebox.askyesno.call_args.args[1], "¿Borrar los 2 ingredientes guardados?"
        )
        self.assertEqual(self.app.ingredientes, [])

    def test_botones_editar_y_eliminar_solo_con_seleccion(self):
        self.assertEqual(str(self.app.boton_editar.cget("state")), "disabled")
        self.agregar("Leche", "1", "L", fecha(2))  # al agregar queda seleccionado
        self.assertEqual(str(self.app.boton_editar.cget("state")), "normal")


class PruebasRecetas(BaseInterfaz):
    def test_sin_ingredientes_muestra_guia(self):
        self.assertEqual(self.filas(self.app.tabla_recetas), [])
        self.assertIn("Agrega ingredientes", self.app.texto_detalle.get("1.0", "end"))

    def test_demostracion_con_datos_de_ejemplo(self):
        self.app._cargar_ejemplo()
        self.assertCountEqual(self.nombres(self.app.tabla_vencidos), ["Pollo", "Yogur"])
        filas = self.filas(self.app.tabla_recetas)
        self.assertTrue(filas)
        self.assertNotEqual(filas[0][2], "", "la 1.ª receta debe aprovechar algo por vencer")
        detalle = self.app.texto_detalle.get("1.0", "end")
        self.assertIn("Preparación", detalle)
        # Ninguna receta sugerida puede usar los ingredientes vencidos.
        for sug in self.app._sugerencias.values():
            self.assertTrue(all(u.lote.nombre not in ("Pollo", "Yogur") for u in sug.usados))

    def test_receta_con_ingrediente_vencido_avisa_que_falta(self):
        self.agregar("Huevos", "6", "unidades", fecha(3))
        self.agregar("Queso", "200", "g", fecha(-4))   # vencido: no cuenta como disponible
        iid = next(i for i, s in self.app._sugerencias.items() if s.receta.nombre.startswith("Omelette"))
        self.app.tabla_recetas.selection_set(iid)
        self.raiz.update()  # Tk procesa el evento <<TreeviewSelect>> (como si se hubiera hecho clic)
        detalle = self.app.texto_detalle.get("1.0", "end")
        self.assertIn("Omelette", detalle)
        self.assertIn("• Queso (lo tienes, pero está vencido)", detalle)
        self.assertIn("está vencido", detalle)

    def test_filtro_solo_completas(self):
        self.agregar("Plátano", "2", "unidades", fecha(2))
        self.agregar("Leche", "1", "L", fecha(2))
        self.assertTrue(any("Batido" in n for n in self.nombres(self.app.tabla_recetas)))
        self.app.var_solo_completas.set(True)
        self.app._refrescar_recetas()
        for sug in self.app._sugerencias.values():
            self.assertTrue(sug.completa)

    def test_vencido_no_genera_receta(self):
        self.agregar("Plátano", "2", "unidades", fecha(-1))
        self.assertEqual(self.filas(self.app.tabla_recetas), [])


class PruebasArchivoDanado(BaseInterfaz):
    def test_la_app_abre_aunque_el_archivo_este_danado(self):
        self.ruta.write_text("{{{ no es json", encoding="utf-8")
        ventana = self._abrir_app()
        self.raiz.after(150)  # el aviso se programa con after(100): esperamos a que venza
        self.raiz.update()
        self.assertEqual(ventana.ingredientes, [])
        modulo_app.messagebox.showwarning.assert_called_once()
        self.assertIn("dañado", modulo_app.messagebox.showwarning.call_args.args[1])


if __name__ == "__main__":
    unittest.main()
