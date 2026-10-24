#!/usr/bin/env python3
"""
Crea hojas-contacto ligeras (miniaturas) de los proyectos, para poder enseñármelas y clasificarlas
(Cuina / Banys / Interiorisme / Reformes / Parquets) sin subir las fotos completas.

Usa la carpeta `imatges-web` que genera renombrar_imatges.py (carpetas p01-..., p02-... sin nombres de cliente).

Uso:
    pip install pillow
    python fulls_contacte.py imatges-web

Resultado: carpeta `fulls-contacte/` con unos pocos JPG (~300 KB cada uno). Sube esos JPG al chat.
"""
import os, re, sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

MINI_W, MINI_H = 250, 170        # miniatura
POR_FILA = 5                     # fotos por proyecto
PROYECTOS_POR_HOJA = 6
CALIDAD = 72


def natural(s):
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", s)]


def fuente(tam):
    for ruta in ("C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(ruta):
            return ImageFont.truetype(ruta, tam)
    return ImageFont.load_default()


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    origen = sys.argv[1]
    salida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fulls-contacte")
    os.makedirs(salida, exist_ok=True)
    carpetas = sorted([d for d in os.listdir(origen) if os.path.isdir(os.path.join(origen, d))], key=natural)
    f_tit = fuente(26)
    hojas = [carpetas[i:i + PROYECTOS_POR_HOJA] for i in range(0, len(carpetas), PROYECTOS_POR_HOJA)]
    for n, grupo in enumerate(hojas, 1):
        alto_fila = MINI_H + 44
        hoja = Image.new("RGB", (POR_FILA * (MINI_W + 8) + 8, len(grupo) * alto_fila + 8), "white")
        d = ImageDraw.Draw(hoja)
        for fila, carpeta in enumerate(grupo):
            pid = carpeta.split("-")[0].upper()          # P01 (nunca el nombre del cliente)
            loc = carpeta.split("-", 1)[1].replace("-", " ") if "-" in carpeta else ""
            y = 8 + fila * alto_fila
            d.text((8, y), f"{pid}   {loc}", fill=(20, 20, 20), font=f_tit)
            archivos = sorted([f for f in os.listdir(os.path.join(origen, carpeta))
                               if f.lower().endswith((".webp", ".jpg", ".jpeg", ".png"))], key=natural)
            # fotos repartidas a lo largo de la carpeta (no solo las primeras)
            pasos = [archivos[round(i * (len(archivos) - 1) / max(1, POR_FILA - 1))] for i in range(min(POR_FILA, len(archivos)))]
            for col, a in enumerate(dict.fromkeys(pasos)):
                try:
                    im = ImageOps.exif_transpose(Image.open(os.path.join(origen, carpeta, a))).convert("RGB")
                except Exception:
                    continue
                im = ImageOps.fit(im, (MINI_W, MINI_H))
                hoja.paste(im, (8 + col * (MINI_W + 8), y + 36))
        ruta = os.path.join(salida, f"hoja-{n:02d}.jpg")
        hoja.save(ruta, "JPEG", quality=CALIDAD, optimize=True)
        print(ruta, f"{os.path.getsize(ruta) // 1024} KB", [c.split('-')[0].upper() for c in grupo])
    print("\nSube estas hojas al chat y te digo a qué categoría pertenece cada proyecto.")


if __name__ == "__main__":
    main()
