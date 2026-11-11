package foodsaver;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

/**
 * Un lote de ingrediente en la despensa: nombre, cantidad, unidad y fecha de vencimiento.
 *
 * La clase es inmutable: para "modificar" un ingrediente se crea uno nuevo
 * (conCantidad, conFecha, sumar). Así los datos validados en el constructor
 * nunca pueden quedar en un estado inválido.
 */
public final class Ingrediente {

    /** Un ingrediente está "próximo a vencer" si faltan este número de días o menos. Cámbielo aquí. */
    public static final int DIAS_PROXIMO_A_VENCER = 3;

    private final String nombre;
    private final String claveNombre; // nombre normalizado, solo para comparar
    private final double cantidad;
    private final Unidad unidad;
    private final LocalDate fechaVencimiento;

    public Ingrediente(String nombre, double cantidad, Unidad unidad, LocalDate fechaVencimiento) {
        if (unidad == null) {
            throw new DatoInvalidoException("La unidad es obligatoria.");
        }
        if (fechaVencimiento == null) {
            throw new DatoInvalidoException("La fecha de vencimiento es obligatoria.");
        }
        this.nombre = Validaciones.nombre(nombre);
        this.claveNombre = Validaciones.claveDeNombre(this.nombre);
        this.cantidad = Validaciones.cantidad(cantidad);
        this.unidad = unidad;
        this.fechaVencimiento = fechaVencimiento;
    }

    /**
     * Crea un ingrediente a partir de textos crudos (lo que escribe el usuario).
     * Valida en orden y falla en el primer dato incorrecto con un mensaje claro.
     */
    public static Ingrediente desdeTexto(String nombre, String cantidad, String unidad, String fecha) {
        return new Ingrediente(
                Validaciones.nombre(nombre),
                Validaciones.cantidad(cantidad),
                Unidad.desdeTexto(unidad),
                Validaciones.fecha(fecha));
    }

    // ----- Consultas de vencimiento (reciben "hoy" como parámetro para poder probarlas) -----

    /** Vencido = su fecha ya pasó. Si vence hoy todavía se puede usar. */
    public boolean estaVencido(LocalDate hoy) {
        return fechaVencimiento.isBefore(hoy);
    }

    /** Días que faltan para vencer (negativo si ya venció). */
    public long diasParaVencer(LocalDate hoy) {
        return ChronoUnit.DAYS.between(hoy, fechaVencimiento);
    }

    public boolean estaProximoAVencer(LocalDate hoy) {
        return !estaVencido(hoy) && diasParaVencer(hoy) <= DIAS_PROXIMO_A_VENCER;
    }

    // ----- Operaciones que devuelven un ingrediente nuevo -----

    public Ingrediente conCantidad(double nuevaCantidad) {
        return new Ingrediente(nombre, nuevaCantidad, unidad, fechaVencimiento);
    }

    public Ingrediente conFecha(LocalDate nuevaFecha) {
        return new Ingrediente(nombre, cantidad, unidad, nuevaFecha);
    }

    /** Dos registros son el mismo lote si tienen el mismo nombre, la misma fecha y unidades compatibles. */
    public boolean esMismoLoteQue(Ingrediente otro) {
        return claveNombre.equals(otro.claveNombre)
                && fechaVencimiento.equals(otro.fechaVencimiento)
                && unidad.esCompatibleCon(otro.unidad);
    }

    /** Suma la cantidad de otro lote del mismo tipo (convirtiendo unidades: 1 kg + 500 g = 1.5 kg). */
    public Ingrediente sumar(Ingrediente otro) {
        double cantidadDelOtro = otro.unidad.convertir(otro.cantidad, unidad);
        return new Ingrediente(nombre, cantidad + cantidadDelOtro, unidad, fechaVencimiento);
    }

    /** Cantidad expresada en la unidad base (g, ml o unidad), para comparar con las recetas. */
    public double getCantidadBase() {
        return unidad.aBase(cantidad);
    }

    public String getNombre() {
        return nombre;
    }

    public String getClaveNombre() {
        return claveNombre;
    }

    public double getCantidad() {
        return cantidad;
    }

    public Unidad getUnidad() {
        return unidad;
    }

    public LocalDate getFechaVencimiento() {
        return fechaVencimiento;
    }

    @Override
    public String toString() {
        return nombre + " " + unidad.formatear(cantidad) + " (vence " + fechaVencimiento + ")";
    }
}
