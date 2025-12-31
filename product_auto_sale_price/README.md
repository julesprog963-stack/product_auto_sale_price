# Product Automatic Sale Price

Calcula `list_price` en productos a partir del costo usando fórmulas heredables desde la categoría. Incluye acción masiva para recalcular precios sin tocar el core.

## Funcionalidad
- Campos en producto (`product.template`): habilitar cálculo automático, tipo de fórmula (porcentaje/coeficiente/suma fija), valor, y campos de solo lectura para mostrar origen/tipo/valor efectivo.
- Campos en categoría (`product.category`): activar auto precio por defecto y definir fórmula/valor por defecto para productos sin fórmula propia.
- Fallback producto → categoría: si el producto no define fórmula se usa la de la categoría. Al cambiar la fórmula por defecto de la categoría se recalculan sus productos que usan la herencia y tienen el flag activo.
- Acción masiva “Recalcular precios de venta” en la vista lista de productos (Actions) que recalcula `list_price` de los seleccionados sin abrir fichas.
- Cálculo: `percent = costo * (1 + valor/100)`, `factor = costo * valor`, `fixed = costo + valor`; se redondea con la moneda del producto.

## Enfoque técnico
- No se toca `list_price` como campo computado; se actualiza mediante `onchange`, `create/write` y la acción masiva, evitando loops y manteniendo compatibilidad con listas de precios estándar.
- Defaults desde categoría se aplican al crear/cambiar categoría en el formulario, pero el flag por producto sigue mandando.


## Pruebas rápidas
- En producto: activar “Precio de venta automático”, elegir tipo de fórmula y valor, cambiar costo y verificar que `Precio de Venta` se actualiza y persiste.
- Fallback: dejar fórmula vacía en producto, configurar fórmula en categoría y activar el flag; comprobar que el precio usa la categoría.
- Acción masiva: en la lista de productos seleccionar varios y ejecutar “Recalcular precios de venta”; confirmar que los precios cambian sin abrir las fichas.
- Pricelists: usar una lista basada en `Sales Price` y validar que toma el `list_price` resultante.
