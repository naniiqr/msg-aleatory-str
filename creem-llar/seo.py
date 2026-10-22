#!/usr/bin/env python3
"""Fitxa SEO Creem Llar (Yoast SEO). Valida: títol i descripció comencen per la keyphrase,
longituds dins dels marges de Yoast i amplada del títol en píxels (Arial 20px)."""
from PIL import ImageFont
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
import re, sys

FONT = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 20)
PAGES = [
 ("Inici", "/", "estudi d'interiorisme a Figueres",
  "Estudi d'interiorisme a Figueres | Cuines, banys i reformes",
  "Estudi d'interiorisme a Figueres i Banyoles: dissenyem cuines, banys, reformes i parquets a mida per crear llars úniques. Demana pressupost."),
 ("Projectes", "/projectes/", "projectes d'interiorisme a l'Empordà",
  "Projectes d'interiorisme a l'Empordà | Creem Llar Figueres",
  "Projectes d'interiorisme a l'Empordà i el Pla de l'Estany: cuines, banys, reformes i parquets a Figueres, Banyoles i més. Descobreix el nostre treball."),
 ("Cuines", "/cuines/", "cuines a Figueres",
  "Cuines a Figueres | Disseny a mida i muntatge – Creem Llar",
  "Cuines a Figueres i Banyoles: dissenys a mida funcionals i elegants per al teu dia a dia, amb materials de qualitat i acompanyament. Demana pressupost."),
 ("Banys", "/banys/", "banys a Banyoles",
  "Banys a Banyoles | Reformes de banys a mida – Creem Llar",
  "Banys a Banyoles i Figueres: reformes d'espais moderns, còmodes i plens de benestar, amb disseny a mida i garantia. Explica'ns la teva idea."),
 ("Interiorisme", "/interiorisme/", "disseny d'interiors a Banyoles",
  "Disseny d'interiors a Banyoles | Creem Llar Figueres",
  "Disseny d'interiors a Banyoles i Figueres per a cada estil de vida: combinem estètica, funcionalitat i benestar. Parla amb el nostre equip d'interioristes."),
 ("Parquets", "/parquets/", "parquets a Figueres",
  "Parquets a Figueres | Paviments càlids – Creem Llar",
  "Parquets a Figueres i Banyoles: paviments càlids i duradors per a la teva llar, amb assessorament i col·locació professional. Demana pressupost."),
 ("Nosaltres", "/nosaltres/", "equip d'interioristes a Figueres",
  "Equip d'interioristes a Figueres | Qui som – Creem Llar",
  "Equip d'interioristes a Figueres: Carlos, Xavi i Samuel lideren un equip de professionals que dissenya i executa espais per viure, fins a l'últim detall."),
 ("Projecte (exemple de plantilla)", "/projecte/", "cuina contemporània a Figueres",
  "Cuina contemporània a Figueres | Projecte – Creem Llar",
  "Cuina contemporània a Figueres: una cuina oberta, pràctica i amb caràcter, amb materials naturals i molta llum. Mira el projecte i demana pressupost."),
 ("Contacte", "/contacte/", "pressupost de reformes Figueres",
  "Pressupost de reformes Figueres | Contacta amb Creem Llar",
  "Pressupost de reformes Figueres i Banyoles sense compromís: truca al 972 684 896 o 972 519 324, o escriu-nos a info@creemllar.com i t'assessorem."),
]
PLACES = ("figueres", "banyoles", "empordà", "girona", "pla de l'estany")
def has_place(t): return any(p in t.lower() for p in PLACES)
T_MIN, T_MAX_PX = 400, 580
D_MIN, D_MAX = 140, 155
TC_MIN, TC_MAX = 45, 60

def px(s): return round(FONT.getlength(s))
rows, ok_all = [], True
for name, slug, kw, title, desc in PAGES:
    checks = {
      "títol comença per keyphrase": title.lower().startswith(kw.lower()),
      "descripció comença per keyphrase": desc.lower().startswith(kw.lower()),
      "títol 45-60 car.": TC_MIN <= len(title) <= TC_MAX,
      "títol dins 400-580 px": T_MIN <= px(title) <= T_MAX_PX,
      "descripció 140-155 car.": D_MIN <= len(desc) <= D_MAX,
      "keyphrase ≤ 4 paraules": len(kw.split()) <= 4,
      "lloc a la keyphrase": has_place(kw),
      "lloc al títol": has_place(title),
      "lloc a la descripció": has_place(desc),
    }
    ok_all &= all(checks.values())
    rows.append((name, slug, kw, title, len(title), px(title), desc, len(desc), checks))
    flag = "OK " if all(checks.values()) else "REVISAR"
    print(f"{flag} {name:13} títol {len(title):2} car / {px(title):3}px | desc {len(desc):3} car | kw '{kw}'",
          [k for k, v in checks.items() if not v] or "")

wb = Workbook(); ws = wb.active; ws.title = "Fitxa SEO"
head = ["Pàgina", "URL", "Keyphrase principal", "Títol SEO", "Car. títol", "Píxels títol (màx. 600)",
        "Meta descripció", "Car. descripció (120-156)", "Comença per keyphrase"]
ws.append(head)
for r in rows:
    ws.append([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7],
               "Sí" if r[8]["títol comença per keyphrase"] and r[8]["descripció comença per keyphrase"] else "NO"])
for c in ws[1]:
    c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="5B452D")
    c.alignment = Alignment(wrap_text=True, vertical="center")
for col, w in zip("ABCDEFGHI", (14, 16, 30, 52, 10, 14, 80, 14, 14)):
    ws.column_dimensions[col].width = w
for row in ws.iter_rows(min_row=2):
    for c in row: c.alignment = Alignment(wrap_text=True, vertical="top")
wb.save("output/seo-creem-llar.xlsx")

with open("output/seo-creem-llar.md", "w", encoding="utf-8") as f:
    f.write("# Fitxa SEO · Creem Llar (Yoast SEO)\n\n")
    for r in rows:
        f.write(f"## {r[0]} · `{r[1]}`\n- **Keyphrase:** {r[2]}\n- **Títol SEO** ({r[4]} car. · {r[5]} px): {r[3]}\n"
                f"- **Meta descripció** ({r[7]} car.): {r[6]}\n\n")
sys.exit(0 if ok_all else 1)
