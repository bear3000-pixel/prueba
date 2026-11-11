package foodsaver;

import java.util.List;

/**
 * Una receta que se puede preparar con lo que hay en la despensa, junto con los
 * ingredientes próximos a vencer que se aprovechan al prepararla.
 */
public record Sugerencia(Receta receta, List<Aprovechamiento> aprovechados) {

    /**
     * Un ingrediente próximo a vencer que la receta consume.
     *
     * @param ingrediente   nombre del ingrediente en la despensa
     * @param cantidadUsada cuánto de ese lote usa la receta (en la unidad del lote)
     * @param unidad        unidad del lote
     * @param diasRestantes días que faltan para que venza (0 = vence hoy)
     */
    public record Aprovechamiento(String ingrediente, double cantidadUsada, Unidad unidad, long diasRestantes) {

        /** Cuanto más cerca del vencimiento, más puntos: vence hoy = 4, mañana = 3, ..., en 3 días = 1. */
        public int puntos() {
            return Ingrediente.DIAS_PROXIMO_A_VENCER + 1 - (int) diasRestantes;
        }
    }

    /** Puntaje de urgencia de la receta: suma de los puntos de los ingredientes que rescata. */
    public int puntaje() {
        return aprovechados.stream().mapToInt(Aprovechamiento::puntos).sum();
    }
}
