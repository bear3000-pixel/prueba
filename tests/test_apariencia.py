"""Pruebas de la capa visual (food_saver/app_visual.py y tema.py).

La apariencia nueva HEREDA de la aplicación original. Aquí se comprueba que:
  * no se sustituyó ninguna función original salvo las dos que se extienden (con super());
  * el encabezado y su resumen muestran los números correctos y se actualizan solos;
  * los mensajes van en una caja de color; y
  * todo funciona también con zoom de pantalla alto y se puede volver a la versión original.
"""
import unittest
from unittest import mock

from food_saver import app_visual, tema
from food_saver.app import AplicacionFoodSaver
from food_saver.app_visual import AplicacionFoodSaverVisual

from test_interfaz import BaseInterfaz, fecha


class PruebasHerencia(unittest.TestCase):
    """No necesita pantalla: solo mira cómo está definida la clase."""

    def test_solo_se_extienden_las_funciones_documentadas(self):
        propias = {nombre for nombre, valor in vars(AplicacionFoodSaverVisual).items() if callable(valor)}
        sustituidas = propias & set(vars(AplicacionFoodSaver))  # nombres que ya existían en la original
        # Cada una de estas llama primero a la original con super() y luego agrega lo visual.
        self.assertEqual(sustituidas, {"__init__", "refrescar", "_mostrar_mensaje"})

    def test_la_logica_de_negocio_se_hereda_sin_cambios(self):
        for nombre in ("_enviar_formulario", "_editar_seleccionado", "_eliminar_seleccionado",
                       "_cargar_ejemplo", "_borrar_todo", "_guardar", "_refrescar_recetas",
                       "_mostrar_detalle", "_llenar_tabla", "_entrar_en_edicion", "_cancelar_edicion"):
            with self.subTest(funcion=nombre):
                self.assertIs(getattr(AplicacionFoodSaverVisual, nombre), getattr(AplicacionFoodSaver, nombre))

    def test_main_con_clasico_abre_la_version_original(self):
        for clasico, esperada, otra in ((True, "AplicacionFoodSaver", "AplicacionFoodSaverVisual"),
                                        (False, "AplicacionFoodSaverVisual", "AplicacionFoodSaver")):
            with self.subTest(clasico=clasico):
                with mock.patch.object(app_visual.tk, "Tk"), \
                        mock.patch.object(app_visual, "_activar_dpi_alto"), \
                        mock.patch.object(app_visual, esperada) as abre, \
                        mock.patch.object(app_visual, otra) as no_abre:
                    app_visual.main(clasico=clasico)
                abre.assert_called_once()
                no_abre.assert_not_called()


class PruebasApariencia(BaseInterfaz):
    CLASE_APP = AplicacionFoodSaverVisual

    def textos_resumen(self):
        return {clave: chip.cget("text") for clave, chip in self.app._chips.items()}

    def test_el_resumen_del_encabezado_cuenta_bien(self):
        self.assertEqual(
            self.textos_resumen(),
            {"vigentes": "0 vigentes", "por_vencer": "0 por vencer", "vencidos": "0 vencidos"},
        )
        self.agregar("Leche", "1", "L", fecha(2))       # vigente y por vencer
        self.agregar("Arroz", "1", "kg", fecha(200))    # vigente
        self.agregar("Pollo", "500", "g", fecha(-1))    # vencido
        self.assertEqual(
            self.textos_resumen(),
            {"vigentes": "2 vigentes", "por_vencer": "1 por vencer", "vencidos": "1 vencido"},
        )

    def test_el_resumen_se_actualiza_al_editar_y_eliminar(self):
        self.agregar("Leche", "1", "L", fecha(2))
        (iid,) = self.app.tabla_vigentes.get_children()
        self.app.tabla_vigentes.selection_set(iid)
        self.app._editar_seleccionado()
        self.app.var_vence.set(fecha(-3))  # ahora está vencida
        self.app._enviar_formulario()
        self.assertEqual(
            self.textos_resumen(),
            {"vigentes": "0 vigentes", "por_vencer": "0 por vencer", "vencidos": "1 vencido"},
        )
        self.app._borrar_todo()
        self.assertEqual(self.textos_resumen()["vencidos"], "0 vencidos")

    def test_el_resumen_con_datos_de_ejemplo(self):
        self.app._cargar_ejemplo()
        self.assertEqual(
            self.textos_resumen(),
            {"vigentes": "10 vigentes", "por_vencer": "4 por vencer", "vencidos": "2 vencidos"},
        )

    def test_los_mensajes_van_en_una_caja_de_color(self):
        etiqueta = self.app.etiqueta_mensaje
        self.agregar("Leche", "0", "L", fecha(2))  # error
        self.assertEqual(str(etiqueta.cget("background")), tema.ROJO_FONDO)
        self.agregar("Leche", "1", "L", fecha(2))  # éxito
        self.assertEqual(str(etiqueta.cget("background")), tema.VERDE_CLARO)
        self.app._mostrar_mensaje("")              # sin mensaje: la caja desaparece
        self.assertEqual(str(etiqueta.cget("background")), tema.FONDO)

    def test_el_encabezado_ocupa_la_fila_superior_y_el_contenido_crece(self):
        self.raiz.update()
        self.assertEqual(int(self.app.encabezado.grid_info()["row"]), 0)
        self.assertEqual(int(self.app.marco_form.grid_info()["row"]), 1)
        self.assertEqual(int(self.app.tabla_vigentes.master.master.grid_info()["row"]), 2)
        self.assertEqual(self.raiz.grid_rowconfigure(2)["weight"], 1)
        self.assertEqual(self.raiz.grid_rowconfigure(1)["weight"], 0)

    def test_botones_con_su_jerarquia(self):
        self.assertEqual(str(self.app.boton_guardar.cget("style")), "Primario.TButton")
        self.assertEqual(str(self.app.boton_eliminar.cget("style")), "Peligro.TButton")

    def test_tiene_icono(self):
        self.assertTrue(self.app._icono.width() > 0)


class PruebasZoomAlto(unittest.TestCase):
    def test_funciona_con_pantalla_al_150_por_ciento(self):
        try:
            import tkinter as tk
            raiz = tk.Tk()
        except Exception as error:  # noqa: BLE001
            self.skipTest(f"No hay pantalla disponible para tkinter: {error}")
        self.addCleanup(raiz.destroy)
        raiz.tk.call("tk", "scaling", 2.0)  # equivale a ~150 % de zoom en Windows
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as carpeta, mock.patch("food_saver.app.messagebox"):
            app = AplicacionFoodSaverVisual(raiz, ruta_datos=Path(carpeta) / "d.json")
            app._cargar_ejemplo()
            raiz.update()
            self.assertGreater(app.escala, 1.4)
            self.assertEqual(len(app.tabla_vigentes.get_children()), 10)


if __name__ == "__main__":
    unittest.main()
