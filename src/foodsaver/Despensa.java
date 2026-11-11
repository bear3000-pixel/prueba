package foodsaver;

import java.time.Clock;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * La despensa del hogar: guarda los ingredientes (cada fecha de vencimiento distinta
 * es un "lote" aparte), los ordena por vencimiento y separa los vencidos.
 *
 * Recibe un Clock para saber qué día es "hoy". En el programa real se usa el reloj del
 * sistema; en las pruebas y la demostración se usa un reloj fijo y así el resultado
 * no depende del día en que se ejecute.
 */
public class Despensa {

    /** Del que vence primero al que vence último; si empatan, por nombre. */
    private static final Comparator<Ingrediente> POR_VENCIMIENTO =
            Comparator.comparing(Ingrediente::getFechaVencimiento)
                    .thenComparing(Ingrediente::getClaveNombre);

    private final Clock reloj;
    private final List<Ingrediente> lotes = new ArrayList<>();

    public Despensa(Clock reloj) {
        this.reloj = reloj;
    }

    /** Despensa que usa el reloj real del sistema. */
    public Despensa() {
        this(Clock.systemDefaultZone());
    }

    public LocalDate hoy() {
        return LocalDate.now(reloj);
    }

    /**
     * Agrega un ingrediente. Si ya existe uno con el mismo nombre y la misma fecha
     * de vencimiento, suma la cantidad en lugar de crear un registro duplicado.
     *
     * @return true si se sumó a un lote existente, false si se creó un lote nuevo
     */
    public boolean agregar(Ingrediente nuevo) {
        for (int i = 0; i < lotes.size(); i++) {
            Ingrediente existente = lotes.get(i);
            if (existente.esMismoLoteQue(nuevo)) {
                lotes.set(i, existente.sumar(nuevo));
                return true;
            }
        }
        lotes.add(nuevo);
        return false;
    }

    /**
     * Cambia la cantidad y/o la fecha de vencimiento de un ingrediente (null = dejar igual).
     * Si tras el cambio coincide con otro lote del mismo nombre y fecha, se fusionan.
     *
     * @return true si el resultado se fusionó con otro lote
     */
    public boolean actualizar(Ingrediente existente, Double nuevaCantidad, LocalDate nuevaFecha) {
        if (nuevaCantidad == null && nuevaFecha == null) {
            throw new DatoInvalidoException("Indique una cantidad nueva, una fecha nueva o ambas.");
        }
        // Se construye primero el ingrediente nuevo: si algún dato es inválido, falla aquí
        // y la despensa queda intacta.
        Ingrediente actualizado = existente;
        if (nuevaCantidad != null) {
            actualizado = actualizado.conCantidad(nuevaCantidad);
        }
        if (nuevaFecha != null) {
            actualizado = actualizado.conFecha(nuevaFecha);
        }
        if (!lotes.remove(existente)) {
            throw new DatoInvalidoException("Ese ingrediente no está en la despensa.");
        }
        return agregar(actualizado);
    }

    public boolean estaVacia() {
        return lotes.isEmpty();
    }

    /** Todos los ingredientes (vigentes y vencidos), del vencimiento más próximo al más lejano. */
    public List<Ingrediente> listarPorVencimiento() {
        return lotes.stream().sorted(POR_VENCIMIENTO).toList();
    }

    /** Ingredientes aún utilizables, ordenados por vencimiento. */
    public List<Ingrediente> listarVigentes() {
        LocalDate hoy = hoy();
        return lotes.stream().filter(l -> !l.estaVencido(hoy)).sorted(POR_VENCIMIENTO).toList();
    }

    /** Ingredientes vencidos, ordenados por vencimiento (el que venció hace más tiempo primero). */
    public List<Ingrediente> listarVencidos() {
        LocalDate hoy = hoy();
        return lotes.stream().filter(l -> l.estaVencido(hoy)).sorted(POR_VENCIMIENTO).toList();
    }

    /**
     * Lotes NO vencidos de un ingrediente que se pueden usar para una receta, del que vence primero
     * al que vence último. Es el único punto por donde el sugeridor ve la despensa, así que los
     * vencidos quedan excluidos de las recetas y del cálculo de lo disponible en un solo lugar.
     */
    public List<Ingrediente> lotesVigentesDe(String nombre, Unidad unidad) {
        String clave = Validaciones.claveDeNombre(nombre);
        LocalDate hoy = hoy();
        return lotes.stream()
                .filter(l -> l.getClaveNombre().equals(clave))
                .filter(l -> l.getUnidad().esCompatibleCon(unidad))
                .filter(l -> !l.estaVencido(hoy))
                .sorted(POR_VENCIMIENTO)
                .toList();
    }
}
