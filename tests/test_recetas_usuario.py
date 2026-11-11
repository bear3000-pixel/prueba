"""Pruebas de las recetas propias: validaciones, guardado y comparación de cantidades."""
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from food_saver import recetas_usuario as ru
from food_saver.logica import sugerir_recetas
from food_saver.modelo import ErrorValidacion, Ingrediente
from food_saver.recetas import RECETAS

HOY = date(2026, 6, 15)


def ing(nombre, dias, cantidad=1, unidad="unidades"):
    return Ingrediente(nombre, cantidad, unidad, HOY + timedelta(days=dias))


def receta_valida(**cambios):
    datos = dict(
        nombre="Tortilla de papa",
        ingredientes=[("Papa", "3", "unidades"), ("Huevo", "4", "unidades"), ("Cebolla", "1,5", "unidades")],
        pasos="1. Pela y corta las papas.\n2) Fríelas con la cebolla.\n- Agrega el huevo batido.",
    )
    datos.update(cambios)
    return ru.crear_receta(datos["nombre"], datos["ingredientes"], datos["pasos"])


class PruebasCrearReceta(unittest.TestCase):
    def test_receta_valida(self):
        receta = receta_valida()
        self.assertTrue(receta.propia)
        self.assertTrue(receta.id)
        self.assertEqual(receta.ingredientes, ("Papa", "Huevo", "Cebolla"))
        self.assertEqual(receta.cantidades, ((3.0, "unidades"), (4.0, "unidades"), (1.5, "unidades")))
        # La numeración y las viñetas que escribe el usuario se quitan (la pantalla numera sola)
        self.assertEqual(
            receta.instrucciones, ("Pela y corta las papas.", "Fríelas con la cebolla.", "Agrega el huevo batido.")
        )

    def test_cantidades_invalidas_se_rechazan(self):
        for cantidad in ["", "   ", "0", "0,0", "-2", "-0.5", "abc", "1e3", "nan", "inf", "5000000", "0.0001", None]:
            with self.subTest(cantidad=cantidad):
                with self.assertRaises(ErrorValidacion) as contexto:
                    receta_valida(ingredientes=[("Papa", cantidad, "unidades")])
                self.assertEqual(contexto.exception.campo, "cantidad")

    def test_falta_la_cantidad_menciona_el_ingrediente(self):
        with self.assertRaises(ErrorValidacion) as contexto:
            receta_valida(ingredientes=[("Papa", "", "unidades")])
        self.assertIn("Papa", str(contexto.exception))

    def test_ingredientes_invalidos(self):
        for nombre, unidad in [("", "g"), ("123", "g"), ("Papa", "toneladas"), ("Papa", "")]:
            with self.subTest(nombre=nombre, unidad=unidad):
                with self.assertRaises(ErrorValidacion):
                    receta_valida(ingredientes=[(nombre, "1", unidad)])

    def test_sin_ingredientes(self):
        with self.assertRaises(ErrorValidacion) as contexto:
            receta_valida(ingredientes=[])
        self.assertEqual(contexto.exception.campo, "ingredientes")

    def test_ingrediente_repetido(self):
        with self.assertRaises(ErrorValidacion) as contexto:
            receta_valida(ingredientes=[("Tomate", "1", "unidades"), ("TOMATES", "2", "unidades")])
        self.assertIn("repetido", str(contexto.exception))

    def test_demasiados_ingredientes(self):
        filas = [(f"Ingrediente{chr(97 + i)}x", "1", "g") for i in range(ru.MAX_INGREDIENTES + 1)]
        with self.assertRaises(ErrorValidacion):
            receta_valida(ingredientes=filas)

    def test_nombre_de_la_receta(self):
        for nombre in ["", "   ", "123", "a" * 61, None]:
            with self.subTest(nombre=nombre):
                with self.assertRaises(ErrorValidacion) as contexto:
                    receta_valida(nombre=nombre)
                self.assertEqual(contexto.exception.campo, "nombre")
        self.assertEqual(receta_valida(nombre="  Mi   guiso ").nombre, "Mi guiso")

    def test_no_repite_nombres_ni_con_otras_mayusculas_o_acentos(self):
        with self.assertRaises(ErrorValidacion) as contexto:
            ru.crear_receta("OMELETTE DE QUESO Y TOMATE", [("Huevo", "2", "unidades")], "Cocinar",
                            nombres_existentes=[r.nombre for r in RECETAS])
        self.assertIn("Ya existe", str(contexto.exception))
        with self.assertRaises(ErrorValidacion):
            ru.crear_receta("Sopa de plátano", [("Platano", "2", "unidades")], "Cocinar",
                            nombres_existentes=["Sopa de platano"])

    def test_pasos(self):
        for pasos in ["", "   \n  \n", "123\n456", "x\n" * 21, "a" * 301, []]:
            with self.subTest(pasos=pasos[:20] if isinstance(pasos, str) else pasos):
                with self.assertRaises(ErrorValidacion) as contexto:
                    receta_valida(pasos=pasos)
                self.assertEqual(contexto.exception.campo, "pasos")

    def test_los_pasos_no_pierden_numeros_que_son_parte_del_texto(self):
        receta = receta_valida(pasos="2 huevos batidos\n1.5 tazas de leche\nHornear 2-3 minutos")
        self.assertEqual(receta.instrucciones, ("2 huevos batidos", "1.5 tazas de leche", "Hornear 2-3 minutos"))


