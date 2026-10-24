#!/usr/bin/env python3
"""
Reduce las carpetas/zips de proyectos de Creem Llar a un paquete ligero para subirlo.

Uso (Windows, en la terminal):
    pip install pillow
    python reducir_proyectos.py "C:\\Users\\pc\\Downloads\\wetransfer_creem-llar_...\\creem llar"

Resultado: carpeta "creem-llar-reduit" (junto al script) con:
  - pNN-<localitat>-1.jpg, -2.jpg  (máx. 1600 px, calidad 80)
  - projectes.csv  (id, localitat deducida del nombre, categoria vacía, nombre original)
Después comprime esa carpeta en un .zip (suele quedar por debajo de 30-40 MB) y súbelo.
Opcional: pip install pillow-heif para incluir fotos .HEIC.
"""
import csv, io, os, re, sys, zipfile, unicodedata

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Falta Pillow. Ejecuta primero:  pip install pillow")
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

FOTOS_POR_PROYECTO = 2
LADO_MAX = 1600
CALIDAD = 80
EXT = (".jpg", ".jpeg", ".png", ".webp", ".heic")
SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "creem-llar-reduit")


def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def localitat(nombre):
    """'NOM CLIENT_FIGUERES-2026...' -> 'Figueres'; sin guion bajo -> ''."""
    base = re.sub(r"\.[A-Za-z0-9]+$", "", nombre)
    if "_" not in base:
        return ""
    t = base.split("_")[-1]
    t = re.split(r"[-\s]*(drive|download|confirmat|\d{4})", t, flags=re.I)[0]
    return t.strip(" -_.").title()


def guardar(img_bytes, destino):
    try:
        im = Image.open(io.BytesIO(img_bytes))
        im = ImageOps.exif_transpose(im).convert("RGB")
    except Exception as e:
        print("   (omitida, no se pudo abrir:", e, ")")
        return False
    im.thumbnail((LADO_MAX, LADO_MAX))
    im.save(destino, "JPEG", quality=CALIDAD, optimize=True)
    return True


def imagenes_de(ruta):
    """Devuelve [(nombre, bytes)] de un zip, carpeta o archivo suelto, las más pesadas primero."""
    items = []
    if os.path.isdir(ruta):
        for r, _, fs in os.walk(ruta):
            for f in fs:
                if f.lower().endswith(EXT):
                    p = os.path.join(r, f); items.append((f, os.path.getsize(p), p))
        items.sort(key=lambda x: -x[1])
        return [(n, open(p, "rb").read()) for n, _, p in items[:FOTOS_POR_PROYECTO * 3]]
    if ruta.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(ruta) as z:
                infos = [i for i in z.infolist() if i.filename.lower().endswith(EXT) and not i.is_dir()]
                infos.sort(key=lambda i: -i.file_size)
                return [(os.path.basename(i.filename), z.read(i)) for i in infos[:FOTOS_POR_PROYECTO * 3]]
        except zipfile.BadZipFile:
            print("   (zip dañado o no es .zip real; si es .rar, extráelo antes con WinRAR)")
            return []
    if ruta.lower().endswith(EXT):
        return [(os.path.basename(ruta), open(ruta, "rb").read())]
    return []


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    origen = sys.argv[1]
    os.makedirs(SALIDA, exist_ok=True)
    filas, n = [], 0
    for nombre in sorted(os.listdir(origen)):
        ruta = os.path.join(origen, nombre)
        if not (os.path.isdir(ruta) or nombre.lower().endswith((".zip",) + EXT)):
            if nombre.lower().endswith(".rar"):
                print("RAR no soportado, extráelo antes:", nombre)
            continue
        print(nombre)
        imgs = imagenes_de(ruta)
        if not imgs:
            continue
        n += 1
        loc = localitat(nombre)
        pid = f"p{n:02d}"
        guardadas = 0
        for nom, data in imgs:
            if guardadas >= FOTOS_POR_PROYECTO:
                break
            dest = os.path.join(SALIDA, f"{pid}-{slug(loc) or 'sense-localitat'}-{guardadas + 1}.jpg")
            if guardar(data, dest):
                guardadas += 1
        filas.append([pid, loc, "", guardadas, nombre])
        print(f"   -> {pid} {loc or '(sin localidad)'} · {guardadas} foto(s)")
    with open(os.path.join(SALIDA, "projectes.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id", "localitat", "categoria (Cuina/Banys/Interiorisme/Reformes/Parquets)", "fotos", "original"])
        w.writerows(filas)
    print(f"\nListo: {n} proyectos en {SALIDA}")
    print("Rellena la columna 'categoria' en projectes.csv, comprime la carpeta en .zip y súbela.")


if __name__ == "__main__":
    main()
