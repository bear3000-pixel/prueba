"""Pruebas de persistencia en JSON (food_saver/almacenamiento.py)."""
import json
import tempfile
import unittest
from pathlib import Path

from food_saver import almacenamiento
from food_saver.modelo import crear_ingrediente


class PruebasAlmacenamiento(unittest.TestCase):
    def setUp(self):
        self._carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(self._carpeta.cleanup)
        self.ruta = Path(self._carpeta.name) / "datos" / "ingredientes.json"

    def test_archivo_inexistente_devuelve_lista_vacia(self):
        self.assertEqual(almacenamiento.cargar(self.ruta), ([], None))

    def test_guardar_y_cargar_conserva_los_datos(self):
        original = [
            crear_ingrediente("Leche", "1,5", "L", "20/06/2026"),
            crear_ingrediente("Piña", 2, "unidades", "2026-07-01"),  # acento y ñ
        ]
        almacenamiento.guardar(self.ruta, original)
        cargados, aviso = almacenamiento.cargar(self.ruta)
        self.assertEqual(cargados, original)
        self.assertIsNone(aviso)

    def test_no_quedan_archivos_temporales(self):
        almacenamiento.guardar(self.ruta, [crear_ingrediente("Leche", 1, "L", "20/06/2026")])
        self.assertEqual([p.name for p in self.ruta.parent.iterdir()], ["ingredientes.json"])

    def test_archivo_danado_no_rompe_y_se_respalda(self):
        self.ruta.parent.mkdir(parents=True)
        self.ruta.write_text("{esto no es json", encoding="utf-8")
        cargados, aviso = almacenamiento.cargar(self.ruta)
        self.assertEqual(cargados, [])
        self.assertIn("dañado", aviso)
        self.assertTrue(self.ruta.with_suffix(".corrupto").exists())
        self.assertFalse(self.ruta.exists())

    def test_estructura_inesperada_se_trata_como_danada(self):
        self.ruta.parent.mkdir(parents=True)
        for texto in ["[]", '{"ingredientes": 5}', '{"otra_cosa": []}', ""]:
            with self.subTest(texto=texto):
                self.ruta.write_text(texto, encoding="utf-8")
                cargados, aviso = almacenamiento.cargar(self.ruta)
                self.assertEqual(cargados, [])
                self.assertIsNotNone(aviso)

    def test_entradas_invalidas_se_omiten_y_las_buenas_se_conservan(self):
        self.ruta.parent.mkdir(parents=True)
        contenido = {
            "version": 1,
            "ingredientes": [
                {"nombre": "Leche", "cantidad": 1, "unidad": "L", "vencimiento": "2026-06-20"},
                {"nombre": "Malo", "cantidad": -5, "unidad": "L", "vencimiento": "2026-06-20"},
                {"nombre": "SinFecha", "cantidad": 1, "unidad": "L"},
                "no soy un objeto",
            ],
        }
        self.ruta.write_text(json.dumps(contenido), encoding="utf-8")
        cargados, aviso = almacenamiento.cargar(self.ruta)
        self.assertEqual([i.nombre for i in cargados], ["Leche"])
        self.assertIn("3", aviso)


if __name__ == "__main__":
    unittest.main()
