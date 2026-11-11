package foodsaver;

import java.util.List;
import java.util.stream.Collectors;

/** Una receta: nombre, ingredientes necesarios e instrucciones breves de preparación. */
public final class Receta {

    private final String nombre;
    private final List<IngredienteReceta> ingredientes;
    private final String instrucciones;

    public Receta(String nombre, List<IngredienteReceta> ingredientes, String instrucciones) {
        this.nombre = Validaciones.nombre(nombre);
        if (ingredientes == null || ingredientes.isEmpty()) {
            throw new DatoInvalidoException("La receta '" + this.nombre + "' debe tener al menos un ingrediente.");
        }
        this.ingredientes = List.copyOf(ingredientes); // copia inmutable: nadie la modifica por fuera
        this.instrucciones = instrucciones == null ? "" : instrucciones.trim();
    }

    public String getNombre() {
        return nombre;
    }

    public List<IngredienteReceta> getIngredientes() {
        return ingredientes;
    }

    public String getInstrucciones() {
        return instrucciones;
    }

    /** Ejemplo: "3 unidades de huevo, 100 g de espinaca, 50 g de queso". */
    public String describirIngredientes() {
        return ingredientes.stream()
                .map(IngredienteReceta::describir)
                .collect(Collectors.joining(", "));
    }
}
