"""Pruebas de validaciones y formato (food_saver/modelo.py)."""
import unittest
from datetime import date

from food_saver.modelo import (
    ErrorValidacion,
    autoformatear_fecha,
    convertir_cantidad,
    Ingrediente,
    crear_ingrediente,
    describir_vencimiento,
    dias_para_vencer,
    esta_por_vencer,
    esta_vencido,
    formatear_cantidad,
    normalizar,
    parsear_fecha,
    texto_cantidad,
    validar_cantidad,
    validar_nombre,
    validar_unidad,
)

HOY = date(2026, 6, 15)


class PruebasCantidad(unittest.TestCase):
    def test_acepta_numeros_validos(self):
        self.assertEqual(validar_cantidad("2"), 2)
        self.assertEqual(validar_cantidad(" 3 "), 3)
        self.assertEqual(validar_cantidad("1,5"), 1.5)   # coma decimal
        self.assertEqual(validar_cantidad("1.5"), 1.5)   # punto decimal
        self.assertEqual(validar_cantidad(".25"), 0.25)
        self.assertEqual(validar_cantidad(4), 4)         # ya viene numérico (datos guardados)

    def test_rechaza_cantidades_invalidas(self):
        invalidas = ["", "   ", "abc", "0", "0,0", "-1", "-0.5", "1e3", "nan", "inf",
                     "1_000", "1,2,3", "2 kg", "0.0001", "9" * 400, "5000000"]
        for texto in invalidas:
            with self.subTest(texto=texto):
                with self.assertRaises(ErrorValidacion) as contexto:
                    validar_cantidad(texto)
                self.assertEqual(contexto.exception.campo, "cantidad")


class PruebasNombreYUnidad(unittest.TestCase):
    def test_nombre_se_limpia(self):
        self.assertEqual(validar_nombre("  Leche    entera "), "Leche entera")

    def test_nombre_invalido(self):
        for texto in ["", "   ", "123", "!!!", "a" * 51, None]:
            with self.subTest(texto=texto):
                with self.assertRaises(ErrorValidacion):
                    validar_nombre(texto)

    def test_unidad(self):
        self.assertEqual(validar_unidad("kg"), "kg")
        for texto in ["", "toneladas", "KG"]:
            with self.subTest(texto=texto):
                with self.assertRaises(ErrorValidacion):
                    validar_unidad(texto)


class PruebasFecha(unittest.TestCase):
    def test_formatos_aceptados(self):
        esperada = date(2026, 12, 25)
        for texto in ["25/12/2026", "2026-12-25", "25-12-2026", " 25/12/2026 ", "5/1/2027"]:
            with self.subTest(texto=texto):
                self.assertIsInstance(parsear_fecha(texto), date)
        self.assertEqual(parsear_fecha("25/12/2026"), esperada)
        self.assertEqual(parsear_fecha("2026-12-25"), esperada)
        self.assertEqual(parsear_fecha("5/1/2027"), date(2027, 1, 5))

    def test_fechas_invalidas(self):
        for texto in ["", "mañana", "31/02/2026", "32/01/2026", "2026/12/25", "25/13/2026",
                      "25/12/26", "25/12/0226", "25/12/2926"]:
            with self.subTest(texto=texto):
                with self.assertRaises(ErrorValidacion) as contexto:
                    parsear_fecha(texto)
                self.assertEqual(contexto.exception.campo, "vencimiento")


class PruebasAutoformatoFecha(unittest.TestCase):
    def test_pone_las_barras_solas(self):
        self.assertEqual(autoformatear_fecha("02112026"), "02/11/2026")
        self.assertEqual(autoformatear_fecha("0211"), "02/11")
        self.assertEqual(autoformatear_fecha("021"), "02/1")

    def test_barra_automatica_al_escribir_pero_no_al_borrar(self):
        self.assertEqual(autoformatear_fecha("02", agregar_barra=True), "02/")
        self.assertEqual(autoformatear_fecha("0211", agregar_barra=True), "02/11/")
        self.assertEqual(autoformatear_fecha("02", agregar_barra=False), "02")  # borrando no reaparece la barra
        self.assertEqual(autoformatear_fecha("02/11/2026", agregar_barra=True), "02/11/2026")  # el año no lleva barra

    def test_completa_ceros_cuando_se_escribe_la_barra(self):
        self.assertEqual(autoformatear_fecha("2/11/2026"), "02/11/2026")
        self.assertEqual(autoformatear_fecha("1/1/2026"), "01/01/2026")
        self.assertEqual(autoformatear_fecha("02/1/"), "02/01/")

    def test_solo_acepta_numeros(self):
        self.assertEqual(autoformatear_fecha("mañana"), "")
        self.assertEqual(autoformatear_fecha("ab0c2d", agregar_barra=True), "02/")
        self.assertEqual(autoformatear_fecha("02/11/2026 "), "02/11/2026")

    def test_ignora_lo_que_sobra(self):
        self.assertEqual(autoformatear_fecha("123456789"), "12/34/5678")
        self.assertEqual(autoformatear_fecha("02/11/2026/"), "02/11/2026")
        self.assertEqual(autoformatear_fecha("//02//11"), "02/11")

    def test_otros_separadores_y_formato_iso_pegado(self):
        self.assertEqual(autoformatear_fecha("20-11-2026"), "20/11/2026")
        self.assertEqual(autoformatear_fecha("20.11.2026"), "20/11/2026")
        self.assertEqual(autoformatear_fecha("2026-11-20"), "20/11/2026")

    def test_no_decide_si_la_fecha_existe(self):
        # Solo da forma: que 31/02 no existe lo sigue decidiendo parsear_fecha
        self.assertEqual(autoformatear_fecha("31022026"), "31/02/2026")
        with self.assertRaises(ErrorValidacion):
            parsear_fecha(autoformatear_fecha("31022026"))
        self.assertEqual(parsear_fecha(autoformatear_fecha("02112026")), date(2026, 11, 2))

    def test_es_estable_al_aplicarlo_otra_vez(self):
        for texto in ["02112026", "2/11/2026", "0211", "02/", "mañana", "2026-11-20", "02/11/26"]:
            with self.subTest(texto=texto):
                una_vez = autoformatear_fecha(texto)
                self.assertEqual(autoformatear_fecha(una_vez), una_vez)


