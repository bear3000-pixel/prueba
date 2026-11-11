# Casos de prueba manuales — Food Saver

Sirven para **comprobar la app con sus propias manos** antes de presentarla y, si el jurado pregunta
«¿cómo verificaron que funciona?», para mostrar qué se probó y qué resultado se esperaba.

> Complementan las pruebas automáticas (193 de Python con `python -m unittest discover -s tests`, y 45 + 17 de la versión web en `web/tests/`).
> Los resultados esperados de los grupos **A–E, G1–G4, H, I1–I5, J y K** se obtuvieron ejecutando cada caso contra
> la aplicación real, con la fecha de «hoy» fijada en el 11/11/2026 (los de A–I, con la versión original y con la de
> apariencia renovada: las salidas fueron idénticas). Los grupos **F, G5, G6, I6 e I7** dependen de tu computador
> (archivos de Windows, tamaño y zoom de pantalla, icono) y no se pudieron probar a mano antes de escribirlos: son
> justo lo que conviene mirar tú en Windows.
>
> **Novedad:** la fecha de vencimiento se escribe solo con números y el campo pone las barras (grupo **J**), y
> ahora se pueden crear recetas propias (grupo **K**). Por eso los casos A12, B2 y B3 cambiaron respecto a la
> versión anterior de este documento.

## Cómo usar este documento

1. **Parte de cero:** abre la app y pulsa **Borrar todo** (confirma con *Sí*) antes de cada grupo de casos,
   salvo que el caso diga lo contrario. Los datos se guardan entre una ejecución y otra.
2. **Las fechas dependen del día en que pruebes.** Los casos usan `HOY+N` (dentro de N días) y `HOY-N` (hace N días).
   La tabla de abajo ya trae las fechas calculadas para **HOY = 11/11/2026**: si pruebas otro día, calcula las tuyas
   (por ejemplo, desde el calendario de Windows). Lo que se espera en pantalla (*«Vence en 2 días»*, etc.) es
   igual sin importar el día.
3. Marca la columna **Resultado** con ✔ si pasó o ✘ si no. Si algo falla, anota qué viste: es un error a corregir.

| Notación | Fecha si HOY = 11/11/2026 |
|---|---|
| HOY-10 | 01/11/2026 |
| HOY-1 | 10/11/2026 |
| HOY | 11/11/2026 |
| HOY+1 | 12/11/2026 |
| HOY+2 | 13/11/2026 |
| HOY+3 | 14/11/2026 |
| HOY+4 | 15/11/2026 |
| HOY+5 | 16/11/2026 |
| HOY+9 | 20/11/2026 |
| HOY+10 | 21/11/2026 |
| HOY+15 | 26/11/2026 |
| HOY+30 | 11/12/2026 |
| HOY+200 | 30/05/2027 |

---

## A. Datos inválidos: la app debe rechazarlos

En todos estos casos: pulsa **Agregar** → aparece el mensaje **en rojo**, **no se agrega nada** a las tablas,
el cursor queda en el campo con el problema y **lo que escribiste no se borra**.
Usa Unidad = `L` y, salvo que se indique, Vence = `HOY+1` (12/11/2026).

| ID | Ingrediente | Cantidad | Vence | Mensaje esperado | Resultado |
|---|---|---|---|---|---|
| A1 | Leche | `0` | HOY+1 | La cantidad debe ser mayor que cero. | |
| A2 | Leche | `-3` | HOY+1 | La cantidad debe ser mayor que cero. | |
| A3 | Leche | `abc` | HOY+1 | La cantidad debe ser un número (por ejemplo 2 o 1,5). | |
| A4 | Leche | *(vacío)* | HOY+1 | Escribe la cantidad. | |
| A5 | Leche | `1e3` | HOY+1 | La cantidad debe ser un número (por ejemplo 2 o 1,5). | |
| A6 | Leche | `5000000` | HOY+1 | La cantidad es demasiado grande (máximo 1.000.000). | |
| A7 | Leche | `0,0001` | HOY+1 | La cantidad debe ser mayor que cero. | |
| A8 | *(vacío)* | `1` | HOY+1 | Escribe el nombre del ingrediente. | |
| A9 | `123` | `1` | HOY+1 | El nombre debe contener letras. | |
| A10 | Leche | `1` | *(vacío)* | Escribe la fecha de vencimiento (DD/MM/AAAA). | |
| A11 | Leche | `1` | `31/02/2026` | Fecha no válida. Usa DD/MM/AAAA (por ejemplo 25/12/2026) y verifica que el día exista. *(aparece apenas termines de escribir la fecha, y se repite al pulsar Agregar)* | |
| A12 | Leche | `1` | `mañana` | **El campo no deja escribir letras** (queda vacío). Al pulsar *Agregar*: Escribe la fecha de vencimiento (DD/MM/AAAA). | |
| A13 | Leche | `1` | `12/11/26` | Fecha no válida. Usa DD/MM/AAAA… *(el año debe tener 4 dígitos)* | |
| A14 | Leche | `1` | `25/12/0226` | El año del vencimiento debe estar entre 2000 y 2100. | |

