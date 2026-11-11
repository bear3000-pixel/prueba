"""Pruebas de la lógica: orden por vencimiento, vencidos y sugerencia de recetas."""
import unittest
from datetime import date, timedelta

from food_saver.ejemplos import ingredientes_de_ejemplo
from food_saver.logica import (
    clasificar,
    coincide_ingrediente,
    ordenar_por_vencimiento,
    sugerir_recetas,
)
from food_saver.modelo import Ingrediente
from food_saver.recetas import RECETAS, Receta

HOY = date(2026, 6, 15)


def ing(nombre, dias, cantidad=1, unidad="unidades"):
    """Ingrediente que vence dentro de `dias` días (negativo = ya vencido)."""
    return Ingrediente(nombre, cantidad, unidad, HOY + timedelta(days=dias))


def receta(nombre, *ingredientes):
    return Receta(nombre, tuple(ingredientes), ("paso",))


class PruebasOrdenYVencidos(unittest.TestCase):
    def test_ordena_por_fecha_de_vencimiento(self):
        lista = [ing("C", 10), ing("A", 1), ing("B", 5)]
        self.assertEqual([i.nombre for i in ordenar_por_vencimiento(lista)], ["A", "B", "C"])

    def test_empate_se_resuelve_por_nombre(self):
        lista = [ing("zanahoria", 2), ing("Arroz", 2)]
        self.assertEqual([i.nombre for i in ordenar_por_vencimiento(lista)], ["Arroz", "zanahoria"])

    def test_vencidos_van_aparte(self):
        lista = [ing("hoy", 0), ing("ayer", -1), ing("mañana", 1), ing("hace_mucho", -30)]
        vigentes, vencidos = clasificar(lista, HOY)
        self.assertEqual([i.nombre for i in vigentes], ["hoy", "mañana"])
        # Entre los vencidos, el que lleva más tiempo vencido va primero.
        self.assertEqual([i.nombre for i in vencidos], ["hace_mucho", "ayer"])

    def test_no_se_pierde_ningun_ingrediente(self):
        lista = ingredientes_de_ejemplo(HOY)
        vigentes, vencidos = clasificar(lista, HOY)
        self.assertEqual(len(vigentes) + len(vencidos), len(lista))


class PruebasCoincidencia(unittest.TestCase):
    def test_ignora_mayusculas_acentos_y_plurales(self):
        casos = [
            ("tomate", "Tomates"), ("limon", "Limón"), ("limon", "limones"),
            ("frijol", "Frijoles"), ("pan", "Panes"), ("huevo", "HUEVOS"),
            ("leche", "Leche entera"), ("tomate", "Tomates cherry"),
            ("platano", "Plátano"), ("jamon", "Jamón"),
        ]
        for requerido, disponible in casos:
            with self.subTest(requerido=requerido, disponible=disponible):
                self.assertTrue(coincide_ingrediente(requerido, disponible))

    def test_no_confunde_ingredientes_distintos(self):
        casos = [("pan", "papa"), ("arroz", "maiz"), ("leche", "lechuga"),
                 ("ajo", "ajonjoli"), ("pollo", "polvo"), ("tomate", "pasta")]
        for requerido, disponible in casos:
            with self.subTest(requerido=requerido, disponible=disponible):
                self.assertFalse(coincide_ingrediente(requerido, disponible))


