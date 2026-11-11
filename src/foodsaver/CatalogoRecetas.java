package foodsaver;

import java.util.List;

/** Colección predefinida de recetas, cargada directamente en el código. */
public final class CatalogoRecetas {

    private CatalogoRecetas() {
        // Clase de utilidades: no se instancia.
    }

    public static List<Receta> cargar() {
        return List.of(
                new Receta("Omelette de espinaca",
                        List.of(ing("huevo", 3, Unidad.UNIDAD),
                                ing("espinaca", 100, Unidad.G),
                                ing("queso", 50, Unidad.G)),
                        "Batir los huevos. Saltear la espinaca 2 minutos, agregar los huevos y el queso "
                                + "y cocinar 4 minutos por lado."),

                new Receta("Arroz con tomate",
                        List.of(ing("arroz", 200, Unidad.G),
                                ing("tomate", 300, Unidad.G),
                                ing("cebolla", 1, Unidad.UNIDAD),
                                ing("aceite", 20, Unidad.ML)),
                        "Sofreír la cebolla picada en el aceite, agregar el tomate en trozos, incorporar "
                                + "el arroz con el doble de agua y cocinar 18 minutos a fuego bajo."),

                new Receta("Pasta con salsa de tomate",
                        List.of(ing("pasta", 250, Unidad.G),
                                ing("tomate", 400, Unidad.G),
                                ing("cebolla", 1, Unidad.UNIDAD),
                                ing("aceite", 20, Unidad.ML)),
                        "Hervir la pasta 10 minutos. Sofreír la cebolla, agregar el tomate picado y cocinar "
                                + "15 minutos. Mezclar la salsa con la pasta."),

                new Receta("Tortilla de papa",
                        List.of(ing("papa", 500, Unidad.G),
                                ing("huevo", 4, Unidad.UNIDAD),
                                ing("cebolla", 1, Unidad.UNIDAD),
                                ing("aceite", 50, Unidad.ML)),
                        "Freír la papa y la cebolla en rodajas hasta que estén blandas, mezclarlas con los "
                                + "huevos batidos y cuajar 5 minutos por lado."),

                new Receta("Crepes",
                        List.of(ing("harina", 200, Unidad.G),
                                ing("leche", 500, Unidad.ML),
                                ing("huevo", 2, Unidad.UNIDAD)),
                        "Licuar todo, dejar reposar 15 minutos y cocinar porciones finas en una sartén "
                                + "caliente, 1 minuto por lado."),

                new Receta("Arroz con leche",
                        List.of(ing("leche", 1, Unidad.L),
                                ing("arroz", 150, Unidad.G),
                                ing("azúcar", 100, Unidad.G)),
                        "Cocinar el arroz con la leche a fuego bajo 35 minutos, moviendo seguido, "
                                + "y agregar el azúcar al final."),

                new Receta("Sopa de verduras",
                        List.of(ing("zanahoria", 200, Unidad.G),
                                ing("papa", 300, Unidad.G),
                                ing("cebolla", 1, Unidad.UNIDAD)),
                        "Cortar las verduras en cubos, sofreír la cebolla, agregar el resto con 1 litro "
                                + "de agua y hervir 25 minutos.")
        );
    }

    /** Atajo para escribir los ingredientes de cada receta en una sola línea. */
    private static IngredienteReceta ing(String nombre, double cantidad, Unidad unidad) {
        return new IngredienteReceta(nombre, cantidad, unidad);
    }
}
