# Creem Llar · Elementor (lote 1)

Generat amb `python3 build.py`. Cada component es defineix una sola vez y de él salen el JSON de Elementor y el HTML de previsualización.

## Contenido
| Carpeta | Qué hay |
|---|---|
| `output/json/` | `header.json`, `footer.json` y un JSON por página: inici, projectes, cuines, banys, interiorisme, parquets, nosaltres, contacte |
| `output/descarregar/` | un HTML autocontenido por página (imágenes incrustadas) |
| `output/html/` | Mismas previsualizaciones, con imágenes de `assets/` |
| `assets/` | Imágenes recortadas del PDF (**solo marcadores de posición**) |

## Cómo importar
1. **Imágenes**: sube `assets/*` a Medios. El JSON apunta a
   `https://proveswebsfigueres.com/creemllar/wp-content/uploads/2026/10/<archivo>`
   (cámbialo en `BASE_URL` de `build.py` si las subes en otro mes). Mejor aún: súbelas con los mismos nombres y, cuando tengas los originales, sustitúyelas.
2. **Menú**: Apariencia → Menús → crea uno llamado **Menu principal** (slug `menu-principal`) con Inici, Projectes, Cuines, Banys, Interiorisme, Parquets, Nosaltres, Contacte.
3. **Header y footer**: Elementor → Plantillas → Theme Builder → importa `header.json` y `footer.json`, publica y aplica condición *Todo el sitio*.
4. **Páginas**: crea las 8 páginas con los slugs del menú, importa cada JSON desde Plantillas → Guardadas → Importar, e insértalas en la página (la plantilla de página ya va como *Elementor Header & Footer*).

## Pendiente / decisiones
- **Provisionales** (el PDF solo diseña Inici y Projectes): Cuines, Banys, Interiorisme, Parquets, Nosaltres y Contacte. Reutilizan los componentes del PDF; los textos de Parquets y Nosaltres son míos y hay que validarlos. El formulario de Contacte envía a info@creemllar.com (a confirmar).
- **Nosaltres y Contacte** se han construido con los textos del web actual (traducidos al catalán): citas, equipo, marcas, direcciones, teléfonos, horario y mapas. Faltan las fotos reales (equipo, tienda) y los logos de Levantina, Lapitec, Laminam y Kronoswiss (ahora hay marcadores de texto).
- Footer: añade horario, redes (enlaces `#` por completar) y política de privacidad.
- Hero: es un contenedor con imagen (el PDF muestra flechas de slider; se puede pasar al widget *Slides*).
- Feed de Instagram: imagen fija; sustituir por plugin (Smash Balloon) cuando se quiera dinámico.
- Filtro de Projectes: JS en un widget HTML sobre contenedores estáticos (ideal: CPT + Loop Grid).
