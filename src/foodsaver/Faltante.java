package foodsaver;

/**
 * Lo que le falta a una receta de un ingrediente: nombre y cantidad que hay que conseguir,
 * expresada en la misma unidad que usa la receta.
 */
public record Faltante(String nombre, double cantidad, Unidad unidad) {

    /** Ejemplo: "500 g de papa". */
    public String describir() {
        return unidad.formatear(cantidad) + " de " + nombre;
    }
}
