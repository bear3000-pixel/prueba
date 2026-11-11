# Casos de prueba manuales — Food Saver

Sirven para **comprobar la app con sus propias manos** antes de presentarla y, si el jurado pregunta
«¿cómo verificaron que funciona?», para mostrar qué se probó y qué resultado se esperaba.

> Complementan las 54 pruebas automáticas (`python -m unittest discover -s tests`).
> Los resultados esperados de los grupos **A–E, G1–G4 y H** se obtuvieron ejecutando cada caso contra la
> aplicación real, con la fecha de «hoy» fijada en el 11/11/2026. Los grupos **F, G5 y G6** dependen de tu
> computador (archivos de Windows, tamaño y zoom de pantalla) y no se pudieron probar a mano antes de escribirlos:
> son justo lo que conviene mirar tú en Windows.

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
| A11 | Leche | `1` | `31/02/2026` | Fecha no válida. Usa DD/MM/AAAA (por ejemplo 25/12/2026) y verifica que el día exista. | |
| A12 | Leche | `1` | `mañana` | Fecha no válida. Usa DD/MM/AAAA (por ejemplo 25/12/2026) y verifica que el día exista. | |
| A13 | Leche | `1` | `12/11/26` | Fecha no válida. Usa DD/MM/AAAA… *(el año debe tener 4 dígitos)* | |
| A14 | Leche | `1` | `25/12/0226` | El año del vencimiento debe estar entre 2000 y 2100. | |

---

## B. Datos válidos: la app debe aceptarlos y normalizarlos

Agrega estos cuatro en orden (Unidad según la tabla).

| ID | Ingrediente | Cantidad | Unidad | Vence | Resultado esperado | Resultado |
|---|---|---|---|---|---|---|
| B1 | `Leche entera` escrito con **2 espacios antes, 3 entre las palabras y 1 después** | `1,5` | L | HOY+2 | Mensaje verde «Leche entera» agregado. Se ve **`Leche entera`** (sin espacios sobrantes) y **`1,5 L`** | |
| B2 | Aceite | `1.5` | L | `2026-11-20` | Acepta punto decimal y fecha AAAA-MM-DD. Se ve `1,5 L` y `20/11/2026` | |
| B3 | Sal | `2` | kg | `20-11-2026` | Acepta fecha DD-MM-AAAA. Se ve `20/11/2026` | |
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
| D1.4 | Casilla **«Mostrar solo recetas que puedo cocinar ya»** marcada | Queda **una sola** receta: Omelette de queso y tomate | |
| D1.5 | Desmarcar la casilla | Vuelve la lista completa | |

### D2. Un ingrediente vencido NO se usa en recetas
Parte de cero. Agrega: **Pollo** 500 g HOY-1 · **Arroz** 1 kg HOY+30 · **Zanahorias** 4 unidades HOY+3 · **Cebolla** 3 unidades HOY+10.

| ID | Qué mirar | Resultado esperado | Resultado |
|---|---|---|---|
| D2.1 | Primera receta | **Arroz con pollo y verduras** · Tienes `3 de 4` · Aprovecha `Zanahorias (en 3 días)` | |
| D2.2 | Detalle de esa receta | `Te faltan 1 ingrediente(s).` · «Lo que usarías»: Zanahorias, Cebolla, Arroz (**el pollo NO aparece aquí**) · «Te faltan»: **`Pollo (lo tienes, pero está vencido)`** | |
| D2.3 | Casilla «solo recetas que puedo cocinar ya» marcada | La lista queda vacía y el panel dice: *Ninguna receta se puede cocinar completa con lo que tienes vigente. Desmarca la casilla para ver recetas con ingredientes faltantes.* | |

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
| H6 | Casilla «solo recetas que puedo cocinar ya» | Quedan 4: Tostadas francesas, Huevos revueltos con espinaca, Omelette de queso y tomate, Arroz frito con huevo | |
| H7 | Pollo y Yogur (vencidos) | **No aparecen** como ingredientes usados en ninguna receta | |

*(Los resultados de H no dependen del día: los vencimientos de ejemplo se calculan respecto a hoy.)*

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
