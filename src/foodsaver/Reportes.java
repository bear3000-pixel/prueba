package foodsaver;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/**
 * Todo lo que se imprime en consola vive aquí, separado de la lógica de negocio.
 * El menú (Main) y la demostración usan los mismos reportes.
 */
public final class Reportes {

    private Reportes() {
        // Clase de utilidades: no se instancia.
    }

    /** Despensa en dos secciones: vigentes por vencimiento y vencidos aparte. */
    public static void imprimirDespensa(Despensa despensa) {
        LocalDate hoy = despensa.hoy();
        List<Ingrediente> vigentes = despensa.listarVigentes();
        List<Ingrediente> vencidos = despensa.listarVencidos();

        System.out.println("--- INGREDIENTES VIGENTES (del que vence primero al que vence último) ---");
        if (vigentes.isEmpty()) {
            System.out.println("  (no hay ingredientes vigentes)");
        }
        for (Ingrediente ingrediente : vigentes) {
            System.out.println("  " + linea(ingrediente, hoy));
        }

        System.out.println();
        System.out.println("--- INGREDIENTES VENCIDOS (no se usan en las sugerencias de recetas) ---");
        if (vencidos.isEmpty()) {
            System.out.println("  (no hay ingredientes vencidos)");
        }
        for (Ingrediente ingrediente : vencidos) {
            System.out.println("  " + linea(ingrediente, hoy));
        }
    }

    /** Lista numerada desde 1, para que el usuario elija un ingrediente por su número. */
    public static void imprimirNumerados(List<Ingrediente> lista, LocalDate hoy) {
        for (int i = 0; i < lista.size(); i++) {
            System.out.printf("  %2d. %s%n", i + 1, linea(lista.get(i), hoy));
        }
    }

    public static void imprimirSugerencias(List<Sugerencia> sugerencias) {
        int posicion = 1;
        for (Sugerencia sugerencia : sugerencias) {
            Receta receta = sugerencia.receta();
            System.out.printf("%d. %s  (puntaje de urgencia: %d)%n",
                    posicion++, receta.getNombre(), sugerencia.puntaje());
            System.out.println("   Ingredientes: " + receta.describirIngredientes());
            if (sugerencia.aprovechados().isEmpty()) {
                System.out.println("   Aprovecha: ningún ingrediente próximo a vencer");
            }
            for (Sugerencia.Aprovechamiento a : sugerencia.aprovechados()) {
                System.out.println("   Aprovecha: " + describirAprovechamiento(a));
            }
            System.out.println("   Preparación: " + receta.getInstrucciones());
        }
    }

    public static void imprimirFaltantes(Receta receta, List<Faltante> faltantes) {
        if (faltantes.isEmpty()) {
            System.out.println(receta.getNombre() + ": tiene todo lo necesario, ya se puede preparar.");
            return;
        }
        System.out.println(receta.getNombre() + " - le falta:");
        for (Faltante faltante : faltantes) {
            System.out.println("   - " + faltante.describir());
        }
    }

    public static void imprimirCasiCompletas(Map<Receta, List<Faltante>> recetas) {
        if (recetas.isEmpty()) {
            System.out.println("No hay recetas casi completas (a ninguna le faltan solo 1 o "
                    + SugeridorRecetas.MAX_FALTANTES_CASI_COMPLETA + " ingredientes).");
            return;
        }
        recetas.forEach(Reportes::imprimirFaltantes);
    }

    /** "100 g de Espinaca (vence mañana)". */
    public static String describirAprovechamiento(Sugerencia.Aprovechamiento a) {
        return a.unidad().formatear(a.cantidadUsada()) + " de " + a.ingrediente()
                + " (" + describirDias(a.diasRestantes()) + ")";
    }

    private static String linea(Ingrediente ingrediente, LocalDate hoy) {
        String etiqueta = "";
        if (ingrediente.estaVencido(hoy)) {
            etiqueta = "[VENCIDO]";
        } else if (ingrediente.estaProximoAVencer(hoy)) {
            etiqueta = "[PRÓXIMO A VENCER]";
        }
        return String.format("%-14s %-14s %s  %-21s %s",
                ingrediente.getNombre(),
                ingrediente.getUnidad().formatear(ingrediente.getCantidad()),
                ingrediente.getFechaVencimiento(),
                describirDias(ingrediente.diasParaVencer(hoy)),
                etiqueta).stripTrailing();
    }

    private static String describirDias(long dias) {
        if (dias < -1) {
            return "venció hace " + (-dias) + " días";
        }
        if (dias == -1) {
            return "venció ayer";
        }
        if (dias == 0) {
            return "vence hoy";
        }
        if (dias == 1) {
            return "vence mañana";
        }
        return "vence en " + dias + " días";
    }
}
