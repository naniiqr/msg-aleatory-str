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
- **Nosaltres y Contacte** se han construido con los textos del web actual (traducidos al catalán): equipo, direcciones, teléfonos, horario y mapas. Nosaltres reutiliza los bloques de la home del PDF (sin cita ni marcas). Faltan las fotos reales (equipo, tienda).
- Footer: añade horario, redes (enlaces `#` por completar) y política de privacidad.
- Hero: es un contenedor con imagen (el PDF muestra flechas de slider; se puede pasar al widget *Slides*).
- Feed de Instagram: imagen fija; sustituir por plugin (Smash Balloon) cuando se quiera dinámico.
- Filtro de Projectes: JS en un widget HTML sobre contenedores estáticos (ideal: CPT + Loop Grid).

## Previsualización web (GitHub Pages)
`docs/` es una web navegable: `index.html` = Inici y el menú enlaza las 8 páginas entre sí. Se regenera con `python3 creem-llar/build.py`. En Settings → Pages elige la rama y la carpeta `/docs`.

## Fitxa de projecte (plantilla per duplicar)
`output/json/projecte.json` (preview: `docs/projecte.html`). Importa-la una vegada, crea una pàgina "Projecte - <nom>" i duplica-la per a cada projecte:
1. Canvia títol (H1), localitat, tipus i superfície, el text del repte i de la solució i la llista de punts.
2. Substitueix les imatges: fons del hero, imatge del repte, fons de la solució i les 5 de la galeria (obren en lightbox).
3. Escriu el SEO del projecte amb la fórmula: `<tipus de projecte> a <localitat>` (keyphrase), al principi del títol i de la descripció.

## Projectes amb pestanyes
`projectes.json` usa el widget **Pestanyes niuades** (Tabs) d'Elementor: Tots · Cuina · Banys · Interiorisme · Reformes · Parquets (+ "Per classificar", temporal).
- Les dades surten de `data/projectes.csv` (34 projectes). Omple la columna *categoria* i torna a generar (`python3 build.py`) o envia'm el CSV.
- El títol de cada targeta és `[NOM DE LA CARPETA]` com a guia: l'esborres en carregar el projecte. La localitat és real.
- `tools/classificar_projectes.py` proposa categories a partir dels noms de carpetes/fitxers.
- Cada projecte apareix a "Tots" i a la seva categoria: copia/enganxa la targeta (Ctrl+C / Ctrl+V) ja amb la foto posada.

## Proyectos dinámicos
Ver `GUIA-PROJECTES-DINAMICS.md`. Archivos: `output/acf/camps-projecte.json`, `output/json/projecte-dinamic.json`, `projecte-targeta-loop.json`, `projectes-dinamic.json`.

## Ficha de proyecto manual (la más simple)
`output/json/projecte-general.json`: textos generales listos; solo se cambian título, localidad, tipo y fotos.