---

## B. Datos válidos: la app debe aceptarlos y normalizarlos

Agrega estos cuatro en orden (Unidad según la tabla).

| ID | Ingrediente | Cantidad | Unidad | Vence | Resultado esperado | Resultado |
|---|---|---|---|---|---|---|
| B1 | `Leche entera` escrito con **2 espacios antes, 3 entre las palabras y 1 después** | `1,5` | L | HOY+2 | Mensaje verde «Leche entera» agregado. Se ve **`Leche entera`** (sin espacios sobrantes) y **`1,5 L`** | |
| B2 | Aceite | `1.5` | L | **pega** (Ctrl+V) `2026-11-20` | Acepta punto decimal. La fecha pegada en formato AAAA-MM-DD se convierte sola: se ve `1,5 L` y `20/11/2026` | |
| B3 | Sal | `2` | kg | `20-11-2026` (escrito con guiones) | Los guiones se cambian por barras. Se ve `20/11/2026` | |
| B4 | Pan | `1` | paquetes | `5/12/2026` | Acepta día/mes sin cero. Se ve **`1 paquete`** (singular) y `05/12/2026` | |

Tras agregar los cuatro, en **Vigentes** el orden debe ser: Leche entera, Aceite, Sal, Pan
(y Aceite antes que Sal por tener igual fecha y ordenarse por nombre).

---

## C. Orden, «por vencer» y vencidos

Parte de cero. Agrega (el orden en que los escribes no importa):

| Ingrediente | Cantidad | Unidad | Vence |
|---|---|---|---|
| Arroz | 1 | kg | HOY+200 |
| Pollo | 500 | g | HOY-1 |
| Leche | 1 | L | HOY+2 |
| Yogur | 2 | unidades | HOY |
| Queso | 200 | g | HOY+3 |
| Pan | 1 | paquetes | HOY+4 |

| ID | Qué mirar | Resultado esperado | Resultado |
|---|---|---|---|
| C1 | Título de la tabla de arriba y orden de filas | **Ingredientes vigentes (5)**. De arriba abajo: Yogur, Leche, Queso, Pan, Arroz (el que vence primero, arriba) | |
| C2 | Columna **Estado** de cada vigente | Yogur: `⚠ Vence hoy` · Leche: `⚠ Vence en 2 días` · Queso: `⚠ Vence en 3 días` · Pan: `Vence en 4 días` · Arroz: `Vence en 200 días` | |
| C3 | Colores (límite de «por vencer») | Yogur, Leche y Queso con **fondo amarillo**. Pan (4 días) y Arroz **sin color** | |
| C4 | Un ingrediente que vence **hoy** | Yogur **sigue en Vigentes** (vence hoy ≠ vencido) | |
| C5 | Tabla de abajo | **Vencidos (1) — no se usan en las recetas**: Pollo, `500 g`, `Vencido hace 1 día`, **fondo rojo** | |
| C6 | Cantidades | Pan se ve como `1 paquete`; Yogur como `2 unidades` | |

---

## D. Recetas

### D1. Demostración principal del reto
Parte de cero. Agrega: **Huevos** 6 unidades HOY+5 · **Queso** 200 g HOY+10 · **Tomates** 4 unidades HOY+2.

| ID | Qué mirar | Resultado esperado | Resultado |
|---|---|---|---|
| D1.1 | Primera receta de la lista | **Omelette de queso y tomate** · Tienes `3 de 3` · Aprovecha `Tomates (en 2 días)` (fila resaltada) | |
| D1.2 | Panel de detalle de esa receta | `✔ Tienes todos los ingredientes: puedes cocinarla ya.` · «Lo que usarías»: Tomates (4 unidades) — vence en 2 días; Huevos (6 unidades) — vence en 5 días; Queso (200 g) — vence en 10 días · y 4 pasos de preparación | |
| D1.3 | Siguientes recetas | En este orden: Ensalada de atún (`1 de 4`), Pasta con salsa de tomate (`1 de 4`), Guiso de lentejas (`1 de 5`) | |
| D1.4 | Casilla **«Solo recetas que puedo cocinar ya»** marcada | Queda **una sola** receta: Omelette de queso y tomate | |
| D1.5 | Desmarcar la casilla | Vuelve la lista completa | |

