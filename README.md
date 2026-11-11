# Food Saver — aprovecha tus ingredientes antes de que venzan

Solución al reto **Food Saver** del evento *Prompt & Solve*: una aplicación de escritorio para Windows
(se entrega como `FoodSaver.exe`) que ayuda a un hogar a reducir el desperdicio de alimentos.

- Registra ingredientes con **cantidad, unidad y fecha de vencimiento**, y permite **editarlos y eliminarlos**.
- Los **ordena por vencimiento** (el que vence primero, arriba) y resalta los que están por vencer (≤ 3 días).
- Los **vencidos van en una lista aparte** y se **excluyen de las recetas**.
- **Sugiere recetas** de una colección predefinida (17) más **las que crea el usuario**, priorizando las que
  aprovechan lo que está por vencer, e indica **qué ingredientes faltan**.
- **Recetas propias:** el usuario crea sus recetas con nombre, **ingredientes con cantidad y unidad** y **pasos de
  preparación**; puede editarlas y eliminarlas. La sugerencia compara las cantidades con la despensa (convierte
  kg↔g y L↔ml) y avisa «pide 500 g, tienes 300 g».
- **Fecha con barras automáticas:** al escribir `02112026` el campo muestra `02/11/2026`, solo acepta números y
  avisa en el momento si la fecha completa no existe.
- **Rechaza datos inválidos** (cantidad 0, negativa, nula, con letras…, fechas que no existen) con un mensaje claro,
  tanto al agregar ingredientes como al crear recetas.
- **Guarda los datos** (ingredientes y recetas propias) y siguen ahí al cerrar y volver a abrir el programa.
- **También para Android:** la misma app como **APK** instalable en el celular (y como página web que funciona
  sin internet). Ver la sección 2b.

La versión de escritorio está hecha solo con la biblioteca estándar de Python (tkinter): no hay dependencias que
instalar para usarla. La de Android/web está hecha con HTML, CSS y JavaScript puros, sin librerías.

---

## 1. Ejecutarla sin compilar