class PruebasGuardado(unittest.TestCase):
    def setUp(self):
        self._carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(self._carpeta.cleanup)
        self.ruta = Path(self._carpeta.name) / "datos" / "recetas_propias.json"

    def test_ida_y_vuelta(self):
        originales = [receta_valida(), receta_valida(nombre="Otra receta")]
        ru.guardar(self.ruta, originales)
        cargadas, aviso = ru.cargar(self.ruta)
        self.assertIsNone(aviso)
        self.assertEqual(cargadas, originales)

    def test_sin_archivo(self):
        self.assertEqual(ru.cargar(self.ruta), ([], None))

    def test_archivo_danado_se_respalda(self):
        self.ruta.parent.mkdir(parents=True)
        self.ruta.write_text("{no es json", encoding="utf-8")
        recetas, aviso = ru.cargar(self.ruta)
        self.assertEqual(recetas, [])
        self.assertIn("dañado", aviso)
        self.assertTrue(self.ruta.with_suffix(".corrupto").exists())

    def test_recetas_invalidas_se_omiten_y_las_buenas_se_conservan(self):
        buena = ru.a_dict(receta_valida())
        mala_cantidad = ru.a_dict(receta_valida(nombre="Mala"))
        mala_cantidad["ingredientes"][0]["cantidad"] = -4
        sin_pasos = ru.a_dict(receta_valida(nombre="Sin pasos"))
        sin_pasos["instrucciones"] = []
        self.ruta.parent.mkdir(parents=True)
        self.ruta.write_text(json.dumps({"version": 1, "recetas": [buena, mala_cantidad, sin_pasos, "basura"]}), encoding="utf-8")
        recetas, aviso = ru.cargar(self.ruta)
        self.assertEqual([r.nombre for r in recetas], ["Tortilla de papa"])
        self.assertIn("3", aviso)

    def test_ruta_junto_al_archivo_de_ingredientes(self):
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {"FOODSAVER_DATA": str(Path(self._carpeta.name) / "x" / "ingredientes.json")}):
            self.assertEqual(ru.ruta_por_defecto().name, "recetas_propias.json")
            self.assertEqual(ru.ruta_por_defecto().parent.name, "x")


class PruebasCantidadesEnSugerencias(unittest.TestCase):
    """La sugerencia compara lo que pide la receta con lo que hay en la despensa."""

    def sugerir(self, stock, **kwargs):
        receta = ru.crear_receta("Prueba", kwargs.get("filas", [("Harina", "500", "g")]), "Mezclar")
        (sug,) = sugerir_recetas(stock, [receta], HOY)
        return sug

    def test_cantidad_suficiente(self):
        sug = self.sugerir([ing("Harina", 5, 1, "kg")])  # 1 kg >= 500 g (convierte unidades)
        self.assertTrue(sug.completa)
        self.assertEqual(sug.insuficientes, ())
        self.assertEqual(sug.usados[0].necesita, (500.0, "g"))

    def test_cantidad_justa(self):
        self.assertTrue(self.sugerir([ing("Harina", 5, 500, "g")]).completa)
        self.assertTrue(self.sugerir([ing("Harina", 5, 0.5, "kg")]).completa)

    def test_cantidad_insuficiente(self):
        sug = self.sugerir([ing("Harina", 5, 300, "g")])
        self.assertFalse(sug.completa)
        self.assertEqual(sug.usados, ())
        (falta,) = sug.insuficientes
        self.assertEqual(falta.necesita, (500.0, "g"))
        self.assertEqual(falta.tienes, (300.0, "g"))
        self.assertEqual(sug.total_ingredientes, 1)

    def test_suma_varios_lotes(self):
        sug = self.sugerir([ing("Harina", 5, 300, "g"), ing("Harina", 9, 0.3, "kg")])  # 300 + 300 g
        self.assertTrue(sug.completa)

    def test_los_lotes_vencidos_no_suman(self):
        sug = self.sugerir([ing("Harina", 5, 300, "g"), ing("Harina", -2, 5, "kg")])
        self.assertFalse(sug.completa)
        self.assertEqual(sug.insuficientes[0].tienes, (300.0, "g"))

    def test_unidades_incomparables_se_dan_por_disponibles(self):
        # La receta pide 3 unidades y en la despensa hay "500 g": no se puede saber, no se bloquea
        sug = self.sugerir([ing("Tomate", 5, 500, "g")], filas=[("Tomate", "3", "unidades")])
        self.assertTrue(sug.completa)

    def test_insuficiente_cuenta_para_lo_que_esta_por_vencer(self):
        sug = self.sugerir([ing("Harina", 1, 100, "g")])  # vence mañana
        self.assertEqual(sug.dias_mas_urgente, 1)
        self.assertEqual(sug.uso_mas_urgente.dias, 1)
        self.assertGreater(sug.puntaje, 0)

    def test_solo_completas_excluye_las_de_poca_cantidad(self):
        receta = ru.crear_receta("Prueba", [("Harina", "500", "g")], "Mezclar")
        self.assertEqual(sugerir_recetas([ing("Harina", 5, 300, "g")], [receta], HOY, solo_completas=True), [])

    def test_las_recetas_predefinidas_no_cambian(self):
        sugerencias = sugerir_recetas([ing("Huevos", 5, 1, "unidades"), ing("Queso", 8)], RECETAS, HOY)
        self.assertTrue(sugerencias)
        for sug in sugerencias:
            self.assertEqual(sug.insuficientes, ())


if __name__ == "__main__":
    unittest.main()