### D2. Un ingrediente vencido NO se usa en recetas
Parte de cero. Agrega: **Pollo** 500 g HOY-1 · **Arroz** 1 kg HOY+30 · **Zanahorias** 4 unidades HOY+3 · **Cebolla** 3 unidades HOY+10.

| ID | Qué mirar | Resultado esperado | Resultado |
|---|---|---|---|
| D2.1 | Primera receta | **Arroz con pollo y verduras** · Tienes `3 de 4` · Aprovecha `Zanahorias (en 3 días)` | |
| D2.2 | Detalle de esa receta | `Te faltan 1 ingrediente(s).` · «Lo que usarías»: Zanahorias, Cebolla, Arroz (**el pollo NO aparece aquí**) · «Te faltan»: **`Pollo (lo tienes, pero está vencido)`** | |
| D2.3 | Casilla «Solo recetas que puedo cocinar ya» marcada | La lista queda vacía y el panel dice: *Ninguna receta se puede cocinar completa con lo que tienes vigente. Desmarca la casilla para ver recetas con ingredientes faltantes.* | |

### D3. Reconoce nombres escritos de formas distintas
Parte de cero. Agrega: **LIMONES** 3 unidades HOY+9 · **Plátanos** 2 unidades HOY+3 · **tomate** 1 unidades HOY+3 ·
**Leche entera** 1 L HOY+2 · **Jamón** 200 g HOY+9 · **PAN** 1 paquetes HOY+3 · **queso** 100 g HOY+9.

| ID | Qué mirar | Resultado esperado | Resultado |
|---|---|---|---|
| D3.1 | Receta de plátano y leche | **Batido de plátano y leche** · `2 de 2` (Plátanos = «platano»; «Leche entera» sirve para «leche») | |
| D3.2 | Receta de jamón y queso | **Sándwich de jamón y queso** · `3 de 3` (ignora mayúsculas y acento: «PAN», «Jamón») | |
| D3.3 | Receta con limón | **Pollo al limón con papas** aparece con `1 de 4` (LIMONES = «limón») | |
| D3.4 | Receta con tomate | **Omelette de queso y tomate** · `2 de 3` | |

### D4. Varias compras del mismo producto: se usa la que vence primero
Parte de cero. Agrega: **Leche** 1 L HOY+15 · **Leche** 2 L HOY+1 · **Plátano** 2 unidades HOY+9.

| ID | Qué mirar | Resultado esperado | Resultado |
|---|---|---|---|
| D4.1 | Tabla de vigentes | Dos filas de Leche (no se mezclan): primero la de `2 L` (`⚠ Vence mañana`), al final la de `1 L` | |
| D4.2 | Receta **Batido de plátano y leche** | `2 de 2` · Aprovecha `Leche (mañana)` · detalle: **`Leche (2 L) — vence mañana`** (la que vence antes) | |

### D5. Casos sin recetas (mensajes de ayuda)

| ID | Preparación | Resultado esperado | Resultado |
|---|---|---|---|
| D5.1 | Sin ningún ingrediente | Lista de recetas vacía. Panel: *Agrega ingredientes (o pulsa «Cargar ejemplo») para ver recetas sugeridas.* | |
| D5.2 | Solo vencidos: **Plátano** 2 unidades HOY-1 y **Leche** 1 L HOY-10 | Vigentes (0). Vencidos (2): Leche `Vencido hace 10 días`, Plátano `Vencido hace 1 día`. Sin recetas. Panel: *Ninguna receta usa tus ingredientes vigentes. Revisa la lista de vencidos o agrega más ingredientes.* | |

---

## E. Editar y eliminar

Parte de cero. Agrega **Leche** 1 L HOY+2 y **Huevos** 6 unidades HOY+5.

| ID | Acción | Resultado esperado | Resultado |
|---|---|---|---|
| E1 | Doble clic sobre la fila **Leche** (o selecciónala y pulsa **Editar**) | El formulario se llena con `Leche`, `1`, `L`, `13/11/2026`. El título pasa a *Editando «Leche»*, el botón a **Guardar cambios** y aparece **Cancelar edición** | |
| E2 | Cambia Cantidad a `0` y pulsa **Guardar cambios** | Mensaje rojo *La cantidad debe ser mayor que cero.* La leche **sigue con `1 L`** y sigues en modo edición | |
| E3 | Cambia Cantidad a `3` y Vence a HOY-1 (`10/11/2026`) → **Guardar cambios** | Mensaje verde *«Leche» actualizado.* Leche **pasa a Vencidos** (`3 L`, `Vencido hace 1 día`, fondo rojo). **No se duplicó**: hay 1 Leche en total. El formulario vuelve a *Agregar ingrediente* | |
| E4 | Entra a editar otra vez y pulsa **Cancelar edición** | El formulario se vacía y vuelve a *Agregar ingrediente*. No cambió ningún dato | |
| E5 | Selecciona Huevos y pulsa **Eliminar** → responde **No** | No se borra nada | |
| E6 | **Eliminar** otra vez → responde **Sí** | Pregunta: *¿Eliminar «Huevos»?* · Mensaje *«Huevos» eliminado.* · desaparece de la tabla y de las recetas | |
| E7 | **Borrar todo** → **Sí** | Pregunta *¿Borrar el ingrediente guardado?* (o *los N ingredientes guardados*) · Mensaje *Se borraron todos los ingredientes.* · tablas vacías | |

