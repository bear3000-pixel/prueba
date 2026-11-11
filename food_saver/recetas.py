"""Colección predefinida de recetas (el reto indica que basta una colección pequeña).

Cada receta lista solo sus ingredientes PRINCIPALES. A propósito se omiten agua,
sal, aceite y especias básicas: se asume que todo hogar los tiene, y así no
aparecen como "faltantes" en todas las sugerencias.

Los nombres van en singular. Al comparar con lo que escribe el usuario se ignoran
mayúsculas, acentos y plurales (ver ``coincide_ingrediente`` en logica.py), así que
"Tomates", "tomate" y "TOMATE" cuentan como el mismo ingrediente.

Para agregar una receta basta con añadir otra línea a RECETAS.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Receta:
    nombre: str
    ingredientes: tuple[str, ...]
    instrucciones: tuple[str, ...]  # pasos breves, en orden
    # Los campos de abajo son opcionales: las recetas predefinidas no los usan.
    # Las recetas que crea el usuario (recetas_usuario.py) sí:
    cantidades: tuple[tuple[float, str], ...] = ()  # (cantidad, unidad) de cada ingrediente, en el mismo orden
    propia: bool = False                            # True = la creó el usuario
    id: str = ""                                    # identificador (solo las propias)


RECETAS: tuple[Receta, ...] = (
    Receta(
        "Omelette de queso y tomate",
        ("huevo", "queso", "tomate"),
        (
            "Pica el tomate y corta o ralla el queso.",
            "Bate los huevos con una pizca de sal.",
            "Cuaja los huevos en una sartén con un poco de aceite.",
            "Agrega el tomate y el queso, dobla el omelette y sirve caliente.",
        ),
    ),
    Receta(
        "Huevos revueltos con espinaca",
        ("huevo", "espinaca", "cebolla"),
        (
            "Pica la cebolla y sofríela 3 minutos.",
            "Agrega la espinaca y cocina hasta que se ablande.",
            "Añade los huevos batidos y revuelve hasta que cuajen.",
        ),
    ),
    Receta(
        "Panqueques",
        ("harina", "leche", "huevo"),
        (
            "Mezcla 1 taza de harina, 1 taza de leche y 1 huevo hasta que no queden grumos.",
            "Cocina porciones en una sartén caliente, unos 2 minutos por lado.",
            "Sirve con fruta o miel.",
        ),
    ),
    Receta(
        "Tostadas francesas",
        ("pan", "huevo", "leche"),
        (
            "Bate el huevo con un chorrito de leche.",
            "Remoja las rebanadas de pan por ambos lados.",
            "Dóralas en una sartén con un poco de mantequilla o aceite.",
        ),
    ),
    Receta(
        "Puré de papa",
        ("papa", "leche", "mantequilla"),
        (
            "Pela las papas y hiérvelas hasta que estén blandas.",
            "Escúrrelas y aplástalas con la mantequilla.",
            "Agrega leche tibia poco a poco hasta lograr la textura deseada.",
        ),
    ),
    Receta(
        "Sándwich de jamón y queso",
        ("pan", "jamon", "queso"),
        (
            "Arma el sándwich con el jamón y el queso entre el pan.",
            "Tuéstalo en una sartén o sandwichera hasta que el queso se derrita.",
        ),
    ),
    Receta(
        "Quesadillas",
        ("tortilla", "queso"),
        (
            "Pon queso sobre la mitad de cada tortilla y dóblala.",
            "Cocina en sartén seca, 2 minutos por lado, hasta que el queso se derrita.",
        ),
    ),
    Receta(
        "Pasta con salsa de tomate",
        ("pasta", "tomate", "ajo", "cebolla"),
        (
            "Hierve la pasta en agua con sal y escúrrela.",
            "Sofríe cebolla y ajo picados; agrega el tomate picado y cocina 10 minutos.",
            "Mezcla la salsa con la pasta y sirve.",
        ),
    ),
    Receta(
        "Sopa de verduras",
        ("zanahoria", "papa", "cebolla", "ajo"),
        (
            "Pica todas las verduras en cubos pequeños.",
            "Sofríe la cebolla y el ajo; agrega zanahoria y papa.",
            "Cubre con agua y hierve 20 minutos. Sazona con sal.",
        ),
    ),
    Receta(
        "Arroz con pollo y verduras",
        ("arroz", "pollo", "zanahoria", "cebolla"),
        (
            "Dora el pollo en trozos con la cebolla picada.",
            "Agrega la zanahoria en cubitos y el arroz; revuelve 1 minuto.",
            "Añade el doble de agua que de arroz y cocina tapado 18 minutos.",
        ),
    ),
    Receta(
        "Arroz frito con huevo",
        ("arroz", "huevo", "cebolla", "zanahoria"),
        (
            "Saltea cebolla y zanahoria picadas en una sartén grande.",
            "Agrega el arroz cocido (mejor del día anterior) y mezcla.",
            "Haz un hueco, revuelve ahí los huevos y combina todo.",
        ),
    ),
    Receta(
        "Guiso de lentejas",
        ("lenteja", "zanahoria", "cebolla", "tomate", "ajo"),
        (
            "Sofríe cebolla, ajo y tomate picados.",
            "Agrega las lentejas lavadas, la zanahoria en cubos y agua suficiente.",
            "Cocina a fuego bajo 30 minutos o hasta que las lentejas estén tiernas.",
        ),
    ),
    Receta(
        "Frijoles con arroz",
        ("frijol", "arroz", "cebolla", "ajo"),
        (
            "Sofríe cebolla y ajo picados.",
            "Agrega los frijoles cocidos con un poco de su caldo y hierve 10 minutos.",
            "Sirve sobre el arroz recién cocido.",
        ),
    ),
    Receta(
        "Pollo al limón con papas",
        ("pollo", "limon", "papa", "ajo"),
        (
            "Marina el pollo con jugo de limón, ajo picado y sal.",
            "Coloca el pollo y las papas en cubos en una bandeja.",
            "Hornea a 200 °C por 40 minutos, volteando a la mitad.",
        ),
    ),
    Receta(
        "Ensalada de atún",
        ("atun", "tomate", "cebolla", "limon"),
        (
            "Pica el tomate y la cebolla en cubos pequeños.",
            "Mezcla con el atún escurrido.",
            "Aliña con jugo de limón y sal.",
        ),
    ),
    Receta(
        "Batido de plátano y leche",
        ("platano", "leche"),
        (
            "Pela el plátano y córtalo en trozos.",
            "Licúalo con 1 taza de leche fría hasta que quede suave.",
        ),
    ),
    Receta(
        "Ensalada de frutas",
        ("manzana", "platano", "naranja"),
        (
            "Lava y pica la manzana y el plátano en cubos.",
            "Agrega el jugo de la naranja para que no se oscurezcan.",
            "Mezcla y sirve fría.",
        ),
    ),
)
