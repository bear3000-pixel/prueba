# Food Saver — aprovecha tus ingredientes antes de que venzan

Solución al reto **Food Saver** del evento *Prompt & Solve*: una aplicación de escritorio para Windows
(se entrega como `FoodSaver.exe`) que ayuda a un hogar a reducir el desperdicio de alimentos.

- Registra ingredientes con **cantidad, unidad y fecha de vencimiento**, y permite **editarlos y eliminarlos**.
- Los **ordena por vencimiento** (el que vence primero, arriba) y resalta los que están por vencer (≤ 3 días).
- Los **vencidos van en una lista aparte** y se **excluyen de las recetas**.
- **Sugiere recetas** de una colección predefinida (17), priorizando las que aprovechan lo que está por
  vencer, e indica **qué ingredientes faltan**.
- **Rechaza datos inválidos** (cantidad 0, negativa, con letras…, fechas que no existen) con un mensaje claro.
- **Guarda los datos** y siguen ahí al cerrar y volver a abrir el programa.

Está hecha solo con la biblioteca estándar de Python (tkinter): no hay dependencias que instalar para usarla.

---

## 1. Ejecutarla sin compilar

Necesitas Python 3.10+ ([python.org](https://www.python.org/downloads/); en el instalador deja marcado
*tcl/tk and IDLE*).

```bat
python main.py
```

## 2. Obtener el `.exe`

### Opción A — En tu Windows (doble clic)
Haz doble clic en **`build_exe.bat`**. Instala PyInstaller, corre las pruebas y crea **`dist\FoodSaver.exe`**.

### Opción B — Con GitHub (sin instalar nada)
El archivo `.github/workflows/build-exe.yml` compila el `.exe` en un servidor Windows en cada `push`:
GitHub → pestaña **Actions** → la última ejecución → sección **Artifacts** → descarga **FoodSaver-exe**
(viene dentro de un `.zip`). También se puede lanzar a mano con *Run workflow*.

> Si Windows muestra «SmartScreen protegió su PC» o un antivirus se queja, es normal con `.exe` nuevos
> creados con PyInstaller: *Más información → Ejecutar de todas formas*. Prueba el `.exe` en el equipo
> donde lo vas a presentar **antes** del evento.

Los datos se guardan en `%APPDATA%\FoodSaver\ingredientes.json` (si algo falla, el detalle técnico queda en
`errores.log` en esa misma carpeta).

---

## 3. Mapa del código

```
main.py                    Punto de entrada (lo que empaqueta PyInstaller)
food_saver/
  modelo.py                Ingrediente + validaciones + estado (vencido / por vencer) + formato de texto
  logica.py                Ordenar, separar vencidos y sugerir recetas  (funciones puras)
  recetas.py               Colección predefinida de recetas
  almacenamiento.py        Guardar / cargar JSON (escritura atómica, archivo dañado no rompe la app)
  ejemplos.py              Datos de ejemplo para la demo (fechas relativas a hoy)
  app.py                   Interfaz tkinter: solo dibuja y conecta botones
tests/                     53 pruebas automáticas (python -m unittest discover -s tests)
build_exe.bat              Crea el .exe en Windows
.github/workflows/         Crea el .exe en GitHub Actions
```

Idea de diseño: **las reglas no dependen de la pantalla**. `modelo.py` y `logica.py` no importan tkinter y
reciben la fecha de «hoy» como parámetro, por eso se pueden probar sin abrir ventanas.

### Requisito del reto → dónde está → qué prueba lo comprueba

| Requisito (documento del reto) | Código | Prueba |
|---|---|---|
| Registrar ingrediente: nombre, cantidad, unidad, vencimiento | `modelo.crear_ingrediente`, `app._enviar_formulario` | `test_agregar_ingrediente_valido` |
| Agregar y **actualizar** ingredientes | `app._entrar_en_edicion` | `test_editar_actualiza_en_lugar_de_duplicar` |
| **Ordenar por fecha de vencimiento** | `logica.ordenar_por_vencimiento` | `test_ordena_por_fecha_de_vencimiento`, `test_orden_por_vencimiento_y_vencidos_aparte` |
| **Rechazar cantidades inválidas** | `modelo.validar_cantidad` | `test_rechaza_cantidades_invalidas`, `test_cantidades_invalidas_se_rechazan_con_mensaje` |
| **Señalar vencidos por separado** | `logica.clasificar` + tabla «Vencidos» | `test_vencidos_van_aparte` |
| **Excluir vencidos** de las sugerencias | `logica.sugerir_recetas` | `test_los_vencidos_se_excluyen_de_las_sugerencias`, `test_vencido_no_genera_receta` |
| **Sugerir recetas** con lo disponible | `logica.sugerir_recetas` | `test_receta_completa_y_parcial`, `test_escenario_de_la_demostracion` |
| **Identificar ingredientes faltantes** | `Sugerencia.faltantes` + panel de detalle | `test_receta_completa_y_parcial` |
| Colección pequeña de recetas | `recetas.RECETAS` | `test_recetas_predefinidas_son_consistentes` |
| **Conservar datos** al reabrir | `almacenamiento.py` | `test_se_guarda_en_disco_y_sobrevive_al_reabrir`, `test_archivo_danado_no_rompe_y_se_respalda` |
| Manejar errores comunes de entrada | `modelo.validar_*`, `parsear_fecha` | `test_fechas_invalidas`, `test_nombre_y_fecha_invalidos` |

---

## 4. Guion de demostración (≈ 2 minutos)

El flujo que pide el reto: *«registrar varios ingredientes con distintas fechas y encontrar una receta que
aproveche uno próximo a vencer»*.

1. **Error de entrada:** escribe `Leche`, cantidad `0` (o `abc`) y pulsa *Agregar* → mensaje rojo, no se guarda nada.
2. **Registrar** con fechas distintas (usa fechas cercanas a hoy):
   `Huevos · 6 unidades · en 5 días`, `Queso · 200 g · en 10 días`, `Tomates · 4 unidades · en 2 días`.
   Se ordenan solos y los de ≤ 3 días salen en amarillo con ⚠.
3. **Vencido:** agrega `Pollo · 500 g` con la fecha de **ayer** → aparece en la tabla *Vencidos*, en rojo.
4. **Receta:** arriba en *Recetas sugeridas* aparece *Omelette de queso y tomate*, con la columna
   *Aprovecha: Tomates (en 2 días)*. Ábrela para ver ingredientes y preparación. El pollo vencido **no** se usa.
5. Marca *«solo recetas que puedo cocinar ya»* → quedan solo las completas.
6. **Editar** (doble clic en una fila) y **cerrar y reabrir** el programa → los datos siguen ahí.

Atajo: el botón **Cargar ejemplo** llena todo con datos ficticios cuyas fechas se calculan respecto a hoy.

---

## 5. Qué revisar con ojo crítico (decisiones y límites conocidos)

Estas son decisiones que tomó el código y que conviene que el equipo entienda y pueda defender:

- **Vencido = fecha anterior a hoy.** Un ingrediente que vence *hoy* todavía cuenta como utilizable. *(modelo.esta_vencido)*
- **Las recetas piden ingredientes por nombre, no por cantidad.** No se compara cuánto necesita la receta
  contra cuánto hay, ni se convierten unidades. Es suficiente para el reto, pero es un límite.
- **Coincidencia de nombres:** ignora mayúsculas, acentos y plurales (`Tomates` = `tomate`, `Limón` = `limones`)
  y acepta nombres más largos (`Leche entera` sirve para `leche`). Falso positivo conocido: `pasta de tomate`
  contaría como `tomate`. *(logica.coincide_ingrediente)*
- **Orden de recetas:** cada ingrediente aprovechado suma 5 puntos si vence en ≤ 3 días, 3 si ≤ 7 días y 1 si no;
  gana el mayor puntaje y se desempata por menos faltantes. Es una heurística: las constantes están al inicio de
  `logica.py`.
- **Varias compras del mismo producto** con distinta fecha son filas separadas, y la receta usa la que vence antes.
- **La fecha de «hoy» es la del reloj del computador.** Si cambia la fecha del sistema, cambian los estados.
- Sal, agua, aceite y especias básicas se asumen disponibles y no aparecen en las recetas.

## 6. Cómo se verificó

- `python -m unittest discover -s tests` → pruebas de validaciones, lógica, almacenamiento **y de la interfaz real**
  (se crea la ventana y se simula escribir en el formulario, seleccionar, editar y eliminar).
- Revisión visual de la pantalla con datos de ejemplo, a zoom normal y al 150 % (columnas sin cortarse).
- Ejecución del programa empaquetado con PyInstaller para confirmar que abre.
- El workflow de GitHub repite pruebas y empaquetado en Windows y comprueba que el `.exe` abre.

> Nota de transparencia para la rúbrica del evento: este código fue generado con un agente de IA (Claude Code)
> a partir del enunciado del reto. Lo que cuenta ante el jurado es que el equipo **entienda, revise y pueda
> modificar** lo generado; por eso el código está comentado en español y esta página resume cada decisión.
