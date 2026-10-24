# Proyectos dinámicos (Elementor Pro + ACF gratuito)

Idea: **una sola plantilla** para todas las fichas de proyecto. Cada proyecto es una entrada (tipo «Projecte»); la plantilla se rellena sola con sus datos. Si un campo está vacío, se muestra un texto general.

## Configuración (una sola vez, ~15 min)
1. Instala **ACF** (gratuito).
2. **ACF → Tipos de entrada → Añadir nuevo**
   - Plural `Projectes`, singular `Projecte`, **clave `projecte`**.
   - Soporta: Título, Imagen destacada, Extracto. (Archivo desactivado.)
3. **ACF → Taxonomías → Añadir nueva**
   - Plural `Categories de projecte`, singular `Categoria de projecte`, **clave `categoria_projecte`**, asociada a `Projectes`, jerárquica.
   - Crea los términos: **Cuina, Banys, Interiorisme, Reformes, Parquets**.
4. **ACF → Herramientas → Importar** → `camps-projecte.json` (crea los campos de cada proyecto).
5. **Elementor → Plantillas → Theme Builder → Entrada única (Single Post)** → importa `projecte-dinamic.json`.
   Condiciones: *Incluir → Entrada → Projectes*. Publica.
6. **Plantillas → Importar** `projecte-targeta-loop.json` (tipo Loop Item): es la tarjeta del listado.
7. Importa `projectes-dinamic.json` en la página **Projectes**. En el widget **Loop Grid** elige la plantilla «Targeta de projecte»; en el **Filtro de taxonomía** comprueba que usa `categoria_projecte` y apunta al grid (ID `cl-projectes-grid`).

## Crear un proyecto (≈2 min)
**Projectes → Añadir nuevo**
| Dónde | Qué | ¿Obligatorio? |
|---|---|---|
| Título | Nombre del proyecto (sale como H1) | Sí |
| Imagen destacada | Foto de portada (hero de la ficha y tarjeta del listado) | Sí |
| Categoría | Cuina / Banys / Interiorisme / Reformes / Parquets | Sí |
| Localitat | Ej.: Figueres | Sí |
| Extracto | 1-2 líneas bajo el título | No (hay texto general) |
| Superfície, El repte, La solució, 5 puntos | Datos y textos | No (hay texto general) |
| Imatge del repte / de la solució / Galeria 1-5 | Fotos extra | No |

Publicas y listo: aparece en el listado, en el filtro de su categoría y tiene su propia página.

## Qué es dinámico
Título, imagen destacada, categoría, extracto, localitat, superfície, textos, 5 puntos y 7 imágenes.