---

## F. Persistencia (los datos sobreviven al cerrar)

| ID | Pasos | Resultado esperado | Resultado |
|---|---|---|---|
| F1 | Agrega 3 ingredientes. Cierra la ventana con la **X**. Abre `FoodSaver.exe` otra vez | Los 3 ingredientes siguen ahí, ordenados y con sus estados | |
| F2 | **Archivo dañado.** Cierra la app. Pulsa `Win + R`, escribe `%APPDATA%\FoodSaver` y Enter. Abre `ingredientes.json` con el Bloc de notas, borra todo y escribe `esto no es json`; guarda. Abre la app | La app **abre igual (no se cae)**, vacía, y muestra el aviso *«El archivo de datos estaba dañado y la app arrancó vacía. Se guardó una copia en: …\ingredientes.corrupto»*. En la carpeta aparece `ingredientes.corrupto` | |
| F3 | **Un dato malo entre datos buenos.** Cierra la app. Con ingredientes guardados, abre `ingredientes.json` y, en **una sola** entrada, cambia el valor de `"cantidad"` por `-5` (deja `"cantidad": -5`); guarda. Abre la app | Abre con aviso *«Se omitieron 1 ingrediente(s) con datos inválidos…»* y **conserva los demás** | |
| F4 | Cierra la app y **borra** `ingredientes.json`. Abre la app | Abre vacía, **sin errores ni avisos** | |

---

## G. Uso del teclado, ratón y ventana

| ID | Acción | Resultado esperado | Resultado |
|---|---|---|---|
| G1 | Llena el formulario y pulsa **Enter** estando en cada campo (nombre, cantidad, unidad, vence) | En los cuatro casos se agrega el ingrediente (equivale a pulsar *Agregar*) | |
| G2 | Selecciona una fila y pulsa la tecla **Supr** | Pregunta *¿Eliminar «…»?* | |
| G3 | Sin ninguna fila seleccionada | Los botones **Editar** y **Eliminar** están **deshabilitados (grises)**; al seleccionar una fila se activan | |
| G4 | Selecciona una fila de **Vigentes** y luego una de **Vencidos** | Solo queda seleccionada la última (no hay dos selecciones a la vez) | |
| G5 | Agranda y reduce la ventana; arrastra el borde hasta el tamaño mínimo | El texto no se corta ni se superpone; las listas y el detalle de receta tienen **barra de desplazamiento** si hace falta | |
| G6 | Si tu pantalla tiene zoom 125 % o 150 % | La ventana se ve nítida (no borrosa) y el texto de las columnas **Estado** no se corta | |

---

## H. Datos de ejemplo (botón «Cargar ejemplo»)

Parte de cero y pulsa **Cargar ejemplo**.

| ID | Qué mirar | Resultado esperado | Resultado |
|---|---|---|---|
| H1 | Mensaje | *Se agregaron 12 ingredientes de ejemplo.* | |
| H2 | Títulos de las tablas | **Ingredientes vigentes (10)** y **Vencidos (2)** | |
| H3 | Vigentes, de arriba abajo | Espinaca, Leche, Pan de molde, Tomates, Huevos, Zanahorias, Queso, Cebolla, Papas, Arroz | |
| H4 | Vencidos | Yogur (hace 3 días) y Pollo (hace 1 día) | |
| H5 | Primeras recetas | 1.ª **Tostadas francesas** `3 de 3` · `Pan de molde (en 2 días)` — 2.ª **Huevos revueltos con espinaca** `3 de 3` · `Espinaca (mañana)` — 3.ª **Omelette de queso y tomate** `3 de 3` · `Tomates (en 3 días)` | |
| H6 | Casilla «Solo recetas que puedo cocinar ya» | Quedan 4: Tostadas francesas, Huevos revueltos con espinaca, Omelette de queso y tomate, Arroz frito con huevo | |
| H7 | Pollo y Yogur (vencidos) | **No aparecen** como ingredientes usados en ninguna receta | |

