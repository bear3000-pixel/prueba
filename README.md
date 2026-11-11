# Food Saver

Aplicación de consola en **Java 17+** (solo librería estándar) que ayuda a un hogar a **priorizar los ingredientes
próximos a vencer** y a elegir recetas que reduzcan el desperdicio de alimentos.

## Estructura de carpetas

```
.
├── README.md
├── .gitignore
└── src/
    └── foodsaver/
        ├── Main.java                  Menú interactivo (Scanner) y ciclo principal
        ├── Ingrediente.java           Lote en la despensa: nombre, cantidad, unidad, vencimiento (inmutable)
        ├── IngredienteReceta.java     Lo que pide una receta: nombre, cantidad, unidad
        ├── Receta.java                Nombre, lista de IngredienteReceta e instrucciones
        ├── CatalogoRecetas.java       7 recetas predefinidas cargadas en el código
        ├── Despensa.java              Agregar / actualizar / ordenar / separar vencidos (usa un Clock)
        ├── SugeridorRecetas.java      Sugerencias, prioridad por vencimiento y faltantes
        ├── Sugerencia.java            Resultado: receta + ingredientes próximos a vencer que aprovecha
        ├── Faltante.java              Resultado: qué ingrediente falta y cuánto
        ├── Unidad.java                g, kg, ml, l, unidad y sus conversiones
        ├── Validaciones.java          Reglas de validación de nombre, cantidad y fecha (yyyy-MM-dd)
        ├── DatoInvalidoException.java Excepción de dato inválido (el menú la captura y sigue)
        ├── Reportes.java              Todo lo que se imprime (separado de la lógica)
        └── Demostracion.java          Demostración con reloj fijo
```

## Compilar y ejecutar

Requiere JDK 17 o superior (`javac -version`). Desde la raíz del proyecto:

```bash
# Compilar (genera las clases en la carpeta out/)
javac -encoding UTF-8 -d out src/foodsaver/*.java

# Ejecutar el menú interactivo
java -cp out foodsaver.Main

# Ejecutar solo la demostración (sin menú)
java -cp out foodsaver.Main --demo
```

En Windows use `src\foodsaver\*.java` en el `javac`. Si los acentos se ven mal en `cmd`, ejecute antes `chcp 65001`.
La demostración también está en el menú, opción **6**.

### Menú

```
1. Agregar ingrediente            4. Sugerir recetas
2. Actualizar ingrediente         5. Ver ingredientes faltantes
3. Listar ingredientes            6. Ejecutar demostración
                                  0. Salir
```

- Unidades válidas: `g`, `kg`, `ml`, `l`, `unidad`. Fecha: `yyyy-MM-dd`. La cantidad acepta punto o coma decimal.
- Las entradas inválidas muestran un mensaje de error y vuelven al menú; nada se guarda y el programa no se cae.

## Reglas de negocio y dónde viven

| Regla | Dónde |
|---|---|
| "Próximo a vencer" = faltan **3 días o menos** (constante) | `Ingrediente.DIAS_PROXIMO_A_VENCER` |
| "Casi completa" = faltan **2 ingredientes o menos** (constante) | `SugeridorRecetas.MAX_FALTANTES_CASI_COMPLETA` |
| Cantidad cero, negativa o no numérica; nombre vacío; fecha mal formada | `Validaciones` (lanza `DatoInvalidoException`) |
| Mismo nombre + misma fecha: se **suma** la cantidad (1 kg + 500 g = 1.5 kg) | `Despensa.agregar` |
| Los vencidos van en una sección aparte y **no cuentan** como disponibles | `Despensa.listarVencidos` / `Despensa.lotesVigentesDe` |
| "Hoy" no depende del día real: se inyecta un `Clock` | `Despensa(Clock)`; `Demostracion` usa un reloj fijo |

Detalles de diseño que conviene saber para la sustentación:

- **Lotes:** cada fecha de vencimiento distinta de un mismo ingrediente es un lote aparte (la leche que venció ayer y la
  leche nueva no se mezclan). Los nombres se comparan sin importar mayúsculas ni tildes (`Azucar` = `azúcar`).
- **Unidades:** todo se convierte a una unidad base (g, ml, unidad) para comparar, así 1 kg de arroz cubre los 200 g de una
  receta. Una unidad de otra magnitud (arroz en `unidad` vs. receta en `g`) no se puede comparar y cuenta como faltante.
- **Vence hoy** todavía es utilizable (vigente) y se considera próximo a vencer; vencido es solo lo que venció antes de hoy.
- **Inmutabilidad:** `Ingrediente` no cambia después de creado; "actualizar" crea uno nuevo, así los datos validados en el
  constructor nunca quedan inválidos.
- **Sugerir no consume** la despensa: cada receta se evalúa por separado, por eso dos recetas pueden proponer usar el mismo tomate.

## Cómo funciona el algoritmo de sugerencia

1. Para cada receta se revisa cada ingrediente que pide contra la despensa (`SugeridorRecetas.evaluar`).
2. Solo se consideran lotes **no vencidos**; los vencidos no cuentan ni como disponibles ni como aprovechables.
3. Las cantidades se pasan a unidad base (kg → g, l → ml), así se comparan manzanas con manzanas.
4. Los lotes se recorren del que **vence primero al que vence último** y se "consumen" hasta cubrir la cantidad pedida.
5. Si no alcanza, lo que falta se anota como faltante (en la unidad de la receta); una receta sin faltantes es preparable.
6. Si se consume un lote **próximo a vencer** (≤ 3 días), se anota como ingrediente aprovechado y suma puntos: `4 − días restantes`
   (vence hoy = 4, mañana = 3, en 2 días = 2, en 3 días = 1).
