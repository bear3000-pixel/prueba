"""La versión web/Android (JavaScript) se compara con ESTE código Python mediante casos de referencia.

Esos casos los genera web/tests/generar_referencia.py a partir del Python. Si alguien cambia una regla
aquí (un mensaje, un límite, el orden de las recetas…) y no regenera los archivos, esta prueba falla y
dice qué comando ejecutar. Así la versión de escritorio y la de Android no se separan sin que nadie lo note.
"""
import importlib.util
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
GENERADOR = RAIZ / "web" / "tests" / "generar_referencia.py"


def _cargar_generador():
    especificacion = importlib.util.spec_from_file_location("generar_referencia", GENERADOR)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


class PruebasReferenciaWeb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generador = _cargar_generador()

    def test_las_recetas_de_la_web_estan_al_dia(self):
        actual = self.generador.RUTA_RECETAS_JS.read_text(encoding="utf-8")
        self.assertEqual(
            actual, self.generador.construir_recetas_js(),
            "web/js/recetas.js está desactualizado. Ejecuta: python web/tests/generar_referencia.py",
        )

    def test_los_casos_de_referencia_estan_al_dia(self):
        actual = self.generador.RUTA_REFERENCIA.read_text(encoding="utf-8")
        self.assertEqual(
            actual, self.generador.serializar_referencia(),
            "web/tests/referencia.json está desactualizado. Ejecuta: python web/tests/generar_referencia.py",
        )

    def test_la_referencia_cubre_lo_importante(self):
        referencia = self.generador.construir_referencia()
        for seccion in ("autoformato", "fechas", "cantidades", "pasos", "recetasNuevas", "sugerencias"):
            self.assertGreaterEqual(len(referencia[seccion]), 10 if seccion != "sugerencias" else 8, seccion)
        # hay casos de error de verdad y casos válidos de verdad en las validaciones
        for seccion in ("fechas", "cantidades", "recetasNuevas"):
            tipos = {"error" in caso for caso in referencia[seccion]}
            self.assertEqual(tipos, {True, False}, f"{seccion} debe traer casos válidos e inválidos")


if __name__ == "__main__":
    unittest.main()