*(Los resultados de H no dependen del día: los vencimientos de ejemplo se calculan respecto a hoy.)*

---

## I. Apariencia: encabezado, mensajes y versión clásica

El encabezado verde de arriba muestra tres «chips» con el **resumen** de tu despensa. Se actualizan solos.

| ID | Preparación / acción | Resultado esperado | Resultado |
|---|---|---|---|
| I1 | Sin ningún ingrediente (**Borrar todo**) | Chips: `0 vigentes` · `0 por vencer` · `0 vencidos` | |
| I2 | Agrega los 6 ingredientes del **grupo C** | Chips: **`5 vigentes`** (verde) · **`3 por vencer`** (amarillo: Yogur, Leche, Queso) · **`1 vencido`** (rojo: Pollo). Observa el singular «1 vencido» | |
| I3 | Pulsa **Cargar ejemplo** (con la despensa vacía) | Chips: `10 vigentes` · `4 por vencer` · `2 vencidos` | |
| I4 | Edita el Pollo del grupo C y pon una fecha futura (HOY+5) | Los chips cambian **al guardar**, sin tocar nada más: `6 vigentes` · `3 por vencer` · `0 vencidos` | |
| I5 | **Mensajes en caja de color.** Escribe cantidad `0` y pulsa *Agregar*; luego agrega un ingrediente válido | El error sale en una **caja rosada** con letra roja en negrita; el éxito, en una **caja verde clara**. El texto es el mismo de los grupos A y B | |
| I6 | **Versión clásica.** Abre la app con `python main.py --clasico` (desde el código fuente) | Se ve la apariencia original, sin encabezado verde, y **todo lo demás funciona igual** (repite D1 y E3) | |
| I7 | **Icono (solo Windows).** Mira el archivo `FoodSaver.exe` en el Explorador, la barra de título y la barra de tareas | Aparece el icono de la **hoja blanca sobre fondo verde** | |

---

## J. Fecha de vencimiento con barras automáticas

En el campo **Vence**, escribe **solo números**: el programa pone las barras. Sirve tanto al agregar un ingrediente
como al editarlo. Las fechas siguen siendo comprobadas igual que antes (que el día exista, etc.).

| ID | Qué hacer | Resultado esperado | Resultado |
|---|---|---|---|
| J1 | Escribe despacio `02112026` | Al escribir `02` aparece `02/`; al llegar a `0211`, `02/11/`; al final, **`02/11/2026`** | |
| J2 | Escribe `2/11/2026` (con las barras tú mismo) | Queda **`02/11/2026`** (completa el cero del día) | |
| J3 | Con `02/11/` escrito, pulsa **Retroceso** varias veces | Borra de a uno y **las barras no reaparecen** solas: `02/11` → `02/1` → `02/` → `02` | |
| J4 | Escribe `mañana`; luego borra y escribe `1a2b` | `mañana` no deja escribir nada (queda vacío); `1a2b` queda `12/` (solo toma los números) | |
| J5 | Escribe `0211202699` (10 dígitos) | Queda `02/11/2026`: **no pasa de 8 dígitos** | |
| J6 | Escribe `31022026` (31 de febrero) | Queda `31/02/2026` y **al instante** sale en rojo: Fecha no válida. Usa DD/MM/AAAA (por ejemplo 25/12/2026) y verifica que el día exista. | |
| J7 | Borra todo y escribe `28022026` | Queda `28/02/2026` y el aviso rojo **desaparece solo** | |
| J8 | Escribe `01132026` (mes 13) | Aviso rojo de fecha no válida | |
| J9 | Escribe `25120226` (año 0226) | Aviso rojo: El año del vencimiento debe estar entre 2000 y 2100. | |
| J10 | Escribe `021126` (año de 2 dígitos) y pulsa **Agregar** con nombre y cantidad válidos | Queda `02/11/26` y al agregar: Fecha no válida… *(el año necesita 4 dígitos)*. No se agrega nada | |
| J11 | Llena nombre `Leche`, cantidad `1` y escribe `02112026`; pulsa **Agregar** | «Leche» agregado. Aparece con vencimiento `02/11/2026` (en **Vencidos** si esa fecha ya pasó, en Vigentes si no) y el formulario queda vacío | |
| J12 | Selecciona un ingrediente y pulsa **Editar** | La fecha aparece ya con barras (`DD/MM/AAAA`) y puedes cambiar solo un dígito sin que se desordene | |

---

## K. Recetas propias

El panel de recetas tiene dos botones nuevos: **+ Crear mi receta** y **Mis recetas**. Una receta tiene: nombre,
**ingredientes (cada uno con cantidad y unidad)** y **pasos de preparación**. Las recetas propias se marcan con **★**.
Para estos casos usa **Borrar todo** antes de empezar. En el cuadro, el botón principal se llama **Guardar receta**.

