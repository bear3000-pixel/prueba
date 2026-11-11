package foodsaver;

import java.time.LocalDate;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.Scanner;

/** Menú interactivo de consola. Uso: "java foodsaver.Main" o "java foodsaver.Main --demo". */
public class Main {

    private final Scanner entrada = new Scanner(System.in);
    private final Despensa despensa = new Despensa();
    private final SugeridorRecetas sugeridor = new SugeridorRecetas(despensa, CatalogoRecetas.cargar());

    public static void main(String[] args) {
        if (args.length > 0 && args[0].equals("--demo")) {
            Demostracion.ejecutar(); // modo no interactivo
            return;
        }
        new Main().iniciar();
    }

    /** Ciclo principal: muestra el menú hasta que el usuario elige salir. */
    private void iniciar() {
        boolean salir = false;
        while (!salir) {
            mostrarMenu();
            try {
                salir = procesarOpcion(leer("Elija una opción: "));
            } catch (DatoInvalidoException e) {
                System.out.println("ERROR: " + e.getMessage());
            } catch (NoSuchElementException e) {
                // La entrada se cerró (Ctrl+D / fin de archivo): salir con elegancia.
                System.out.println();
                System.out.println("Entrada finalizada. ¡Hasta pronto!");
                salir = true;
            }
        }
    }

    private void mostrarMenu() {
        System.out.println();
        System.out.println("========== FOOD SAVER ==========");
        System.out.println("Hoy es " + despensa.hoy());
        System.out.println("1. Agregar ingrediente");
        System.out.println("2. Actualizar ingrediente");
        System.out.println("3. Listar ingredientes (por vencimiento)");
        System.out.println("4. Sugerir recetas");
        System.out.println("5. Ver ingredientes faltantes");
        System.out.println("6. Ejecutar demostración");
        System.out.println("0. Salir");
    }

    /** @return true si el usuario pidió salir */
    private boolean procesarOpcion(String opcion) {
        switch (opcion.trim()) {
            case "1" -> agregarIngrediente();
            case "2" -> actualizarIngrediente();
            case "3" -> Reportes.imprimirDespensa(despensa);
            case "4" -> sugerirRecetas();
            case "5" -> verFaltantes();
            case "6" -> Demostracion.ejecutar();
            case "0" -> {
                System.out.println("¡Hasta pronto!");
                return true;
            }
            default -> throw new DatoInvalidoException(
                    "Opción no válida: '" + opcion.trim() + "'. Elija un número del menú.");
        }
        return false;
    }

    // ---------------------------------------------------------------- opciones del menú

    private void agregarIngrediente() {
        String nombre = leer("Nombre: ");
        String cantidad = leer("Cantidad (ejemplo 2.5): ");
        String unidad = leer("Unidad (" + Unidad.valoresValidos() + "): ");
        String fecha = leer("Fecha de vencimiento (yyyy-MM-dd): ");

        // Si algún dato es inválido, desdeTexto lanza DatoInvalidoException y el ciclo
        // principal muestra el mensaje; nada se guarda.
        Ingrediente ingrediente = Ingrediente.desdeTexto(nombre, cantidad, unidad, fecha);
        boolean sumado = despensa.agregar(ingrediente);
        System.out.println(sumado
                ? "Ya existía con esa fecha de vencimiento: se sumó la cantidad."
                : "Ingrediente agregado.");
        if (ingrediente.estaVencido(despensa.hoy())) {
            System.out.println("Aviso: este ingrediente ya está vencido; no se usará en las sugerencias.");
        }
    }

    private void actualizarIngrediente() {
        List<Ingrediente> lista = despensa.listarPorVencimiento();
        if (lista.isEmpty()) {
            System.out.println("La despensa está vacía: no hay nada que actualizar.");
            return;
        }
        Reportes.imprimirNumerados(lista, despensa.hoy());
        Ingrediente elegido = lista.get(pedirNumero("Número del ingrediente a actualizar: ", lista.size()) - 1);

        String cantidadTexto = leer("Nueva cantidad (Enter para dejarla igual): ");
        String fechaTexto = leer("Nueva fecha yyyy-MM-dd (Enter para dejarla igual): ");
        Double nuevaCantidad = cantidadTexto.isBlank() ? null : Validaciones.cantidad(cantidadTexto);
        LocalDate nuevaFecha = fechaTexto.isBlank() ? null : Validaciones.fecha(fechaTexto);

        boolean fusionado = despensa.actualizar(elegido, nuevaCantidad, nuevaFecha);
        System.out.println(fusionado
                ? "Actualizado y fusionado con otro lote del mismo nombre y fecha."
                : "Ingrediente actualizado.");
    }

    private void sugerirRecetas() {
        List<Sugerencia> sugerencias = sugeridor.sugerirRecetas();
        if (sugerencias.isEmpty()) {
            System.out.println("Con los ingredientes vigentes no se puede preparar ninguna receta completa.");
            System.out.println("Pruebe la opción 5 para ver qué le falta a cada receta.");
            return;
        }
        System.out.println("Recetas que puede preparar (las que rescatan ingredientes próximos a vencer van primero):");
        Reportes.imprimirSugerencias(sugerencias);
    }

    private void verFaltantes() {
        System.out.println("1. Faltantes de una receta");
        System.out.println("2. Recetas casi completas (les faltan hasta "
                + SugeridorRecetas.MAX_FALTANTES_CASI_COMPLETA + " ingredientes)");
        switch (leer("Elija: ").trim()) {
            case "1" -> {
                List<Receta> recetas = sugeridor.getRecetas();
                for (int i = 0; i < recetas.size(); i++) {
                    System.out.printf("  %d. %s%n", i + 1, recetas.get(i).getNombre());
                }
                Receta receta = recetas.get(pedirNumero("Número de la receta: ", recetas.size()) - 1);
                Reportes.imprimirFaltantes(receta, sugeridor.calcularFaltantes(receta));
            }
            case "2" -> Reportes.imprimirCasiCompletas(sugeridor.recetasCasiCompletas());
            default -> throw new DatoInvalidoException("Opción no válida: elija 1 o 2.");
        }
    }

    // ---------------------------------------------------------------- lectura de entrada

    private String leer(String mensaje) {
        System.out.print(mensaje);
        return entrada.nextLine();
    }

    /** Pide un número entero entre 1 y maximo; lanza DatoInvalidoException si no lo es. */
    private int pedirNumero(String mensaje, int maximo) {
        String texto = leer(mensaje).trim();
        try {
            int numero = Integer.parseInt(texto);
            if (numero >= 1 && numero <= maximo) {
                return numero;
            }
        } catch (NumberFormatException e) {
            // No era un entero: se informa más abajo con el mismo mensaje.
        }
        throw new DatoInvalidoException("Debe escribir un número entre 1 y " + maximo + ".");
    }
}