7. El puntaje de la receta es la suma de esos puntos; las recetas preparables se ordenan por puntaje descendente (empate: por nombre).
8. Así, la receta que rescata lo que está más cerca de echarse a perder sale primero, y se muestra qué ingrediente aprovecha.

## Ejemplo de salida de la demostración

Se obtiene con `java -cp out foodsaver.Main --demo`. Siempre es idéntica porque usa un reloj fijo (hoy = 2025-06-10).

```text
======================================================================
FOOD SAVER - DEMOSTRACIÓN
======================================================================
Fecha simulada de hoy: 2025-06-10 (próximo a vencer = 3 días o menos)

======================================================================
PASO 1: Registrar ingredientes
======================================================================
  [OK] Agregado: Leche 1 l (vence 2025-06-05)
  [OK] Agregado: Espinaca 200 g (vence 2025-06-11)
  [OK] Agregado: Tomate 500 g (vence 2025-06-12)
  [OK] Agregado: Huevo 4 unidades (vence 2025-06-25)
  [OK] Sumado al lote existente: Huevo 2 unidades (vence 2025-06-25)
  [OK] Agregado: Arroz 1 kg (vence 2025-12-27)
  [OK] Agregado: Cebolla 3 unidades (vence 2025-06-30)
  [OK] Agregado: Queso 150 g (vence 2025-06-22)
  [OK] Agregado: Pasta 500 g (vence 2025-11-07)
  [OK] Agregado: Aceite 500 ml (vence 2025-10-08)

======================================================================
PASO 2: Despensa ordenada por vencimiento, con los vencidos aparte
======================================================================
--- INGREDIENTES VIGENTES (del que vence primero al que vence último) ---
  Espinaca       200 g          2025-06-11  vence mañana          [PRÓXIMO A VENCER]
  Tomate         500 g          2025-06-12  vence en 2 días       [PRÓXIMO A VENCER]
  Queso          150 g          2025-06-22  vence en 12 días
  Huevo          6 unidades     2025-06-25  vence en 15 días
  Cebolla        3 unidades     2025-06-30  vence en 20 días
  Aceite         500 ml         2025-10-08  vence en 120 días
  Pasta          500 g          2025-11-07  vence en 150 días
  Arroz          1 kg           2025-12-27  vence en 200 días

--- INGREDIENTES VENCIDOS (no se usan en las sugerencias de recetas) ---
  Leche          1 l            2025-06-05  venció hace 5 días    [VENCIDO]

======================================================================
PASO 3: Recetas sugeridas (la leche vencida queda excluida)
======================================================================
1. Omelette de espinaca  (puntaje de urgencia: 3)
   Ingredientes: 3 unidades de huevo, 100 g de espinaca, 50 g de queso
   Aprovecha: 100 g de Espinaca (vence mañana)
   Preparación: Batir los huevos. Saltear la espinaca 2 minutos, agregar los huevos y el queso y cocinar 4 minutos por lado.
2. Arroz con tomate  (puntaje de urgencia: 2)
   Ingredientes: 200 g de arroz, 300 g de tomate, 1 unidad de cebolla, 20 ml de aceite
   Aprovecha: 300 g de Tomate (vence en 2 días)
   Preparación: Sofreír la cebolla picada en el aceite, agregar el tomate en trozos, incorporar el arroz con el doble de agua y cocinar 18 minutos a fuego bajo.
3. Pasta con salsa de tomate  (puntaje de urgencia: 2)
   Ingredientes: 250 g de pasta, 400 g de tomate, 1 unidad de cebolla, 20 ml de aceite
   Aprovecha: 400 g de Tomate (vence en 2 días)
   Preparación: Hervir la pasta 10 minutos. Sofreír la cebolla, agregar el tomate picado y cocinar 15 minutos. Mezclar la salsa con la pasta.

==> Recomendada: Omelette de espinaca
    Aprovecha: 100 g de Espinaca (vence mañana)

======================================================================
PASO 4: Ingredientes faltantes
======================================================================
Una receta que no se puede preparar completa (la leche de la despensa está vencida, por eso cuenta como faltante):
Arroz con leche - le falta:
   - 1 l de leche
   - 100 g de azúcar

Recetas casi completas (les faltan hasta 2 ingredientes):
Tortilla de papa - le falta:
   - 500 g de papa
Arroz con leche - le falta:
   - 1 l de leche
   - 100 g de azúcar
Crepes - le falta:
   - 200 g de harina
   - 500 ml de leche
Sopa de verduras - le falta:
   - 200 g de zanahoria
   - 300 g de papa

======================================================================
PASO 5: Entradas inválidas (el programa no se cae)
======================================================================
  [RECHAZADO] nombre='Harina', cantidad='-5', fecha='2025-07-10' -> La cantidad debe ser mayor que cero (se recibió: -5).
  [RECHAZADO] nombre='Harina', cantidad='0', fecha='2025-07-10' -> La cantidad debe ser mayor que cero (se recibió: 0).
  [RECHAZADO] nombre='Harina', cantidad='mucha', fecha='2025-07-10' -> La cantidad 'mucha' no es un número válido (ejemplo: 2.5).
  [RECHAZADO] nombre='', cantidad='100', fecha='2025-07-10' -> El nombre no puede estar vacío.
  [RECHAZADO] nombre='Harina', cantidad='100', fecha='30/06/2025' -> Fecha inválida '30/06/2025'. Use el formato yyyy-MM-dd con una fecha real (ejemplo: 2025-06-30).

Fin de la demostración.
```
