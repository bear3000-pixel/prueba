"""Genera los datos que comparten la versión de escritorio (Python) y la web/Android (JavaScript).

Produce dos archivos a partir del código Python, que es la referencia:
  * web/js/recetas.js            las recetas predefinidas (así no se transcriben a mano)
  * web/tests/referencia.json    casos con su resultado esperado: validaciones, fechas, conversiones,
                                 sugerencias de recetas, etc. Las pruebas de Node (web/tests/*.test.js)
                                 ejecutan el JavaScript con esos mismos casos y exigen resultados IDÉNTICOS.

Cómo usarlo, desde la carpeta raíz del proyecto:

    python web/tests/generar_referencia.py          # vuelve a escribir los dos archivos

Si cambias una regla en el Python, ejecútalo otra vez: tests/test_web_referencia.py falla mientras los
archivos estén desactualizados, para que las dos versiones no se separen sin que nadie se dé cuenta.
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RAIZ))

from food_saver import recetas_usuario as ru  # noqa: E402
from food_saver.ejemplos import ingredientes_de_ejemplo  # noqa: E402
from food_saver.logica import (  # noqa: E402
    clasificar,
    coincide_ingrediente,
    ordenar_por_vencimiento,
    sugerir_recetas,
)
from food_saver.modelo import (  # noqa: E402
    UNIDADES,
    ErrorValidacion,
    Ingrediente,
    autoformatear_fecha,
    convertir_cantidad,
    describir_vencimiento,
    formatear_cantidad,
    formatear_fecha,
    normalizar,
    parsear_fecha,
    texto_cantidad,
    validar_cantidad,
    validar_nombre,
    validar_unidad,
)
from food_saver.recetas import RECETAS  # noqa: E402

HOY = date(2026, 6, 15)
RUTA_RECETAS_JS = RAIZ / "web" / "js" / "recetas.js"
RUTA_REFERENCIA = RAIZ / "web" / "tests" / "referencia.json"


def _resultado(funcion):
    """{'ok': valor} o {'error': mensaje, 'campo': campo} (así se comparan también los errores)."""
    try:
        return {"ok": funcion()}
    except ErrorValidacion as error:
        return {"error": str(error), "campo": error.campo}


def _receta_a_dict(receta) -> dict:
    return {
        "nombre": receta.nombre,
        "ingredientes": list(receta.ingredientes),
        "instrucciones": list(receta.instrucciones),
        "cantidades": [list(c) for c in receta.cantidades],
        "propia": receta.propia,
        "id": receta.id,
    }


def _ingrediente(nombre, dias, cantidad=1, unidad="unidades") -> Ingrediente:
    return Ingrediente(nombre, cantidad, unidad, HOY + timedelta(days=dias), id=f"{nombre}-{dias}")


def _resumen(sugerencias) -> list:
    """Forma común de una lista de sugerencias, igual en Python y en JavaScript."""
    return [
        {
            "receta": s.receta.nombre,
            "usados": [[u.requerido, u.lote.nombre, u.dias, list(u.necesita) if u.necesita else None] for u in s.usados],
            "faltantes": list(s.faltantes),
            "descartados": list(s.descartados_por_vencidos),
            "insuficientes": [
                [i.requerido, i.lote.nombre, i.dias, list(i.necesita), list(i.tienes)] for i in s.insuficientes
            ],
            "puntaje": s.puntaje,
            "diasMasUrgente": s.dias_mas_urgente,
            "completa": s.completa,
            "total": s.total_ingredientes,
        }
        for s in sugerencias
    ]


# --------------------------------------------------------------------------- #
# Casos
# --------------------------------------------------------------------------- #
ENTRADAS_AUTOFORMATO = [
    "", "0", "02", "021", "0211", "02112026", "021120261", "2/11/2026", "02/1/", "1/1/2026", "02/", "02/11/",
    "02/11/2026", "02/11/26", "mañana", "ab0c2d", "123456789", "0211202699", "2026-11-20", "2026-1-5", "20-11-2026",
    "20.11.2026", "02/11/2026 ", "02/11/2026/", "//02", "02//11", "31022026", "٠٢", "5/12/2026", "5/", "5//1/",
]
ENTRADAS_FECHA = [
    "", "   ", "25/12/2026", "2026-12-25", "25-12-2026", " 25/12/2026 ", "5/1/2027", "05/01/2027", "31/02/2026",
    "29/02/2028", "29/02/2026", "30/04/2026", "31/04/2026", "32/01/2026", "0/1/2026", "1/0/2026", "25/13/2026",
    "mañana", "25/12/26", "25/12/0226", "25/12/2926", "25/12/0000", "01/01/2000", "31/12/2100", "01/01/2101",
    "31/12/1999", "2026/12/25", "2026-13-01", "2026-02-30", "12-31-2026", "1/1/2026", "123/1/2026",
]
ENTRADAS_CANTIDAD = [
    "", "   ", "0", "0,0", "-1", "-0.5", "abc", "1e3", "nan", "inf", "1_000", "1,2,3", "2 kg", "0.0001", "0,0005",
    "9" * 400, "5000000", "1000000", "1000001", "2", " 3 ", "1,5", "1.5", ".25", "5.", "007", "0.001", "999999.9999",
    "١٢", "--3", "+3", None, 4, 1.5,
]
ENTRADAS_NOMBRE = ["", "   ", "123", "!!!", "a" * 50, "a" * 51, "  Leche    entera ", "Piña", "ñandú", "Ünï cödé", None]
ENTRADAS_UNIDAD = ["kg", "g", "L", "ml", "unidades", "tazas", "KG", "toneladas", "", " kg ", None]
CONVERSIONES = [
    (1500, "g", "kg"), (2, "kg", "g"), (250, "ml", "L"), (1, "L", "ml"), (3, "unidades", "unidades"),
    (3, "unidades", "g"), (1, "kg", "L"), (1, "tazas", "ml"), (0.3, "kg", "g"), (300, "g", "kg"), (7, "kg", "kg"),
]
NUMEROS_FORMATO = [0, 1, 2, 1.5, 0.25, 0.125, 1000000, 0.001, 12.34, 99.5, 3.0]
NOMBRES_NORMALIZAR = ["  Limón  Verde ", "PIÑA", "Plátano", "ÁÉÍÓÚ", "", "  ", "Ñandú", "Çedilla"]
PARES_COINCIDENCIA = [
    ("tomate", "Tomates"), ("limon", "Limón"), ("limon", "limones"), ("frijol", "Frijoles"), ("pan", "Panes"),
    ("huevo", "HUEVOS"), ("leche", "Leche entera"), ("tomate", "Tomates cherry"), ("platano", "Plátano"),
    ("jamon", "Jamón"), ("pan", "papa"), ("arroz", "maiz"), ("leche", "lechuga"), ("ajo", "ajonjoli"),
    ("pollo", "polvo"), ("tomate", "pasta"), ("pasta", "pastas"), ("pasta de tomate", "tomate"), ("gas", "gases"),
    ("arroz integral", "arroz"), ("arroz", "arroz integral"),
]
PASOS = [
    "", "   \n  \n", "123\n456", "x\n" * 21, "a" * 301, "a" * 300, "1. Mezclar\n2) Amasar\n- Hornear\n• Servir\n* Fin",
    "2 huevos batidos\n1.5 tazas de leche\nHornear 2-3 minutos", "Paso uno\r\nPaso dos\rPaso tres", "1.Mezclar", "-Mezclar",
    ["Uno", "Dos"], [], ["123"],
]
INGREDIENTES_VALIDOS = [("Papa", "3", "unidades"), ("Huevo", "4", "unidades"), ("Cebolla", "1,5", "unidades")]
CASOS_RECETA = [
    {"nombre": "Tortilla de papa", "filas": [list(f) for f in INGREDIENTES_VALIDOS], "pasos": "1. Pela\n2) Fríe\n- Sirve"},
    {"nombre": "  Mi   guiso ", "filas": [["Papa", "3", "unidades"]], "pasos": "Cocinar"},
    {"nombre": "", "filas": [["Papa", "3", "unidades"]], "pasos": "Cocinar"},
    {"nombre": "123", "filas": [["Papa", "3", "unidades"]], "pasos": "Cocinar"},
    {"nombre": "a" * 61, "filas": [["Papa", "3", "unidades"]], "pasos": "Cocinar"},
    {"nombre": "OMELETTE DE QUESO Y TOMATE", "filas": [["Huevo", "2", "unidades"]], "pasos": "Cocinar"},
    {"nombre": "Otra", "filas": [], "pasos": "Cocinar"},
    {"nombre": "Otra", "filas": [["Papa", "", "unidades"]], "pasos": "Cocinar"},
    {"nombre": "Otra", "filas": [["Papa", "0", "unidades"]], "pasos": "Cocinar"},
    {"nombre": "Otra", "filas": [["Papa", "-2", "unidades"]], "pasos": "Cocinar"},
    {"nombre": "Otra", "filas": [["Papa", "abc", "unidades"]], "pasos": "Cocinar"},
    {"nombre": "Otra", "filas": [["Papa", "1e3", "g"]], "pasos": "Cocinar"},
    {"nombre": "Otra", "filas": [["Papa", "5000000", "g"]], "pasos": "Cocinar"},
    {"nombre": "Otra", "filas": [["Papa", "1", "toneladas"]], "pasos": "Cocinar"},
    {"nombre": "Otra", "filas": [["", "1", "g"]], "pasos": "Cocinar"},
    {"nombre": "Otra", "filas": [["123", "1", "g"]], "pasos": "Cocinar"},
    {"nombre": "Otra", "filas": [["Tomate", "1", "unidades"], ["TOMATES", "2", "unidades"]], "pasos": "Cocinar"},
    {"nombre": "Otra", "filas": [["Papa", "1", "g"]], "pasos": ""},
    {"nombre": "Otra", "filas": [[f"Ingrediente{chr(97 + i)}x", "1", "g"] for i in range(21)], "pasos": "Cocinar"},
]
NOMBRES_EXISTENTES = [r.nombre for r in RECETAS]

# Despensas de prueba: [nombre, días hasta vencer, cantidad, unidad]
PANTRY_PLURALES = [
    ["LIMONES", 9, 3, "unidades"], ["Plátanos", 3, 2, "unidades"], ["tomate", 3, 1, "unidades"],
    ["Leche entera", 2, 1, "L"], ["Jamón", 9, 200, "g"], ["PAN", 3, 1, "paquetes"], ["queso", 9, 100, "g"],
]
PANTRY_LOTES = [["Leche", 15, 1, "L"], ["Leche", 1, 2, "L"], ["Plátano", 9, 2, "unidades"], ["Huevos", 0, 6, "unidades"]]
PANTRY_VENCIDOS = [["Plátano", -1, 2, "unidades"], ["Leche", -10, 1, "L"], ["Pollo", -3, 500, "g"]]
PANTRY_DEMO = [["Huevos", 5, 6, "unidades"], ["Queso", 10, 200, "g"], ["Tomates", 2, 4, "unidades"]]
PANTRY_CANTIDADES = [
    ["Harina", 4, 300, "g"], ["Harina", 9, 0.3, "kg"], ["Agua", 4, 1, "L"], ["Tomate", 2, 500, "g"], ["Azúcar", -2, 5, "kg"],
    ["Mantequilla", 20, 100, "g"],
]
PANTRY_POCA = [["Harina", 5, 300, "g"], ["Agua", 30, 100, "ml"]]
# Cantidades EXACTAS a las que piden las recetas propias: alcanzan (no son «insuficientes»)
PANTRY_JUSTA = [["Harina", 5, 0.5, "kg"], ["Agua", 5, 0.3, "L"], ["Tomate", 5, 3, "unidades"]]
# 0,1 kg + 0,7 kg da 0.7999999999999999 en coma flotante: aun así alcanza para los 0,8 kg de «Pastel»
PANTRY_DECIMALES = [["Harina", 5, 0.1, "kg"], ["Harina", 6, 0.7, "kg"]]
RECETAS_PROPIAS = [
    {"nombre": "Pan casero", "filas": [["Harina", "500", "g"], ["Agua", "300", "ml"]], "pasos": "Mezclar\nAmasar\nHornear", "id": "r1"},
    {"nombre": "Salsa", "filas": [["Tomate", "3", "unidades"]], "pasos": "Cocinar", "id": "r2"},
    {"nombre": "Pastel", "filas": [["Harina", "0,8", "kg"]], "pasos": "Hornear", "id": "r4"},
    {"nombre": "Galletas", "filas": [["Harina", "200", "g"], ["Azúcar", "1,5", "kg"], ["Mantequilla", "100", "g"]], "pasos": "Hornear", "id": "r3"},
]


def _despensa(filas):
    return [_ingrediente(n, d, c, u) for n, d, c, u in filas]


def _recetas_propias():
    return [ru.crear_receta(r["nombre"], r["filas"], r["pasos"], id=r["id"]) for r in RECETAS_PROPIAS]


def _escenarios_sugerencias() -> list:
    propias = _recetas_propias()
    todas = list(RECETAS) + propias
    casos = [
        ("ejemplo, predefinidas", None, RECETAS, False),
        ("ejemplo, predefinidas, solo completas", None, RECETAS, True),
        ("demo del reto", PANTRY_DEMO, RECETAS, False),
        ("plurales, acentos y mayúsculas", PANTRY_PLURALES, RECETAS, False),
        ("varios lotes", PANTRY_LOTES, RECETAS, False),
        ("solo vencidos", PANTRY_VENCIDOS, RECETAS, False),
        ("despensa vacía", [], RECETAS, False),
        ("cantidades, todas las recetas", PANTRY_CANTIDADES, todas, False),
        ("cantidades, solo completas", PANTRY_CANTIDADES, todas, True),
        ("poca cantidad", PANTRY_POCA, todas, False),
        ("cantidad justa", PANTRY_JUSTA, todas, False),
        ("suma de decimales", PANTRY_DECIMALES, todas, False),
        ("cantidad justa, solo completas", PANTRY_JUSTA, todas, True),
        ("recetas propias sin despensa", [], todas, False),
    ]
    salida = []
    for nombre, filas, recetas, solo in casos:
        despensa = ingredientes_de_ejemplo(HOY) if filas is None else _despensa(filas)
        salida.append({
            "caso": nombre,
            "despensa": [[i.nombre, i.cantidad, i.unidad, i.vencimiento.isoformat()] for i in despensa],
            "recetas": "predefinidas" if recetas is RECETAS else "todas",
            "soloCompletas": solo,
            "resultado": _resumen(sugerir_recetas(despensa, recetas, HOY, solo_completas=solo)),
        })
    return salida


def construir_referencia() -> dict:
    propias = _recetas_propias()
    return {
        "hoy": HOY.isoformat(),
        "unidades": list(UNIDADES),
        "autoformato": [
            {"entrada": e, "escribiendo": b, "salida": autoformatear_fecha(e, b)}
            for e in ENTRADAS_AUTOFORMATO for b in (False, True)
        ],
        "fechas": [{"entrada": e, **_resultado(lambda e=e: parsear_fecha(e).isoformat())} for e in ENTRADAS_FECHA],
        "cantidades": [{"entrada": e, **_resultado(lambda e=e: validar_cantidad(e))} for e in ENTRADAS_CANTIDAD],
        "nombres": [{"entrada": e, **_resultado(lambda e=e: validar_nombre(e))} for e in ENTRADAS_NOMBRE],
        "unidadesValidas": [{"entrada": e, **_resultado(lambda e=e: validar_unidad(e))} for e in ENTRADAS_UNIDAD],
        "conversiones": [
            {"cantidad": c, "de": de, "a": a, "salida": convertir_cantidad(c, de, a)} for c, de, a in CONVERSIONES
        ],
        "formatoCantidad": [{"entrada": n, "salida": formatear_cantidad(n)} for n in NUMEROS_FORMATO],
        "textoCantidad": [
            {"cantidad": c, "unidad": u, "salida": texto_cantidad(c, u)}
            for c in (1, 2, 1.5, 0.5) for u in ("paquetes", "unidades", "tazas", "latas", "kg", "L")
        ],
        "describirVencimiento": [{"dias": d, "salida": describir_vencimiento(d)} for d in range(-5, 11)],
        "formatoFecha": [{"entrada": f, "salida": formatear_fecha(date.fromisoformat(f))} for f in ("2026-06-15", "2000-01-05", "2100-12-31")],
        "normalizar": [{"entrada": n, "salida": normalizar(n)} for n in NOMBRES_NORMALIZAR],
        "coincidencias": [{"requerido": a, "disponible": b, "salida": coincide_ingrediente(a, b)} for a, b in PARES_COINCIDENCIA],
        "pasos": [{"entrada": p, **_resultado(lambda p=p: list(ru.validar_pasos(p)))} for p in PASOS],
        "recetasNuevas": [
            {
                "caso": c,
                **_resultado(lambda c=c: _receta_a_dict(
                    ru.crear_receta(c["nombre"], c["filas"], c["pasos"], nombres_existentes=NOMBRES_EXISTENTES, id="r0"))),
            }
            for c in CASOS_RECETA
        ],
        "recetasPropiasEspec": RECETAS_PROPIAS,
        "recetasPropias": [_receta_a_dict(r) for r in propias],
        "datosGuardadosDeRecetas": [ru.a_dict(r) for r in propias],
        "ejemplos": [
            [i.nombre, i.cantidad, i.unidad, i.vencimiento.isoformat()] for i in ingredientes_de_ejemplo(HOY)
        ],
        "orden": _orden_y_clasificacion(),
        "sugerencias": _escenarios_sugerencias(),
    }


def _orden_y_clasificacion() -> dict:
    filas = [
        ["Arroz", 200, 1, "kg"], ["zanahoria", 2, 1, "unidades"], ["Arroz", 2, 1, "kg"], ["Pollo", -1, 500, "g"],
        ["Leche", 0, 1, "L"], ["ayer", -1, 1, "unidades"], ["hace_mucho", -30, 1, "unidades"], ["Ñoquis", 5, 1, "paquetes"],
        ["noquis", 5, 1, "paquetes"], ["Óleo", 5, 1, "latas"],
    ]
    despensa = _despensa(filas)
    vigentes, vencidos = clasificar(despensa, HOY)
    return {
        "despensa": [[i.nombre, i.cantidad, i.unidad, i.vencimiento.isoformat(), i.id] for i in despensa],
        "ordenados": [i.id for i in ordenar_por_vencimiento(despensa)],
        "vigentes": [i.id for i in vigentes],
        "vencidos": [i.id for i in vencidos],
    }


def construir_recetas_js() -> str:
    datos = json.dumps([_receta_a_dict(r) for r in RECETAS], ensure_ascii=False, indent=2)
    return (
        "/**\n"
        " * Colección predefinida de recetas (17), la misma de food_saver/recetas.py.\n"
        " * ARCHIVO GENERADO por web/tests/generar_referencia.py: no se edita a mano (se vuelve a generar).\n"
        " * Cada receta lista solo sus ingredientes PRINCIPALES (sin agua, sal, aceite ni especias básicas).\n"
        " */\n"
        f"export const RECETAS = {datos};\n"
    )


def serializar_referencia() -> str:
    return json.dumps(construir_referencia(), ensure_ascii=False, indent=1) + "\n"


def main() -> None:
    RUTA_RECETAS_JS.write_text(construir_recetas_js(), encoding="utf-8")
    RUTA_REFERENCIA.write_text(serializar_referencia(), encoding="utf-8")
    print(f"Escritos:\n  {RUTA_RECETAS_JS.relative_to(RAIZ)}\n  {RUTA_REFERENCIA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