class PruebasSugerencias(unittest.TestCase):
    def test_receta_completa_y_parcial(self):
        recetas = [receta("Omelette", "huevo", "queso"), receta("Tortilla", "huevo", "papa")]
        stock = [ing("Huevos", 5), ing("Queso", 8)]
        sugerencias = {s.receta.nombre: s for s in sugerir_recetas(stock, recetas, HOY)}
        self.assertTrue(sugerencias["Omelette"].completa)
        self.assertEqual(sugerencias["Tortilla"].faltantes, ("papa",))
        self.assertFalse(sugerencias["Tortilla"].completa)

    def test_los_vencidos_se_excluyen_de_las_sugerencias(self):
        recetas = [receta("Omelette", "huevo", "queso")]
        stock = [ing("Huevos", 5), ing("Queso", -2)]  # el queso está vencido
        (sug,) = sugerir_recetas(stock, recetas, HOY)
        self.assertEqual([u.requerido for u in sug.usados], ["huevo"])
        self.assertEqual(sug.faltantes, ("queso",))
        self.assertEqual(sug.descartados_por_vencidos, ("queso",))  # se avisa por qué falta

    def test_una_receta_con_solo_ingredientes_vencidos_no_se_sugiere(self):
        recetas = [receta("Batido", "platano", "leche")]
        stock = [ing("Plátano", -1), ing("Leche", -5)]
        self.assertEqual(sugerir_recetas(stock, recetas, HOY), [])

    def test_ingrediente_que_vence_hoy_si_cuenta(self):
        recetas = [receta("Batido", "leche")]
        (sug,) = sugerir_recetas([ing("Leche", 0)], recetas, HOY)
        self.assertTrue(sug.completa)
        self.assertEqual(sug.dias_mas_urgente, 0)

    def test_con_varios_lotes_se_usa_el_que_vence_primero(self):
        recetas = [receta("Batido", "leche")]
        stock = [ing("Leche", 9), ing("Leche", 2), ing("Leche", 20)]
        (sug,) = sugerir_recetas(stock, recetas, HOY)
        self.assertEqual(sug.usados[0].dias, 2)

    def test_un_lote_vencido_y_otro_vigente_usa_el_vigente(self):
        recetas = [receta("Batido", "leche")]
        stock = [ing("Leche", -3), ing("Leche", 4)]
        (sug,) = sugerir_recetas(stock, recetas, HOY)
        self.assertTrue(sug.completa)
        self.assertEqual(sug.usados[0].dias, 4)

    def test_prioriza_la_receta_que_aprovecha_lo_proximo_a_vencer(self):
        recetas = [receta("Ensalada", "lechuga"), receta("Sopa", "zanahoria")]
        stock = [ing("Lechuga", 20), ing("Zanahoria", 1)]
        nombres = [s.receta.nombre for s in sugerir_recetas(stock, recetas, HOY)]
        self.assertEqual(nombres, ["Sopa", "Ensalada"])

    def test_solo_completas(self):
        recetas = [receta("Omelette", "huevo", "queso"), receta("Tortilla", "huevo", "papa")]
        stock = [ing("Huevos", 5), ing("Queso", 8)]
        sugerencias = sugerir_recetas(stock, recetas, HOY, solo_completas=True)
        self.assertEqual([s.receta.nombre for s in sugerencias], ["Omelette"])

    def test_sin_ingredientes_no_hay_sugerencias(self):
        self.assertEqual(sugerir_recetas([], RECETAS, HOY), [])

    def test_escenario_de_la_demostracion(self):
        """Datos de ejemplo: la 1.ª sugerencia debe aprovechar algo que vence en <= 3 días
        y ningún ingrediente vencido (pollo, yogur) puede aparecer como usado."""
        stock = ingredientes_de_ejemplo(HOY)
        sugerencias = sugerir_recetas(stock, RECETAS, HOY)
        self.assertTrue(sugerencias)
        self.assertLessEqual(sugerencias[0].dias_mas_urgente, 3)
        for sug in sugerencias:
            for uso in sug.usados:
                self.assertGreaterEqual(uso.dias, 0, f"{sug.receta.nombre} usa un vencido")
        usados = {u.lote.nombre for s in sugerencias for u in s.usados}
        self.assertNotIn("Pollo", usados)
        self.assertNotIn("Yogur", usados)

    def test_recetas_predefinidas_son_consistentes(self):
        nombres = [r.nombre for r in RECETAS]
        self.assertEqual(len(nombres), len(set(nombres)), "hay recetas con nombre repetido")
        for r in RECETAS:
            self.assertTrue(r.ingredientes, r.nombre)
            self.assertTrue(r.instrucciones, r.nombre)


if __name__ == "__main__":
    unittest.main()