### K1. Validaciones al agregar un ingrediente a la receta
Abre **+ Crear mi receta**, escribe `Harina` y una cantidad, y pulsa **Agregar ingrediente**. En todos estos casos el
ingrediente **no se agrega** y sale un aviso rojo.

| ID | Cantidad escrita | Aviso esperado | Resultado |
|---|---|---|---|
| K1.1 | *(vacía)* | Falta la cantidad de «Harina». | |
| K1.2 | `0` | La cantidad debe ser mayor que cero. | |
| K1.3 | `-5` | La cantidad debe ser mayor que cero. | |
| K1.4 | `abc` | La cantidad debe ser un número (por ejemplo 2 o 1,5). | |
| K1.5 | `1e3` | La cantidad debe ser un número (por ejemplo 2 o 1,5). | |
| K1.6 | `5000000` | La cantidad es demasiado grande (máximo 1.000.000). | |
| K1.7 | `0,0001` | La cantidad debe ser mayor que cero. | |
| K1.8 | Nombre vacío y cantidad `5` | Escribe el nombre del ingrediente. | |
| K1.9 | Nombre `123` y cantidad `5` | El nombre debe contener letras. | |
| K1.10 | `Harina` `500` **g** y luego `HARINAS` `2` | La primera se agrega («Harina» agregado a la receta.). La segunda: «HARINAS» ya está en la lista de ingredientes. | |
| K1.11 | `Azúcar` `1,5` **tazas** | Se agrega y en la lista se ve `1,5 tazas` | |

### K2. Validaciones al guardar la receta
| ID | Qué hacer | Aviso esperado (el cuadro **no se cierra**) | Resultado |
|---|---|---|---|
| K2.1 | Pulsa **Guardar receta** sin escribir nada | Escribe el nombre de la receta. | |
| K2.2 | Solo el nombre `Mi receta` | Agrega al menos un ingrediente a la receta. | |
| K2.3 | Nombre + 1 ingrediente, sin pasos | Escribe al menos un paso de preparación. | |
| K2.4 | Escribe `Azúcar` y `5` arriba **pero no pulsas** *Agregar ingrediente*, y guardas | Tienes un ingrediente escrito que no has agregado. Pulsa «Agregar ingrediente» o borra lo escrito. *(así no se pierde un dato sin avisar)* | |
| K2.5 | Nombre `omelette de queso y tomate` (ya existe una predefinida) | Ya existe una receta llamada «omelette de queso y tomate». Elige otro nombre. | |
| K2.6 | Nombre `123` | El nombre de la receta debe contener letras. | |
| K2.7 | Nombre de 61 letras | El nombre de la receta es demasiado largo (máximo 60 caracteres). | |
| K2.8 | Pasos `123` y `456` (solo números) | El paso 1 debe contener texto. | |

### K3. Crear una receta que se usa
Agrega a la despensa **Harina** 1 kg (HOY+2) y **Agua** 1 L (HOY+30). Pulsa **+ Crear mi receta**:
nombre `Pan casero`; ingredientes `Harina` `500` g y `Agua` `300` ml; en *Preparación* escribe tres líneas:
`1. Mezclar todo`, `2) Amasar`, `- Hornear 30 minutos`; **Guardar receta**.

| ID | Qué mirar | Resultado esperado | Resultado |
|---|---|---|---|
| K3.1 | Mensaje bajo el formulario | Receta «Pan casero» guardada. Ya aparece en las recetas sugeridas. | |
| K3.2 | Primera fila de recetas | **`★ Pan casero`** · Tienes `2 de 2` · Aprovecha `Harina (en 2 días)` | |
| K3.3 | Panel de detalle | `★ Pan casero` · *Receta creada por ti* · ✔ Tienes todos los ingredientes · «Lo que usarías»: **Harina (1 kg) — vence en 2 días — la receta pide 500 g** y **Agua (1 L) — vence en 30 días — la receta pide 300 ml** | |
| K3.4 | Pasos | Se ven numerados `1. Mezclar todo`, `2. Amasar`, `3. Hornear 30 minutos` (**sin números repetidos**: se quitó la numeración que escribiste) | |
| K3.5 | Unidades distintas | Se compararon bien aunque la despensa esté en **kg** y **L** y la receta en **g** y **ml** | |

