#!/usr/bin/env python3
"""
Renombra las fotos de los proyectos SIN el nombre del cliente y sin recomprimir (misma calidad).

Cada archivo pasa a llamarse:   <tipo>-<localidad>-<id>-<nn>.webp     (ej.: cuina-figueres-p01-03.webp)
  · el <id> (p01, p02...) hace único cada proyecto, aunque haya dos cocinas en la misma localidad
  · el nombre del cliente NO aparece en ningún archivo ni carpeta de salida

Uso (Windows, en una terminal dentro de esta carpeta):
    python renombrar_imatges.py "C:\\ruta\\carpeta con los proyectos" projectes.csv

Genera, junto al script:
    imatges-web/            fotos listas para subir a WordPress (una carpeta por proyecto: p01-cuina-figueres, ...)
    textos-alt.csv          nombre de archivo + texto alternativo + título sugerido
    CLAVES-PRIVADAS.csv     relación id <-> nombre del cliente. NO SUBIR NUNCA. Guárdalo en tu ordenador.
Opcional: --netejar-metadades  quita datos EXIF/XMP (ubicación GPS, autor) de los .webp sin perder calidad.
"""
import csv, os, re, shutil, struct, sys, unicodedata

EXT = (".webp", ".jpg", ".jpeg", ".png")
SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imatges-web")


def norm(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", " ", t).strip()


def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def natural(s):
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", s)]


def quitar_metadatos_webp(datos):
    """Elimina los bloques EXIF y XMP de un WebP sin recodificar la imagen. Devuelve (bytes, quitados)."""
    if datos[:4] != b"RIFF" or datos[8:12] != b"WEBP":
        return datos, 0
    pos, partes, quitados = 12, [], 0
    while pos + 8 <= len(datos):
        tipo, tam = datos[pos:pos + 4], struct.unpack("<I", datos[pos + 4:pos + 8])[0]
        fin = pos + 8 + tam + (tam & 1)
        bloque = datos[pos:fin]
        if tipo in (b"EXIF", b"XMP "):
            quitados += 1
        else:
            if tipo == b"VP8X":
                flags = bloque[8] & ~0x0C          # apaga los indicadores EXIF (0x08) y XMP (0x04)
                bloque = bloque[:8] + bytes([flags]) + bloque[9:]
            partes.append(bloque)
        pos = fin
    cuerpo = b"WEBP" + b"".join(partes)
    return b"RIFF" + struct.pack("<I", len(cuerpo)) + cuerpo, quitados


def cargar_proyectos(ruta_csv):
    proyectos = []
    with open(ruta_csv, encoding="utf-8-sig") as f:
        for r in csv.reader(f, delimiter=";"):
            if not r or r[0] == "id":
                continue
            cats = [c.strip() for c in r[3].replace("/", ",").split(",") if c.strip()]
            proyectos.append({"id": r[0], "guia": r[1], "loc": r[2], "tipo": cats[0] if cats else "", "clave": norm(r[1])})
    # los nombres más largos primero (evita que «DANI» coincida con «DANI ZENITH»)
    return sorted(proyectos, key=lambda p: -len(p["clave"]))


def buscar(nombre, proyectos):
    n = norm(nombre)
    for p in proyectos:
        if p["clave"] and p["clave"] in n:
            return p
    return None


def imagenes_de(ruta):
    if os.path.isdir(ruta):
        return [os.path.join(r, f) for r, _, fs in os.walk(ruta) for f in fs if f.lower().endswith(EXT)]
    return [ruta] if ruta.lower().endswith(EXT) else []


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    netejar = "--netejar-metadades" in sys.argv
    if len(args) < 2:
        sys.exit(__doc__)
    origen, ruta_csv = args[0], args[1]
    proyectos = cargar_proyectos(ruta_csv)
    por_id, sin_clasificar = {}, []
    for nombre in sorted(os.listdir(origen), key=natural):
        ruta = os.path.join(origen, nombre)
        archivos = imagenes_de(ruta)
        if not archivos:
            continue
        p = buscar(nombre, proyectos)
        if not p:
            sin_clasificar.append(nombre)
            continue
        por_id.setdefault(p["id"], {"p": p, "files": []})["files"] += sorted(archivos, key=natural)
    shutil.rmtree(SALIDA, ignore_errors=True)
    os.makedirs(SALIDA)
    alt, claves, quitados_total = [], [], 0
    for pid in sorted(por_id):
        p, files = por_id[pid]["p"], por_id[pid]["files"]
        tipo = slug(p["tipo"]) or "projecte"
        loc = slug(p["loc"])
        base = "-".join(x for x in (tipo, loc) if x)
        carpeta = os.path.join(SALIDA, f"{pid}-{base}")
        os.makedirs(carpeta, exist_ok=True)
        for n, src in enumerate(files, 1):
            ext = os.path.splitext(src)[1].lower().replace(".jpeg", ".jpg")
            nuevo = f"{base}-{pid}-{n:02d}{ext}"
            datos = open(src, "rb").read()
            if netejar and ext == ".webp":
                datos, q = quitar_metadatos_webp(datos)
                quitados_total += q
            open(os.path.join(carpeta, nuevo), "wb").write(datos)
            texto = f"{(p['tipo'] or 'Projecte')} a {p['loc']}".strip() if p["loc"] else (p["tipo"] or "Projecte")
            alt.append([nuevo, f"{texto} - Creem Llar", texto])
            claves.append([pid, p["guia"], os.path.basename(src), nuevo])
        print(f"{pid} {base:34} {len(files):3} fotos")
    with open(os.path.join(os.path.dirname(SALIDA), "textos-alt.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";"); w.writerow(["archivo", "texto alternativo (ALT)", "titulo sugerido"]); w.writerows(alt)
    with open(os.path.join(os.path.dirname(SALIDA), "CLAVES-PRIVADAS.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";"); w.writerow(["id", "cliente (PRIVADO)", "archivo original", "archivo nuevo"]); w.writerows(claves)
    print(f"\nListo: {len(claves)} fotos en {SALIDA}")
    if netejar:
        print(f"Metadatos eliminados (EXIF/XMP) en {quitados_total} bloques.")
    if sin_clasificar:
        print("\nNo se encontró proyecto para estas carpetas/archivos (revisa el nombre en projectes.csv):")
        for n in sin_clasificar:
            print("  -", n)
    print("\nIMPORTANTE: CLAVES-PRIVADAS.csv contiene nombres de clientes. No lo subas a WordPress ni a GitHub.")


if __name__ == "__main__":
    main()
