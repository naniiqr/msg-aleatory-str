#!/usr/bin/env python3
"""
Proposa la categoria de cada projecte mirant NOMÉS els noms de les carpetes, zips i fitxers
(no puja ni llegeix les fotos). Pensat per córrer al teu PC amb la carpeta original.

Ús:  python classificar_projectes.py "C:\\...\\creem llar"
Resultat: classificacio_proposta.csv (s'obre amb Excel). Revisa-la i envia'm el CSV (pesa pocs KB).
Els .zip es llegeixen; els .rar s'han d'extreure abans amb WinRAR.
"""
import csv, os, re, sys, unicodedata, zipfile

PISTES = {
    "Cuina": ["cuina", "cuines", "cocina", "kitchen", "isla", "illa", "campana", "forn"],
    "Banys": ["bany", "banys", "baño", "banos", "bath", "dutxa", "ducha", "lavabo", "mampara"],
    "Parquets": ["parquet", "tarima", "paviment", "sol laminat", "laminat", "suelo"],
    "Reformes": ["reforma", "reformes", "obra", "enderroc", "rehabilit"],
    "Interiorisme": ["interior", "saló", "salo", "menjador", "comedor", "dormitori", "habitacio", "despatx",
                     "oficina", "local", "bar", "botiga", "tienda", "restaurant", "camping"],
}


def norm(t):
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()


def noms_interns(ruta):
    if os.path.isdir(ruta):
        return [os.path.join(r, f) for r, ds, fs in os.walk(ruta) for f in ds + fs]
    if ruta.lower().endswith(".zip"):
        try:
            return zipfile.ZipFile(ruta).namelist()
        except zipfile.BadZipFile:
            return []
    return []


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    origen = sys.argv[1]
    sortida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "classificacio_proposta.csv")
    files = []
    for nom in sorted(os.listdir(origen)):
        ruta = os.path.join(origen, nom)
        text = norm(" ".join([nom] + noms_interns(ruta)))
        trobades = {}
        for cat, paraules in PISTES.items():
            hits = sorted({p for p in paraules if re.search(r"(?<![a-z])" + re.escape(p), text)})
            if hits:
                trobades[cat] = hits
        proposta = max(trobades, key=lambda c: len(trobades[c])) if trobades else ""
        pistes = "; ".join(f"{c}: {', '.join(h)}" for c, h in trobades.items())
        files.append([nom, proposta, pistes])
        print(f"{nom[:50]:50} -> {proposta or '(sense pistes)'}")
    with open(sortida, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["carpeta o arxiu", "categoria proposada", "pistes trobades", "categoria definitiva (omple-la tu)"])
        w.writerows([r + [""] for r in files])
    print("\nGuardat a", sortida)


if __name__ == "__main__":
    main()