### K4. La receta compara cantidades con lo que tienes
| ID | Despensa | Resultado esperado | Resultado |
|---|---|---|---|
| K4.1 | **Harina** `300` g (HOY+4) y **Agua** 1 L (HOY+4); receta Pan casero (500 g y 300 ml) | Fila `★ Pan casero` · `1 de 2`. Detalle: *Te faltan 1 ingrediente(s).* · «Lo tienes, pero en poca cantidad»: **Harina: pide 500 g, tienes 300 g (te faltan 200 g)**. No dice «puedes cocinarla ya» | |
| K4.2 | La misma, con la casilla **«Solo recetas que puedo cocinar ya»** marcada | La receta **desaparece** (no se puede cocinar completa) | |
| K4.3 | **Harina** 1 kg **vencida** (HOY-2) y **Agua** 1 L vigente | Detalle: «Te faltan»: **Harina — pide 500 g (lo tienes, pero está vencido)**. La harina vencida no se usa | |
| K4.4 | Solo **Tomate** `500` g y una receta que pide **Tomate** `3` unidades | Se da por disponible (`1 de 1`): **no se pueden comparar «unidades» con «g»**, así que no bloquea | |
| K4.5 | Sin ningún ingrediente en la despensa, crea una receta | Mensaje: Receta «…» guardada. Aparecerá en las sugerencias cuando tengas alguno de sus ingredientes (vigente) en la despensa. | |

### K5. Editar el cuadro mientras armas la receta
| ID | Acción | Resultado esperado | Resultado |
|---|---|---|---|
| K5.1 | En la lista de ingredientes de la receta, **doble clic** sobre `Harina` | Sus datos pasan a las casillas de arriba, el botón dice **Guardar cambio** y el aviso: Editando «Harina». Cambia lo que necesites y pulsa «Guardar cambio». | |
| K5.2 | Pon cantidad `0` y pulsa **Guardar cambio** | Aviso rojo; la harina **conserva** su cantidad anterior | |
| K5.3 | Pon cantidad `750` y pulsa **Guardar cambio** | «Harina» actualizado. La lista muestra `750 g` y el botón vuelve a *Agregar ingrediente* | |
| K5.4 | Selecciona un ingrediente y pulsa **Quitar seleccionado** | «…» quitado de la receta. Desaparece de la lista | |
| K5.5 | Pulsa **Quitar seleccionado** sin elegir ninguno | Selecciona un ingrediente de la lista para quitarlo. | |
| K5.6 | Con la receta a medias, pulsa **Cancelar**, la tecla **Esc** o la **X** de la ventana | Pregunta: *Tienes cambios sin guardar en esta receta. ¿Quieres cerrar y perderlos?* Con **No** sigues editando; con **Sí** se cierra y **no se guarda nada** | |
| K5.7 | Abre el cuadro y ciérralo sin escribir nada (o abre una receta para editar y no cambies nada) | Se cierra **sin preguntar** | |

### K6. Administrar «Mis recetas»
| ID | Acción | Resultado esperado | Resultado |
|---|---|---|---|
| K6.1 | Pulsa **Mis recetas** sin haber creado ninguna | Lista vacía y el texto: Todavía no has creado ninguna receta. Pulsa «+ Nueva receta» para empezar. Los botones Editar y Eliminar están **grises** | |
| K6.2 | Con `Pan casero` creada | Una fila: `Pan casero` · Ingredientes `2` · Pasos `3` | |
| K6.3 | Con la lista abierta, crea otra receta desde **+ Crear mi receta** | La lista **se actualiza sola** con la nueva | |
| K6.4 | Selecciona una receta y pulsa **Editar** (o doble clic) | Se abre el cuadro **con todo lleno** (nombre, ingredientes con cantidad y pasos). Cambia el nombre y guarda: Receta «…» actualizada. **No se duplica** | |
| K6.5 | Edita una receta y pon el nombre de **otra** que ya tienes | Ya existe una receta llamada «…». Elige otro nombre. *(dejar su propio nombre sí está permitido)* | |
| K6.6 | Selecciona una receta, **Eliminar** y responde **No** | No se borra nada | |
| K6.7 | **Eliminar** otra vez y responde **Sí** | Pregunta: ¿Eliminar tu receta «…»? · Mensaje: Receta «…» eliminada. · desaparece de la lista y de las sugerencias | |

### K7. Las recetas propias se conservan
| ID | Pasos | Resultado esperado | Resultado |
|---|---|---|---|
| K7.1 | Crea una receta, cierra la app con la **X** y ábrela otra vez | La receta sigue en **Mis recetas** y vuelve a aparecer (con ★) si tienes ingredientes | |
| K7.2 | **Archivo dañado.** Cierra la app, abre `%APPDATA%\FoodSaver\recetas_propias.json` con el Bloc de notas, escribe `esto no es json` y guarda; abre la app | La app **abre igual**, con tus ingredientes, y avisa: *El archivo de tus recetas estaba dañado y se empezó con la lista vacía.* + la ruta de la copia `recetas_propias.corrupto` | |
| K7.3 | Las 17 recetas de siempre | Siguen funcionando igual (las de la demo del grupo D no cambian) | |

