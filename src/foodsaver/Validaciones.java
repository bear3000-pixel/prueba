package foodsaver;

import java.text.Normalizer;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.Locale;

/**
 * Validación y conversión de los textos que escribe el usuario.
 * Todas las reglas de "dato inválido" viven aquí, en un solo lugar.
 */
public final class Validaciones {

    /** Formato de fecha exigido: yyyy-MM-dd (ISO_LOCAL_DATE rechaza fechas inexistentes como 2025-02-30). */
    private static final DateTimeFormatter FORMATO_FECHA = DateTimeFormatter.ISO_LOCAL_DATE;

    /** Número simple: signo opcional, dígitos y un separador decimal (punto o coma). Rechaza "1e5", "5f", "NaN". */
    private static final String PATRON_NUMERO = "[-+]?(\\d+([.,]\\d+)?|[.,]\\d+)";

    private Validaciones() {
        // Clase de utilidades: no se instancia.
    }

    /** Devuelve el nombre sin espacios sobrantes; rechaza vacío o nulo. */
    public static String nombre(String texto) {
        if (texto == null || texto.isBlank()) {
            throw new DatoInvalidoException("El nombre no puede estar vacío.");
        }
        return texto.trim().replaceAll("\\s+", " ");
    }

    /** Convierte texto a cantidad (acepta "2.5" o "2,5"); rechaza vacío, no numérico, cero y negativos. */
    public static double cantidad(String texto) {
        if (texto == null || texto.isBlank()) {
            throw new DatoInvalidoException("La cantidad no puede estar vacía.");
        }
        String limpio = texto.trim();
        if (!limpio.matches(PATRON_NUMERO)) {
            throw new DatoInvalidoException(
                    "La cantidad '" + limpio + "' no es un número válido (ejemplo: 2.5).");
        }
        double valor = Double.parseDouble(limpio.replace(',', '.'));
        return validarPositiva(valor, limpio);
    }

    /** Valida una cantidad que ya es numérica (la usan los constructores). */
    public static double cantidad(double valor) {
        return validarPositiva(valor, String.valueOf(valor));
    }

    private static double validarPositiva(double valor, String textoOriginal) {
        if (Double.isNaN(valor) || Double.isInfinite(valor)) {
            throw new DatoInvalidoException("La cantidad '" + textoOriginal + "' no es un número finito.");
        }
        if (valor <= 0) {
            throw new DatoInvalidoException(
                    "La cantidad debe ser mayor que cero (se recibió: " + textoOriginal + ").");
        }
        return valor;
    }

    /** Convierte texto yyyy-MM-dd a LocalDate; rechaza vacío, otro formato o fechas inexistentes. */
    public static LocalDate fecha(String texto) {
        if (texto == null || texto.isBlank()) {
            throw new DatoInvalidoException(
                    "La fecha no puede estar vacía. Use el formato yyyy-MM-dd (ejemplo: 2025-06-30).");
        }
        String limpio = texto.trim();
        try {
            return LocalDate.parse(limpio, FORMATO_FECHA);
        } catch (DateTimeParseException e) {
            throw new DatoInvalidoException(
                    "Fecha inválida '" + limpio + "'. Use el formato yyyy-MM-dd con una fecha real (ejemplo: 2025-06-30).");
        }
    }

    /**
     * Clave para comparar nombres sin importar mayúsculas, tildes ni espacios dobles:
     * "  Plátano " y "platano" se consideran el mismo ingrediente.
     */
    public static String claveDeNombre(String nombre) {
        String sinTildes = Normalizer.normalize(nombre, Normalizer.Form.NFD).replaceAll("\\p{M}", "");
        return sinTildes.trim().replaceAll("\\s+", " ").toLowerCase(Locale.ROOT);
    }
}
