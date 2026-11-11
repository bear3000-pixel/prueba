package foodsaver;

/**
 * Error de validación de un dato ingresado por el usuario
 * (nombre, cantidad, unidad, fecha u opción de menú).
 *
 * Es una excepción "no comprobada": el menú la captura, muestra el mensaje y
 * continúa, así el programa nunca se cae por una entrada incorrecta.
 */
public class DatoInvalidoException extends IllegalArgumentException {

    private static final long serialVersionUID = 1L;

    public DatoInvalidoException(String mensaje) {
        super(mensaje);
    }
}
