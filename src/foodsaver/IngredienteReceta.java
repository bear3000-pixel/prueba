package foodsaver;

/**
 * Un ingrediente que pide una receta: nombre, cantidad y unidad.
 * (A diferencia de Ingrediente, no tiene fecha de vencimiento: es solo un requisito.)
 */
public final class IngredienteReceta {

    private final String nombre;
    private final String claveNombre;
    private final double cantidad;
    private final Unidad unidad;

    public IngredienteReceta(String nombre, double cantidad, Unidad unidad) {
        if (unidad == null) {
            throw new DatoInvalidoException("La unidad es obligatoria.");
        }
        this.nombre = Validaciones.nombre(nombre);
        this.claveNombre = Validaciones.claveDeNombre(this.nombre);
        this.cantidad = Validaciones.cantidad(cantidad);
        this.unidad = unidad;
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

    public double getCantidadBase() {
        return unidad.aBase(cantidad);
    }

    /** Ejemplo: "100 g de espinaca". */
    public String describir() {
        return unidad.formatear(cantidad) + " de " + nombre;
    }
}