Necesitas Python 3.10+ ([python.org](https://www.python.org/downloads/); en el instalador deja marcado
*tcl/tk and IDLE*).

```bat
python main.py             :: apariencia renovada
python main.py --clasico   :: la versión original, por si hiciera falta volver atrás
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

## 2b. Versión para Android (celular)

Es la **misma aplicación** (mismas reglas, mismos mensajes, mismas 17 recetas y recetas propias), escrita en
JavaScript en la carpeta `web/`. Tkinter no existe en Android, así que no se puede «convertir» el programa de
escritorio: se reescribió, y se comprueba que las dos versiones den **los mismos resultados** (ver más abajo).

### Instalar el APK
1. En GitHub: pestaña **Actions** → **Compilar app Android (APK)** → la última ejecución → sección **Artifacts** →
   descarga **FoodSaver-apk** (un `.zip`) y extráelo: dentro está `FoodSaver.apk`.
2. Pásalo al celular (cable USB, Drive, WhatsApp, correo…) y ábrelo desde el administrador de archivos.
3. Android pedirá permiso para **instalar apps de esta fuente** (la del navegador o del administrador de archivos):
   actívalo solo para esa app.
4. Si aparece un aviso de **Google Play Protect** («app no verificada»), elige **Instalar de todos modos**.
   Es normal: el APK está firmado con la clave de depuración, no con una de la tienda de Google Play.

### Usarla como página web (sin instalar nada)
```bash
cd web
python -m http.server 8000          # y abre http://localhost:8000 en el navegador
```
Funciona en cualquier navegador moderno. Con un servidor `https` (por ejemplo GitHub Pages) el navegador del celular
ofrece **«Añadir a la pantalla de inicio»** y la app queda instalada, también sin internet.

### Detalles a conocer
- **Los datos se guardan en el propio celular** (en el almacenamiento de la app) y no se sincronizan con la versión
  de escritorio. El formato es el mismo JSON, por lo que se podrían copiar de una a otra.
- **Botón «atrás» de Android:** primero cierra lo que esté abierto (preguntando si hay una receta sin guardar), luego
  vuelve de «Recetas» a «Despensa» y solo entonces sale de la app.
- En pantallas anchas (tableta o computador) se ven las dos columnas a la vez; en el celular, dos pestañas.
- Tema claro y oscuro automáticos, según la configuración del celular.

### Cómo se mantienen iguales las dos versiones
`web/tests/generar_referencia.py` ejecuta el **Python** y guarda cientos de casos con su resultado esperado
(`web/tests/referencia.json`) y las 17 recetas (`web/js/recetas.js`, así no se transcriben a mano).
`web/tests/paridad.test.js` ejecuta el **JavaScript** con esos mismos casos y exige resultados idénticos: valores,
mensajes de error, orden de las recetas, puntajes. Si cambias una regla en Python,
`tests/test_web_referencia.py` falla hasta que ejecutes `python web/tests/generar_referencia.py`, y entonces las
pruebas de JavaScript te dicen qué falta copiar.

---

## 3. Mapa del código

```
main.py                    Punto de entrada (lo que empaqueta PyInstaller)
food_saver/
  modelo.py                Ingrediente + validaciones + estado (vencido / por vencer) + formato de texto
  logica.py                Ordenar, separar vencidos y sugerir recetas (compara cantidades)  (funciones puras)
  recetas.py               Colección predefinida de recetas y la definición de «Receta»
  recetas_usuario.py       Recetas propias: validaciones (cantidades, pasos, nombres) y su archivo JSON
  almacenamiento.py        Guardar / cargar JSON (escritura atómica, archivo dañado no rompe la app)
  ejemplos.py              Datos de ejemplo para la demo (fechas relativas a hoy)
  app.py                   Interfaz tkinter ORIGINAL: dibuja y conecta botones
  dialogos.py              Ventanas «Crear / editar mi receta» y «Mis recetas»
  app_visual.py            Apariencia renovada: hereda de app.py y solo cambia cómo se ve
  tema.py                  Colores, tipografía y estilos de la apariencia renovada
  icono.py                 Icono de la ventana (generado por assets/generar_icono.py)
assets/icono.ico           Icono del .exe
assets/generar_icono.py    Genera todos los iconos (.exe, ventana, web y Android) desde una sola hoja
web/                       VERSIÓN ANDROID / WEB (JavaScript): index.html, css/, js/, manifest, service worker
  js/modelo.js ...         Las mismas reglas que food_saver/*.py (modelo, logica, recetasUsuario, almacenamiento)
  js/app.js                La pantalla (pestañas, formularios, cuadros de recetas, botón «atrás»)
  tests/                   45 pruebas Node (comparan con Python) + 17 casos de extremo a extremo (Playwright)
android-app/               Envoltorio Capacitor que convierte web/ en un APK
tests/                     193 pruebas automáticas de Python (python -m unittest discover -s tests)
CASOS_DE_PRUEBA.md         Casos de prueba MANUALES con datos exactos y resultado esperado
build_exe.bat              Crea el .exe en Windows
.github/workflows/         Crea el .exe (Windows) y el APK (Android) en GitHub Actions
```

Idea de diseño: **las reglas no dependen de la pantalla**. `modelo.py` y `logica.py` no importan tkinter y
reciben la fecha de «hoy» como parámetro, por eso se pueden probar sin abrir ventanas.

### La apariencia está separada del comportamiento

La mejora visual **no modifica ninguna función existente**. `app_visual.py` define una clase que **hereda** de la
original (`app.py`) y, una vez construida la ventana, cambia colores, tipografía, botones y distribución; además
agrega un encabezado con el logo y un resumen (cuántos ingredientes hay, por vencer y vencidos).

Solo se extienden dos funciones, y ambas llaman primero a la original con `super()`:
`refrescar` (para actualizar el resumen del encabezado) y `_mostrar_mensaje` (para pintar la caja del mensaje).
Una prueba automática (`test_solo_se_extienden_las_funciones_documentadas`) falla si alguien sustituye otra.

### Qué se tocó al agregar la fecha automática y las recetas propias

Estas dos funciones **sí** necesitaron integrarse en el código existente. Se hizo con cambios **aditivos**: lo que
ya había se comporta igual (las pruebas de antes pasan sin cambios, con la versión original y con la renovada).

| Archivo | Qué cambió |
|---|---|
| `modelo.py` | Se agregaron `autoformatear_fecha` y `convertir_cantidad`. No se tocó ninguna función anterior (`parsear_fecha` sigue decidiendo si una fecha existe). |
| `recetas.py` | `Receta` ganó 3 campos **opcionales** (`cantidades`, `propia`, `id`). Las 17 recetas predefinidas no cambian. |
| `logica.py` | `sugerir_recetas` compara cantidades **solo si la receta las trae** (las propias). Las predefinidas dan exactamente los mismos resultados. |
| `almacenamiento.py` | La escritura atómica se extrajo a `escribir_json_atomico` para reutilizarla; `guardar` hace lo mismo que antes. |
| `app.py` | Conexión del campo de fecha, botones «+ Crear mi receta» / «Mis recetas», lista de sugerencias con las recetas propias (★) y detalle con cantidades. |
| `recetas_usuario.py`, `dialogos.py` | **Archivos nuevos**: validación y guardado de recetas propias, y sus ventanas. |

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
| *(extra)* Fecha con barras automáticas | `modelo.autoformatear_fecha`, `app._al_escribir_fecha` | `PruebasAutoformatoFecha`, `PruebasFechaAutomatica` |
| *(extra)* Crear recetas propias (nombre, ingredientes con cantidad, pasos) | `recetas_usuario.crear_receta`, `dialogos.DialogoReceta` | `PruebasCrearReceta`, `test_crear_una_receta` |
| *(extra)* Sin cantidades negativas, nulas ni inválidas en las recetas | `modelo.validar_cantidad` (reutilizada) | `test_cantidades_invalidas_se_rechazan`, `test_las_cantidades_invalidas_no_se_agregan_a_la_receta` |
| *(extra)* Comparar cantidades con la despensa | `logica.sugerir_recetas`, `modelo.convertir_cantidad` | `PruebasCantidadesEnSugerencias`, `test_se_compara_la_cantidad_con_la_despensa` |
| *(extra)* Editar / eliminar recetas propias y conservarlas | `app.guardar_receta_propia`, `recetas_usuario.cargar` | `test_editar_una_receta`, `test_eliminar_una_receta`, `test_las_recetas_propias_sobreviven_al_reabrir` |

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
7. **Fecha automática:** al agregar un ingrediente, escribe en «Vence» solo `02112026` → aparece `02/11/2026`.
8. **Receta propia:** pulsa **+ Crear mi receta**, ponle nombre, agrega ingredientes con cantidad (prueba una cantidad
   `0` o `-3` → la rechaza) y escribe los pasos, uno por línea. Al guardar aparece con una ★ entre las sugerencias;
   si pides más cantidad de la que tienes, el detalle dice «pide 500 g, tienes 300 g».

Atajo: el botón **Cargar ejemplo** llena todo con datos ficticios cuyas fechas se calculan respecto a hoy.

---

## 5. Qué revisar con ojo crítico (decisiones y límites conocidos)

Estas son decisiones que tomó el código y que conviene que el equipo entienda y pueda defender:

- **Vencido = fecha anterior a hoy.** Un ingrediente que vence *hoy* todavía cuenta como utilizable. *(modelo.esta_vencido)*
- **Las 17 recetas predefinidas piden ingredientes por nombre, no por cantidad.** Las **recetas propias** sí
  traen cantidades y se comparan con la despensa (sumando todas las compras vigentes). Solo se convierten
  kg↔g y L↔ml; si la receta pide «3 unidades» y tienes «500 g» no se puede saber y se da por disponible.
- **Coincidencia de nombres:** ignora mayúsculas, acentos y plurales (`Tomates` = `tomate`, `Limón` = `limones`)
  y acepta nombres más largos (`Leche entera` sirve para `leche`). Falso positivo conocido: `pasta de tomate`
  contaría como `tomate`. *(logica.coincide_ingrediente)*
- **Orden de recetas:** cada ingrediente aprovechado suma 5 puntos si vence en ≤ 3 días, 3 si ≤ 7 días y 1 si no;
  gana el mayor puntaje y se desempata por menos faltantes. Es una heurística: las constantes están al inicio de
  `logica.py`.
- **Varias compras del mismo producto** con distinta fecha son filas separadas, y la receta usa la que vence antes.
- **La fecha de «hoy» es la del reloj del computador.** Si cambia la fecha del sistema, cambian los estados.
- Sal, agua, aceite y especias básicas se asumen disponibles y no aparecen en las recetas.
- **Las reglas existen dos veces** (Python y JavaScript). Para que no se separen, las pruebas de paridad comparan
  ambas con los mismos casos; aun así, un cambio de reglas hay que hacerlo en los dos lados.
- **El APK no se probó en un celular real**: sí se probó la misma pantalla en un Chrome que emula un Pixel 7 y se
  comprobó que el APK compila, tiene el paquete correcto y está firmado. El botón «atrás» y la instalación en un
  celular concreto son lo primero que conviene mirar (grupo L de `CASOS_DE_PRUEBA.md`).
- El APK está firmado con la clave de **depuración**: sirve para instalarlo y mostrarlo, no para publicarlo en Google Play.

## 6. Cómo se verificó

- `python -m unittest discover -s tests` → pruebas de validaciones, lógica, almacenamiento **y de la interfaz real**
  (se crea la ventana y se simula escribir en el formulario, seleccionar, editar y eliminar).
- **Las mismas pruebas de interfaz se ejecutan dos veces**: con la versión original y con la apariencia renovada.
  Si la capa visual cambiara el comportamiento, la segunda tanda fallaría.
- Los escenarios de `CASOS_DE_PRUEBA.md` se ejecutaron con ambas versiones y las salidas fueron idénticas.
- Revisión visual de la pantalla con datos de ejemplo, a zoom normal y al 150 % (columnas sin cortarse), con la
  pantalla vacía y en modo edición. Contraste de colores texto/fondo ≥ 4,5:1 (nivel AA).
- Ejecución del programa empaquetado con PyInstaller para confirmar que abre.
- El workflow de GitHub repite pruebas y empaquetado en Windows y comprueba que el `.exe` abre.
- **Versión Android/web:** 45 pruebas de Node que comparan el JavaScript con el Python (se comprobó que detectan
  errores introducidos a propósito), 17 casos de extremo a extremo en Chrome emulando un Pixel 7 (escribir en los
  campos, tocar botones, recargar, cortar el internet, modo oscuro, botón «atrás») y la compilación del APK en
  GitHub con comprobación de su paquete y su firma.

## 7. Criterios de evaluación del reto y dónde se ve cada uno

| Criterio (peso) | Qué lo respalda en este repositorio |
|---|---|
| **Demostración funcional** (20 %) | El flujo completo (agregar → ordenar → vencidos aparte → receta sugerida → editar → reabrir) está en el guion de la sección 4 y cubierto por pruebas de interfaz. |
| **Resolución del problema** (15 %) | La tabla «Requisito → código → prueba» de la sección 3 cubre cada punto del enunciado de Food Saver. |
| **Experiencia de usuario y acabado** (15 %) | Interfaz renovada: encabezado con resumen, estados con **texto y color** (no solo color), mensajes de error/éxito en una caja visible, botones con jerarquía, buen contraste, zoom alto y ventana adaptada a la pantalla. Los errores comunes de entrada (cantidad inválida, fecha inexistente, campos vacíos, archivo dañado) se explican sin romper la app. |
| **Descomposición de tareas** (15 %) | El código se divide por responsabilidad (modelo, lógica, recetas, almacenamiento, pantalla, apariencia) y la mejora visual se hizo como una capa aparte, sin tocar lo que ya funcionaba. |
| **Gestión del contexto** (15 %) | El documento del reto se tradujo a requisitos concretos (sección 3), límites conocidos (sección 5) y reglas explícitas. |
| **Verificación y depuración** (20 %) | 193 pruebas de Python, 45 de la versión web comparadas con el Python, 17 de extremo a extremo, `CASOS_DE_PRUEBA.md`, comparación entre la versión original y la renovada, y compilación + prueba automática del `.exe` en Windows y del APK en Android. |

> Los tres últimos criterios también evalúan **cómo trabajó el equipo con el agente de IA** (qué pidió, qué revisó,
> qué corrigió). Esta tabla muestra la evidencia que deja el repositorio; la explicación del proceso la tiene que
> dar el equipo con lo que realmente hizo.

> Nota de transparencia para la rúbrica del evento: este código fue generado con un agente de IA (Claude Code)
> a partir del enunciado del reto. Lo que cuenta ante el jurado es que el equipo **entienda, revise y pueda
> modificar** lo generado; por eso el código está comentado en español y esta página resume cada decisión.
