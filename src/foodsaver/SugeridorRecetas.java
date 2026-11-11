package foodsaver;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Lógica de sugerencias: decide qué recetas se pueden preparar, cuáles conviene cocinar
 * primero (las que rescatan ingredientes próximos a vencer) y qué le falta a las demás.
 */
public class SugeridorRecetas {

    /** Una receta "casi completa" es la que tiene como máximo este número de ingredientes faltantes. */
    public static final int MAX_FALTANTES_CASI_COMPLETA = 2;

    private final Despensa despensa;
    private final List<Receta> recetas;

    public SugeridorRecetas(Despensa despensa, List<Receta> recetas) {
        this.despensa = despensa;
        this.recetas = List.copyOf(recetas);
    }

    public List<Receta> getRecetas() {
        return recetas;
    }

    /**
     * Recetas que se pueden preparar completas, de la más urgente a la menos urgente.
     * Orden: 1) mayor puntaje de urgencia, 2) nombre de la receta.
     */
    public List<Sugerencia> sugerirRecetas() {
        return recetas.stream()
                .map(this::evaluar)
                .filter(e -> e.faltantes().isEmpty())
                .map(e -> new Sugerencia(e.receta(), e.aprovechados()))
                .sorted(Comparator.comparingInt(Sugerencia::puntaje).reversed()
                        .thenComparing(s -> s.receta().getNombre()))
                .toList();
    }

    /** Ingredientes (y cantidades) que faltan para preparar una receta; lista vacía si se puede preparar. */
    public List<Faltante> calcularFaltantes(Receta receta) {
        return evaluar(receta).faltantes();
    }

    /**
     * Recetas a las que les faltan entre 1 y MAX_FALTANTES_CASI_COMPLETA ingredientes, con lo que falta.
     * Primero las que están más cerca de completarse.
     */
    public Map<Receta, List<Faltante>> recetasCasiCompletas() {
        Map<Receta, List<Faltante>> resultado = new LinkedHashMap<>();
        recetas.stream()
                .map(this::evaluar)
                .filter(e -> !e.faltantes().isEmpty() && e.faltantes().size() <= MAX_FALTANTES_CASI_COMPLETA)
                .sorted(Comparator.comparingInt((Evaluacion e) -> e.faltantes().size())
                        .thenComparing(e -> e.receta().getNombre()))
                .forEach(e -> resultado.put(e.receta(), e.faltantes()));
        return resultado;
    }

    /** Resultado de revisar una receta contra la despensa. */
    private record Evaluacion(Receta receta, List<Faltante> faltantes,
                              List<Sugerencia.Aprovechamiento> aprovechados) {
    }

    /**
     * Núcleo del algoritmo. Para cada ingrediente que pide la receta:
     *  - toma solo lotes NO vencidos, empezando por el que vence primero;
     *  - va "consumiendo" lotes hasta cubrir la cantidad requerida (en unidad base, así 1 kg cubre 200 g);
     *  - si consume un lote próximo a vencer, lo registra como ingrediente aprovechado;
     *  - si al final no alcanza, registra cuánto falta.
     * La despensa NO se modifica: es solo una simulación de cocinar la receta.
     */
    private Evaluacion evaluar(Receta receta) {
        LocalDate hoy = despensa.hoy();
        List<Faltante> faltantes = new ArrayList<>();
        List<Sugerencia.Aprovechamiento> aprovechados = new ArrayList<>();

        for (IngredienteReceta requerido : receta.getIngredientes()) {
            double porCubrir = requerido.getCantidadBase();

            for (Ingrediente lote : despensa.lotesVigentesDe(requerido.getNombre(), requerido.getUnidad())) {
                if (porCubrir <= Unidad.TOLERANCIA) {
                    break; // ya está cubierto, no hace falta tocar más lotes
                }
                double usado = Math.min(porCubrir, lote.getCantidadBase());
                porCubrir -= usado;

                if (lote.estaProximoAVencer(hoy)) {
                    aprovechados.add(new Sugerencia.Aprovechamiento(
                            lote.getNombre(),
                            lote.getUnidad().desdeBase(usado),
                            lote.getUnidad(),
                            lote.diasParaVencer(hoy)));
                }
            }

            if (porCubrir > Unidad.TOLERANCIA) {
                faltantes.add(new Faltante(
                        requerido.getNombre(),
                        requerido.getUnidad().desdeBase(porCubrir), // se informa en la unidad de la receta
                        requerido.getUnidad()));
            }
        }
        return new Evaluacion(receta, faltantes, aprovechados);
    }
}