---

## L. Versión Android (APK) y web

Estos casos se hacen **en el celular**. Los mensajes y resultados son los mismos de los grupos A–K (la pantalla
cambia, las reglas no): puedes repetir cualquier caso de esos grupos en la app de Android y debe dar lo mismo.
Lo que sigue son los casos propios del celular. **No pude probarlos en un celular real**; lo que sí se probó fue la
misma pantalla en un Chrome emulando un Pixel 7 (`web/tests/e2e/movil.e2e.cjs`) y que el APK compila y está firmado.

| ID | Qué hacer | Resultado esperado | Resultado |
|---|---|---|---|
| L1 | Descarga `FoodSaver.apk` (ver README, sección 2b) y ábrelo desde el administrador de archivos | Android pide permiso para instalar desde esa fuente. Puede salir un aviso de **Play Protect**: *Instalar de todos modos*. Termina con «Aplicación instalada» | |
| L2 | Abre la app | Icono de una **hoja blanca sobre fondo verde**, nombre *Food Saver*. Se ve el encabezado verde con los tres contadores y las pestañas **Despensa / Recetas** | |
| L3 | Toca el campo **Vence** | Aparece el **teclado numérico**. Escribe `02112026`: queda `02/11/2026` sin que tengas que poner barras | |
| L4 | Toca **Cantidad** | Aparece el teclado con punto decimal. `1,5` y `1.5` se aceptan | |
| L5 | Con el campo de nombre, pulsa **Siguiente** del teclado | Pasa a Cantidad, y de ahí a Vence (no envía el formulario a medias) | |
| L6 | Pulsa **Cargar ejemplo** y ve a **Recetas** | Contadores `10 vigentes · 4 por vencer · 2 vencidos`. La primera receta es *Tostadas francesas* y viene **abierta**, con su detalle y pasos | |
| L7 | Toca el título de una receta | Se abre y se cierra su detalle (una a la vez no es obligatorio) | |
| L8 | **+ Crear mi receta** | Se abre a **pantalla completa**. Con el teclado abierto puedes llegar a *Agregar ingrediente* y a *Guardar receta* (la pantalla se desplaza) | |
| L9 | Escribe un nombre de receta y toca el botón **«atrás»** de Android (o el gesto) | Pregunta *Tienes cambios sin guardar en esta receta…*. Con **atrás** otra vez (o *No*) sigues en la receta **sin perder lo escrito**. Con *Sí* se cierra | |
| L10 | Con **Mis recetas** abierto, botón **atrás** | Se cierra «Mis recetas» (no sale de la app) | |
| L11 | Estando en la pestaña **Recetas**, botón **atrás** | Vuelve a **Despensa**. Un **atrás** más, sin nada abierto, **sale** de la app | |
| L12 | Agrega un ingrediente, cierra la app del todo (sácala de las recientes) y ábrela | El ingrediente **sigue ahí** | |
| L13 | Activa el **modo avión** y usa la app (agrega, edita, crea una receta) | Todo funciona igual; no necesita internet | |
| L14 | Gira el celular (horizontal) | Nada se corta ni se sale de la pantalla; no hay desplazamiento lateral | |
| L15 | Cambia el celular a **modo oscuro** | La app se ve oscura, con texto legible (contraste suficiente) | |
| L16 | En Ajustes del celular, pon el **tamaño de letra** al máximo | El texto crece y los botones siguen visibles y tocables; nada queda tapado | |
| L17 | Usa un nombre con tilde o eñe (`Piña`, `Limón`) y una receta que pida `limon` | Se reconoce igual que en el escritorio (tildes y plurales ignorados) | |
| L18 | Mira la información de la app en Ajustes | Paquete `com.foodsaver.app`, nombre *Food Saver*. Ocupa unos 4 MB | |

---

## Lista rápida antes de presentar (5 minutos)

Hazlo en **el computador de la presentación**, con el `.exe` final:

- [ ] El `.exe` abre con doble clic (y si sale SmartScreen, ya sabes qué pulsar).
- [ ] **Borrar todo**, y luego el flujo de **D1** completo (agregar 3 ingredientes → ver Omelette sugerida).
- [ ] **C5 / D2**: un vencido va aparte y no aparece en recetas.
- [ ] **A1 y A3**: cantidad `0` y `abc` se rechazan con mensaje.
- [ ] **E3**: editar un ingrediente.
- [ ] **F1**: cerrar y reabrir conserva los datos.
- [ ] Deja la app lista para la demo: **Borrar todo** (o **Cargar ejemplo** si vas a usar el atajo).
