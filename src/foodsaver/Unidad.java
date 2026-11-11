package foodsaver;

import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.Locale;

/**
 * Unidades de medida soportadas.
 *
 * Cada unidad sabe convertirse a una unidad "base" de su misma magnitud
 * (g para masa, ml para volumen, unidad para conteo). Gracias a eso se puede
 * comparar 1 kg de arroz de la despensa contra los 200 g que pide una receta.
 */
public enum Unidad {
    G("g", "g", Magnitud.MASA, 1),
    KG("kg", "kg", Magnitud.MASA, 1000),
    ML("ml", "ml", Magnitud.VOLUMEN, 1),
    L("l", "l", Magnitud.VOLUMEN, 1000),
    UNIDAD("unidad", "unidades", Magnitud.CONTEO, 1);

    /** Tolerancia para comparar decimales (evita errores de redondeo tipo 0.1 + 0.2). */
    public static final double TOLERANCIA = 1e-9;

    /** Tipo de cosa que se mide: solo se pueden convertir unidades de la misma magnitud. */
    public enum Magnitud { MASA, VOLUMEN, CONTEO }

    private final String simbolo;
    private final String plural;
    private final Magnitud magnitud;
    private final double factorABase;

    Unidad(String simbolo, String plural, Magnitud magnitud, double factorABase) {
        this.simbolo = simbolo;
        this.plural = plural;
        this.magnitud = magnitud;
        this.factorABase = factorABase;
    }

    public boolean esCompatibleCon(Unidad otra) {
        return magnitud == otra.magnitud;
    }

    /** Convierte una cantidad expresada en esta unidad a la unidad base de su magnitud. */
    public double aBase(double cantidad) {
        return cantidad * factorABase;
    }

    /** Convierte una cantidad en unidad base a esta unidad (inversa de aBase). */
    public double desdeBase(double cantidadBase) {
        return cantidadBase / factorABase;
    }

    /** Convierte una cantidad de esta unidad a otra de la misma magnitud (ej. 500 g -> 0.5 kg). */
    public double convertir(double cantidad, Unidad destino) {
        if (!esCompatibleCon(destino)) {
            throw new DatoInvalidoException(
                    "No se puede convertir '" + simbolo + "' a '" + destino.simbolo + "'.");
        }
        return destino.desdeBase(aBase(cantidad));
    }

    /** Texto legible: "500 g", "1.5 kg", "1 unidad", "3 unidades". */
    public String formatear(double cantidad) {
        // Locale.ROOT fuerza el punto decimal sin importar la configuración regional.
        DecimalFormat formato = new DecimalFormat("0.###", DecimalFormatSymbols.getInstance(Locale.ROOT));
        boolean esUno = Math.abs(cantidad - 1) < TOLERANCIA;
        return formato.format(cantidad) + " " + (esUno ? simbolo : plural);
    }

    /** Interpreta el texto escrito por el usuario (g, kg, ml, l, unidad/unidades). */
    public static Unidad desdeTexto(String texto) {
        if (texto == null || texto.isBlank()) {
            throw new DatoInvalidoException(
                    "La unidad no puede estar vacía. Unidades válidas: " + valoresValidos() + ".");
        }
        String limpio = texto.trim().toLowerCase(Locale.ROOT);
        for (Unidad unidad : values()) {
            if (unidad.simbolo.equals(limpio) || unidad.plural.equals(limpio)) {
                return unidad;
            }
        }
        throw new DatoInvalidoException(
                "Unidad no reconocida: '" + texto.trim() + "'. Unidades válidas: " + valoresValidos() + ".");
    }

    public static String valoresValidos() {
        return "g, kg, ml, l, unidad";
    }

    @Override
    public String toString() {
        return simbolo;
    }
}