class PruebasConversion(unittest.TestCase):
    def test_masa_y_volumen(self):
        self.assertEqual(convertir_cantidad(1500, "g", "kg"), 1.5)
        self.assertEqual(convertir_cantidad(2, "kg", "g"), 2000)
        self.assertEqual(convertir_cantidad(250, "ml", "L"), 0.25)
        self.assertEqual(convertir_cantidad(1, "L", "ml"), 1000)

    def test_misma_unidad(self):
        self.assertEqual(convertir_cantidad(3, "unidades", "unidades"), 3)

    def test_unidades_que_no_se_pueden_comparar(self):
        self.assertIsNone(convertir_cantidad(3, "unidades", "g"))
        self.assertIsNone(convertir_cantidad(1, "kg", "L"))
        self.assertIsNone(convertir_cantidad(1, "tazas", "ml"))


class PruebasEstado(unittest.TestCase):
    def _ing(self, dias):
        from datetime import timedelta
        return Ingrediente("X", 1, "unidades", HOY + timedelta(days=dias))

    def test_vencido_es_estrictamente_anterior_a_hoy(self):
        self.assertTrue(esta_vencido(self._ing(-1), HOY))
        self.assertFalse(esta_vencido(self._ing(0), HOY))  # vence hoy: todavía sirve
        self.assertFalse(esta_vencido(self._ing(1), HOY))

    def test_por_vencer(self):
        self.assertFalse(esta_por_vencer(self._ing(-1), HOY))
        self.assertTrue(esta_por_vencer(self._ing(0), HOY))
        self.assertTrue(esta_por_vencer(self._ing(3), HOY))
        self.assertFalse(esta_por_vencer(self._ing(4), HOY))
        self.assertEqual(dias_para_vencer(self._ing(5), HOY), 5)

    def test_descripcion(self):
        self.assertEqual(describir_vencimiento(0), "vence hoy")
        self.assertEqual(describir_vencimiento(1), "vence mañana")
        self.assertEqual(describir_vencimiento(5), "vence en 5 días")
        self.assertEqual(describir_vencimiento(-1), "vencido hace 1 día")
        self.assertEqual(describir_vencimiento(-4), "vencido hace 4 días")


class PruebasFormato(unittest.TestCase):
    def test_cantidad(self):
        self.assertEqual(formatear_cantidad(2.0), "2")
        self.assertEqual(formatear_cantidad(1.5), "1,5")
        self.assertEqual(formatear_cantidad(0.25), "0,25")
        self.assertEqual(formatear_cantidad(0.125), "0,125")

    def test_unidad_concuerda_con_la_cantidad(self):
        self.assertEqual(texto_cantidad(1, "paquetes"), "1 paquete")
        self.assertEqual(texto_cantidad(2, "paquetes"), "2 paquetes")
        self.assertEqual(texto_cantidad(1, "unidades"), "1 unidad")
        self.assertEqual(texto_cantidad(1.5, "tazas"), "1,5 tazas")
        self.assertEqual(texto_cantidad(1, "kg"), "1 kg")

    def test_normalizar(self):
        self.assertEqual(normalizar("  Limón  Verde "), "limon verde")
        self.assertEqual(normalizar("PIÑA"), "pina")

    def test_ida_y_vuelta_dict(self):
        original = crear_ingrediente("Leche", "1,5", "L", "20/06/2026")
        copia = Ingrediente.desde_dict(original.a_dict())
        self.assertEqual(copia, original)


if __name__ == "__main__":
    unittest.main()
