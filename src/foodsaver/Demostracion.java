package foodsaver;

import java.time.Clock;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;

/**
 * Demostración automática. Usa una despensa propia y un reloj FIJO (siempre es el
 * 2025-06-10), así que el resultado es siempre el mismo, sin importar el día real,
 * y no toca la despensa que el usuario esté armando en el menú.
 */
public final class Demostracion {

    private static final Clock RELOJ_DEMO = Clock.fixed(Instant.parse("2025-06-10T12:00:00Z"), ZoneOffset.UTC);

    private Demostracion() {
        // Clase de utilidades: no se instancia.
    }

    public static void ejecutar() {
        Despensa despensa = new Despensa(RELOJ_DEMO);
        SugeridorRecetas sugeridor = new SugeridorRecetas(despensa, CatalogoRecetas.cargar());
        LocalDate hoy = despensa.hoy();

        titulo("FOOD SAVER - DEMOSTRACIÓN");
        System.out.println("Fecha simulada de hoy: " + hoy
                + " (próximo a vencer = " + Ingrediente.DIAS_PROXIMO_A_VENCER + " días o menos)");

        // ---------- Paso 1 ----------
        titulo("PASO 1: Registrar ingredientes");
        intentarAgregar(despensa, "Leche", "1", "l", dia(hoy, -5));        // ya vencida
        intentarAgregar(despensa, "Espinaca", "200", "g", dia(hoy, 1));    // próxima a vencer
        intentarAgregar(despensa, "Tomate", "500", "g", dia(hoy, 2));      // próximo a vencer
        intentarAgregar(despensa, "Huevo", "4", "unidad", dia(hoy, 15));
        intentarAgregar(despensa, "Huevo", "2", "unidad", dia(hoy, 15));   // misma fecha: se suma al anterior
        intentarAgregar(despensa, "Arroz", "1", "kg", dia(hoy, 200));
        intentarAgregar(despensa, "Cebolla", "3", "unidad", dia(hoy, 20));
        intentarAgregar(despensa, "Queso", "150", "g", dia(hoy, 12));
        intentarAgregar(despensa, "Pasta", "500", "g", dia(hoy, 150));
        intentarAgregar(despensa, "Aceite", "500", "ml", dia(hoy, 120));

        // ---------- Paso 2 ----------
        titulo("PASO 2: Despensa ordenada por vencimiento, con los vencidos aparte");
        Reportes.imprimirDespensa(despensa);

        // ---------- Paso 3 ----------
        titulo("PASO 3: Recetas sugeridas (la leche vencida queda excluida)");
        List<Sugerencia> sugerencias = sugeridor.sugerirRecetas();
        Reportes.imprimirSugerencias(sugerencias);
        if (!sugerencias.isEmpty()) {
            Sugerencia mejor = sugerencias.get(0);
            System.out.println();
            System.out.println("==> Recomendada: " + mejor.receta().getNombre());
            for (Sugerencia.Aprovechamiento a : mejor.aprovechados()) {
                System.out.println("    Aprovecha: " + Reportes.describirAprovechamiento(a));
            }
        }

        // ---------- Paso 4 ----------
        titulo("PASO 4: Ingredientes faltantes");
        Receta arrozConLeche = sugeridor.getRecetas().stream()
                .filter(r -> r.getNombre().equals("Arroz con leche"))
                .findFirst()
                .orElseThrow();
        System.out.println("Una receta que no se puede preparar completa "
                + "(la leche de la despensa está vencida, por eso cuenta como faltante):");
        Reportes.imprimirFaltantes(arrozConLeche, sugeridor.calcularFaltantes(arrozConLeche));
        System.out.println();
        System.out.println("Recetas casi completas (les faltan hasta "
                + SugeridorRecetas.MAX_FALTANTES_CASI_COMPLETA + " ingredientes):");
        Map<Receta, List<Faltante>> casiCompletas = sugeridor.recetasCasiCompletas();
        Reportes.imprimirCasiCompletas(casiCompletas);

        // ---------- Paso 5 ----------
        titulo("PASO 5: Entradas inválidas (el programa no se cae)");
        intentarAgregar(despensa, "Harina", "-5", "g", dia(hoy, 30));
        intentarAgregar(despensa, "Harina", "0", "g", dia(hoy, 30));
        intentarAgregar(despensa, "Harina", "mucha", "g", dia(hoy, 30));
        intentarAgregar(despensa, "   ", "100", "g", dia(hoy, 30));
        intentarAgregar(despensa, "Harina", "100", "g", "30/06/2025");
        System.out.println();
        System.out.println("Fin de la demostración.");
    }

    /** Intenta agregar usando textos crudos, igual que el menú, e informa el resultado. */
    private static void intentarAgregar(Despensa despensa, String nombre, String cantidad,
                                        String unidad, String fecha) {
        try {
            Ingrediente ingrediente = Ingrediente.desdeTexto(nombre, cantidad, unidad, fecha);
            boolean sumado = despensa.agregar(ingrediente);
            System.out.println("  [OK] " + (sumado ? "Sumado al lote existente: " : "Agregado: ") + ingrediente);
        } catch (DatoInvalidoException e) {
            System.out.println("  [RECHAZADO] nombre='" + nombre.trim() + "', cantidad='" + cantidad
                    + "', fecha='" + fecha + "' -> " + e.getMessage());
        }
    }

    /** Fecha relativa a "hoy" en formato yyyy-MM-dd. */
    private static String dia(LocalDate hoy, int diasDespues) {
        return hoy.plusDays(diasDespues).toString();
    }

    private static void titulo(String texto) {
        System.out.println();
        System.out.println("=".repeat(70));
        System.out.println(texto);
        System.out.println("=".repeat(70));
    }
}
