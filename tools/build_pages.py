#!/usr/bin/env python3
"""Genera les plantilles Elementor (JSON) de Caravaning Vilamacolum.

Ús:  python3 tools/build_pages.py   ->  escriu els fitxers a ./elementor/
Pàgines: Elementor > Plantilles > Plantilles desades > Importa.
Header/Footer: Elementor Pro > Theme Builder > Importa (types header / footer).
"""
import hashlib
import json
import os

NAVY, LIGHT, TEXT, WHITE = "#061C49", "#F3F7FA", "#526078", "#FFFFFF"
FONT = "Montserrat"
UP = "https://proveswebsfigueres.com/caravaningvilamacolum/wp-content/uploads/2026/10/"

# Només les imatges que ja són a la mediateca. La resta queden com a placeholder.
IMG = {
    "aeria": (UP + "vista_aerea.webp", 18),
    "coberts": (UP + "places_cobertes.webp", 19),
    "exterior": (UP + "zona_exterior.webp", 20),
    "panoramica": (UP + "vista_aerea_panoramica.webp", 25),
}
ADDR = "Ctra. Figueres a la Bisbal, Km 28 · 17474 Vilamacolum · Girona"
TEL, MAIL = "677 858 096", "masfont@caravanvilamacolum.es"
MAPS = "https://www.google.com/maps/search/?api=1&query=Caravaning+Vilamacolum"

_n = 0


def _id():
    global _n
    _n += 1
    return hashlib.md5(str(_n).encode()).hexdigest()[:8]


def px(n):
    return {"unit": "px", "size": n}


def pad(t, r=None, b=None, l=None):
    r = t if r is None else r
    b = t if b is None else b
    l = r if l is None else l
    return {"unit": "px", "top": t, "right": r, "bottom": b, "left": l, "isLinked": False}


def img(key):
    if not key:
        return {"url": "", "id": ""}
    url, i = IMG[key]
    return {"url": url, "id": i, "size": "", "alt": "", "source": "library"}


def widget(kind, settings):
    return {"id": _id(), "settings": settings, "elements": [], "isInner": False,
            "widgetType": kind, "elType": "widget"}


# ------------------------------------------------------------ contenidors
def box(children, *, width=None, row=False, bg=None, padding=None, gap=16, boxed=False,
        inner=True, align=None, justify=None, radius=None, bg_image=None, overlay=None,
        min_h=None, css=None, mob=None, center=False, align_mobile=None, shadow=False):
    s = {"content_width": "boxed" if boxed else "full",
         "flex_direction": "row" if row else "column",
         "flex_gap": {"unit": "px", "size": gap, "column": str(gap), "row": str(gap), "isLinked": True}}
    if boxed:
        s["boxed_width"] = px(1200)
    if width:
        s["width"] = {"unit": "%", "size": width}
    if padding is not None:
        s["padding"] = padding
    if bg:
        s["background_background"] = "classic"
        s["background_color"] = bg
    if bg_image:
        s["background_background"] = "classic"
        s["background_image"] = img(bg_image)
        s["background_position"] = "center center"
        s["background_size"] = "cover"
    if overlay:
        s["background_overlay_background"] = "classic"
        s["background_overlay_color"] = NAVY
        s["background_overlay_opacity"] = {"unit": "px", "size": overlay, "sizes": []}
    if min_h:
        s["min_height"] = px(min_h)
        s["min_height_mobile"] = px(int(min_h * 0.75))
    if align:
        s["align_items"] = align
    if align_mobile:
        s["align_items_mobile"] = align_mobile
    if justify:
        s["justify_content"] = justify
    if radius:
        s["border_radius"] = {"unit": "px", "top": radius, "right": radius, "bottom": radius,
                              "left": radius, "isLinked": True}
    if shadow:
        s["box_shadow_box_shadow_type"] = "yes"
        s["box_shadow_box_shadow"] = {"horizontal": 0, "vertical": 4, "blur": 18, "spread": 0,
                                      "color": "rgba(6,28,73,0.08)"}
    if css:
        s["_css_classes"] = css
    if mob:
        s["_mob"] = mob
    if center:
        s["_center"] = True
    return {"id": _id(), "settings": s, "elements": children, "isInner": inner, "elType": "container"}


def section(children, **kw):
    kw.setdefault("boxed", True)
    kw.setdefault("row", True)
    kw.setdefault("inner", False)
    kw.setdefault("padding", pad(48, 24))
    kw.setdefault("gap", 20)
    return box(children, **kw)


def finalize(node):
    """Aplica responsive i alineació de manera uniforme a tot l'arbre."""
    if node["elType"] != "container":
        return node
    s = node["settings"]
    mob = s.pop("_mob", None)
    center = s.pop("_center", False)
    kids = node["elements"]
    if center:
        s["align_items"] = "center"
        for k in kids:
            if k["elType"] == "widget":
                k["settings"]["align"] = "center"
    # padding escalat per tablet / mòbil
    if "padding" in s:
        t, r = s["padding"]["top"], s["padding"]["right"]
        b = s["padding"]["bottom"]
        s["padding_tablet"] = pad(min(t, 44), min(r, 24), min(b, 44))
        s["padding_mobile"] = pad(min(t, 32), min(r, 16), min(b, 32))
    if s["flex_direction"] == "row":
        cont = [k for k in kids if k["elType"] == "container"]
        if not cont:
            s["flex_wrap"] = "wrap"
        else:
            s["flex_wrap"] = "nowrap"
            sized = [k for k in cont if "width" in k["settings"]]
            narrow = [k for k in sized if k["settings"]["width"]["size"] < 90]
            n = len(narrow)
            if sized:
                s["flex_wrap_tablet"] = "wrap"
                s["flex_wrap_mobile"] = "wrap"
            if n >= 3:
                s["justify_content_tablet"] = "center"
                s["justify_content_mobile"] = "center"
            for k in sized:
                w = k["settings"]["width"]["size"]
                uneven = n == 3 and len({x["settings"]["width"]["size"] for x in narrow}) > 1
                if w >= 90 or n <= 2 or (uneven and k is narrow[0]):
                    tw = 100
                elif uneven:
                    tw = 47
                else:
                    tw = 30 if n in (3, 5) else 47
                mw = 46 if (mob == 2 and w < 90) else 100
                k["settings"]["width_tablet"] = {"unit": "%", "size": tw}
                k["settings"]["width_mobile"] = {"unit": "%", "size": mw}
    for k in kids:
        finalize(k)
    return node


# ---------------------------------------------------------------- widgets
def eyebrow(text, color=NAVY):
    return widget("heading", {
        "title": text.upper(), "header_size": "h6", "title_color": color,
        "typography_typography": "custom", "typography_font_family": FONT,
        "typography_font_size": px(12), "typography_font_weight": "700",
        "typography_letter_spacing": px(2)})


def h(text, size=30, color=NAVY, tag="h2", align=None):
    s = {"title": text, "header_size": tag, "title_color": color,
         "typography_typography": "custom", "typography_font_family": FONT,
         "typography_font_size": px(size), "typography_font_weight": "700",
         "typography_line_height": {"unit": "em", "size": 1.2},
         "typography_font_size_tablet": px(max(20, int(size * 0.82))),
         "typography_font_size_mobile": px(max(18, int(size * 0.66)))}
    if align:
        s["align"] = align
    return widget("heading", s)


def p(text, color=TEXT, size=15, align=None):
    s = {"editor": f"<p>{text}</p>", "text_color": color,
         "typography_typography": "custom", "typography_font_family": FONT,
         "typography_font_size": px(size),
         "typography_line_height": {"unit": "em", "size": 1.6}}
    if align:
        s["align"] = align
    return widget("text-editor", s)


def btn(text, url, *, light=False, outline=False, icon_cls="fas fa-arrow-right"):
    s = {"text": text, "link": {"url": url}, "size": "md",
         "typography_typography": "custom", "typography_font_family": FONT,
         "typography_font_weight": "600", "typography_font_size": px(13),
         "border_radius": {"unit": "px", "top": 6, "right": 6, "bottom": 6, "left": 6, "isLinked": True},
         "button_text_color": NAVY if light else WHITE,
         "background_color": WHITE if light else NAVY,
         "text_padding": pad(14, 22), "align_mobile": "stretch"}
    if icon_cls:
        s["selected_icon"] = {"value": icon_cls, "library": "fa-solid"}
        s["icon_align"] = "row-reverse"
        s["icon_indent"] = px(8)
    if outline:
        s.update({"background_color": "rgba(255,255,255,0)", "button_text_color": WHITE,
                  "border_border": "solid",
                  "border_width": {"unit": "px", "top": "1", "right": "1", "bottom": "1",
                                  "left": "1", "isLinked": True},
                  "border_color": WHITE})
    return widget("button", s)


def btn_row(buttons):
    return box(buttons, row=True, gap=14)


def image(key, height=260):
    return widget("image", {
        "image": img(key), "image_size": "full",
        "width": {"unit": "%", "size": 100},
        "height": px(height), "height_tablet": px(int(height * 0.9)),
        "height_mobile": px(int(height * 0.75)), "object-fit": "cover",
        "image_border_radius": {"unit": "px", "top": 8, "right": 8, "bottom": 8, "left": 8,
                                "isLinked": True}})


def checklist(items):
    return widget("icon-list", {
        "icon_list": [{"text": t, "selected_icon": {"value": "fas fa-check-circle", "library": "fa-solid"},
                       "_id": _id()} for t in items],
        "space_between": px(8), "icon_color": NAVY, "icon_size": px(14), "text_color": TEXT,
        "text_indent": px(10),
        "icon_typography_typography": "custom", "icon_typography_font_family": FONT,
        "icon_typography_font_size": px(14)})


def icon(cls, size=34):
    return widget("icon", {"selected_icon": {"value": cls, "library": "fa-solid"},
                           "primary_color": NAVY, "size": px(size), "align": "left"})


def gallery(keys):
    return widget("image-gallery", {
        "wp_gallery": [{"id": IMG[k][1], "url": IMG[k][0]} for k in keys],
        "gallery_columns": "3", "gallery_columns_tablet": "2", "gallery_columns_mobile": "1",
        "gallery_link": "file", "thumbnail_size": "large", "gap": px(12)})


def map_block():
    return widget("google_maps", {"address": "Caravaning Vilamacolum, Vilamacolum, Girona",
                                  "zoom": {"unit": "px", "size": 13},
                                  "height": px(340), "height_mobile": px(260)})


def info_lines(color=NAVY):
    return [p(f"<strong>Caravaning Vilamacolum – Mas Font</strong><br>{ADDR}", color),
            p(f'<a href="tel:+34677858096" style="color:inherit">{TEL}</a>', color),
            p(f'<a href="mailto:{MAIL}" style="color:inherit">{MAIL}</a>', color)]


def form():
    return widget("form", {
        "form_name": "Contacte Caravaning Vilamacolum",
        "form_fields": [
            {"field_type": "text", "field_label": "Nom", "placeholder": "Nom", "required": "true",
             "_id": "nom", "css_classes": "", "width": "50", "width_mobile": "100"},
            {"field_type": "tel", "field_label": "Telèfon", "placeholder": "Telèfon", "required": "true",
             "_id": "telefon", "width": "50", "width_mobile": "100"},
            {"field_type": "email", "field_label": "Email", "placeholder": "Email", "required": "true",
             "_id": "email", "width": "100"},
            {"field_type": "select", "field_label": "Tipus de vehicle",
             "field_options": "Caravana\nAutocaravana\nRemolc\nAltres", "_id": "vehicle", "width": "100"},
            {"field_type": "textarea", "field_label": "Missatge", "placeholder": "Missatge",
             "_id": "missatge", "width": "100"},
            {"field_type": "acceptance", "field_label": "Accepto la política de privacitat",
             "required": "true", "_id": "privacitat", "width": "100"}],
        "show_labels": "", "button_text": "SOL·LICITAR INFORMACIÓ", "button_width": "100",
        "button_background_color": NAVY, "button_text_color": WHITE,
        "submit_actions": ["email"], "email_subject": "Nova consulta - Caravaning Vilamacolum",
        "email_content": "[all-fields]",
        "success_message": "Gràcies! Hem rebut la teva consulta.",
        "error_message": "S'ha produït un error. Torna-ho a provar.",
        "server_message": "Error del servidor. Torna-ho a provar.",
        "invalid_message": "El formulari no és vàlid.",
        "required_field_message": "Aquest camp és obligatori."})


# --------------------------------------------------------------- blocs
def stat(ic, title, sub, width):
    return box([icon(ic, 28), h(title, 14, tag="h4"), p(sub, size=12)],
               width=width, padding=pad(16), gap=6, bg=LIGHT, radius=8, center=True,
               justify="center")


def stats_row(items):
    w = 100 // len(items)
    return section([stat(*i, w) for i in items], bg=WHITE, padding=pad(20, 24), mob=2)


def hero(eyebrow_t, title, text, buttons, bg="aeria", min_h=460):
    return section(
        [box([eyebrow(eyebrow_t, WHITE), h(title, 46, WHITE, "h1"), p(text, WHITE, 16),
              btn_row(buttons)], width=62, gap=18)],
        bg_image=bg, overlay=0.5, min_h=min_h, padding=pad(70, 24), align="center")


def head(eyebrow_t, title, text=None, button=None, bg=LIGHT):
    left = [eyebrow(eyebrow_t), h(title)] + ([p(text)] if text else [])
    if button:
        return section([box(left, width=70), box([button], width=30, align="flex-end",
                                                 align_mobile="flex-start", justify="center")],
                       bg=bg, padding=pad(48, 24, 0), align="center")
    return section([box(left, width=100)], bg=bg, padding=pad(48, 24, 0))


def grid(cards, bg=LIGHT, mob=None, bottom=48):
    return section(cards, bg=bg, padding=pad(24, 24, bottom), mob=mob)


def card(children, width, **kw):
    return box(children, width=width, bg=WHITE, padding=pad(20), gap=14, radius=8, shadow=True, **kw)


def icon_card(ic, title, text, width, size=40, tsize=18, center=False):
    return card([icon(ic, size), h(title, tsize, tag="h3"), p(text, size=13)], width, center=center)


def cta(eyebrow_t, title, label="CONTACTA ARA", url="/contacte/"):
    return section(
        [box([eyebrow(eyebrow_t, WHITE), h(title, 32, WHITE)], width=65),
         box([btn(label, url, light=True)], width=35, align="flex-end", align_mobile="flex-start",
             justify="center")],
        bg=NAVY, padding=pad(50, 24), align="center")


def contact_block(title="Busques un lloc per a la teva caravana?"):
    sec = section(
        [box([eyebrow("Contacte", WHITE), h(title, 30, WHITE),
              p("Explica'ns què necessites i t'informarem sobre disponibilitat i serveis.", WHITE)],
             width=40, justify="center"),
         box([form()], width=60, padding=pad(24), bg=WHITE, radius=10)],
        bg=NAVY, padding=pad(50, 24), align="center")
    sec["settings"]["_element_id"] = "contacte"
    return sec


# ---------------------------------------------------------------- pàgines
def page_inici():
    return [
        hero("Caravaning Vilamacolum", "La teva caravana, sempre en bones mans",
             "Parking i cura de caravanes a Vilamacolum, en ple Alt Empordà.",
             [btn("SOL·LICITAR PLAÇA", "#contacte", light=True),
              btn("VEURE INSTAL·LACIONS", "/installacions/", outline=True, icon_cls=None)],
             bg="aeria", min_h=520),
        stats_row([("fas fa-vector-square", "12.000 m²", "d'instal·lacions"),
                   ("fas fa-home", "PLACES COBERTES", "i exteriors"),
                   ("fas fa-shield-alt", "VIGILÀNCIA", "per a la teva tranquil·litat"),
                   ("fas fa-wrench", "MANTENIMENT", "i reparacions"),
                   ("fas fa-tint", "NETEJA", "per tenir-la sempre a punt")]),
        section([
            box([eyebrow("Molt més que un parking"), h("Un espai pensat per a la teva tranquil·litat"),
                 p("A Caravaning Vilamacolum t'oferim un espai ampli, segur i ben equipat per guardar "
                   "la teva caravana durant tot l'any, amb serveis de manteniment, neteja i reparacions."),
                 btn("DESCOBREIX ELS NOSTRES SERVEIS", "/serveis/")], width=40, justify="center"),
            card([image("coberts", 240), h("Parking cobert", 23, tag="h3"),
                  p("Protecció durant tot l'any.")], 30),
            card([image("exterior", 240), h("Parking exterior", 23, tag="h3"),
                  p("Amples zones per a caravanes i altres vehicles.")], 30),
        ], bg=LIGHT, padding=pad(40, 24), align="stretch"),
        head("Els nostres serveis", "Ens ocupem de la teva caravana"),
        grid([icon_card("fas fa-parking", "Parking", "Espais amplis, còmodes i segurs.", 25, 34, 23),
              icon_card("fas fa-tint", "Neteja",
                        "La preparem perquè estigui llesta per a les teves properes vacances.", 25, 34, 23),
              icon_card("fas fa-wrench", "Manteniment",
                        "Revisió i manteniment per conservar-la en les millors condicions.", 25, 34, 23),
              icon_card("fas fa-cog", "Reparacions",
                        "Solucions per a petites reparacions i posada a punt.", 25, 34, 23)]),
        section([box([image("panoramica", 340)], width=55),
                 box([eyebrow("Tranquil·litat tot l'any", WHITE),
                      h("Tu gaudeix del viatge. Nosaltres cuidem de la teva caravana.", 40, WHITE),
                      btn("SOL·LICITAR INFORMACIÓ", "#contacte", light=True)],
                     width=45, gap=18, justify="center")],
                bg=NAVY, padding=pad(40, 24), align="center"),
        section([box([eyebrow("Ubicació"), h("En un punt estratègic de l'Alt Empordà"),
                      p("Caravaning Vilamacolum està situat a Vilamacolum, molt a prop de Sant Pere "
                        "Pescador i de les principals zones de la Costa Brava, amb fàcil accés des de "
                        "Figueres i la resta de la comarca.")] + info_lines(), width=45,
                     justify="center"),
                 box([map_block(), btn("VEURE UBICACIÓ", MAPS)], width=55, bg=LIGHT, padding=pad(20),
                     radius=8)],
                bg=WHITE, padding=pad(48, 24), align="center"),
        contact_block(),
    ]


def page_parking():
    def col(key, title, items, label):
        return card([image(key, 300), h(title, 24, tag="h3"), checklist(items),
                     btn(label, "/contacte/")], 50, justify="space-between")
    return [
        hero("Parking de caravanes", "Un espai segur per a la teva caravana",
             "A Caravaning Vilamacolum posem a la teva disposició un ampli espai amb places cobertes i "
             "exteriors perquè la teva caravana estigui sempre protegida i llesta per a la teva "
             "pròxima aventura.",
             [btn("SOL·LICITAR PLAÇA", "/contacte/", light=True),
              btn("VEURE INSTAL·LACIONS", "/installacions/", outline=True, icon_cls=None)],
             bg="coberts"),
        stats_row([("fas fa-vector-square", "12.000 m²", "d'instal·lacions"),
                   ("fas fa-home", "PLACES COBERTES", "i exteriors"),
                   ("fas fa-shield-alt", "VIGILÀNCIA", "24 hores"),
                   ("fas fa-video", "ACCÉS CONTROLAT", "i tancat perimetralment")]),
        section([box([eyebrow("Dos tipus de places"), h("Parking cobert i exterior"),
                      p("Oferim solucions adaptades a les teves necessitats amb places cobertes i "
                        "exteriors, totes dins d'un recinte tancat, vigilat i amb fàcil accés durant tot l'any.")],
                     width=58, justify="center"),
                 box([icon("fas fa-parking", 40), h("Espais amplis i còmodes", 18, tag="h3"),
                      p("Dissenyats per a tot tipus de caravanes, autocaravanes i altres vehicles d'oci.",
                        size=13)], width=42, bg="#E8EFF7", padding=pad(22), radius=8)],
                bg=LIGHT, padding=pad(48, 24, 0), align="center"),
        grid([col("coberts", "Parking cobert",
                  ["Protecció davant del sol, la pluja i les inclemències del temps",
                   "Manté la teva caravana en les millors condicions",
                   "Ideal per a estades de llarga durada", "Accés fàcil i ampli"],
                  "SOL·LICITAR PLAÇA COBERTA"),
              col("exterior", "Parking exterior",
                  ["Zones àmplies i ben delimitades", "Bona maniobrabilitat",
                   "Espais per a caravanes, autocaravanes i remolcs", "Entorn tranquil i segur"],
                  "SOL·LICITAR PLAÇA EXTERIOR")]),
        section([box([eyebrow("12.000 m²", WHITE), h("12.000 m²", 44, WHITE),
                      h("dedicats a la teva tranquil·litat", 22, WHITE, "h3"),
                      p("Un gran espai, ben organitzat i equipat, per garantir la seguretat i el bon "
                        "estat de la teva caravana durant tot l'any.", WHITE)], width=50)],
                bg_image="panoramica", overlay=0.45, min_h=380, padding=pad(60, 24), align="center"),
        head("Per què triar-nos", "Màxima seguretat i comoditat"),
        grid([icon_card("fas fa-shield-alt", "Vigilància 24 hores", "Recinte tancat amb control d'accessos.", 25, center=True),
              icon_card("fas fa-video", "Entorn segur", "Càmeres de seguretat i il·luminació.", 25, center=True),
              icon_card("fas fa-map-marker-alt", "Fàcil accés", "Accés ampli per a tot tipus de vehicles.", 25, center=True),
              icon_card("fas fa-cog", "Servei addicional", "Neteja, manteniment i reparacions.", 25, center=True)]),
        head("Galeria", "Les nostres instal·lacions",
             button=btn("VEURE TOTES LES IMATGES", "/installacions/", outline=True), bg=WHITE),
        section([box([gallery(["coberts", "exterior", "aeria", "panoramica"])], width=100)],
                bg=WHITE, padding=pad(24, 24, 48)),
        cta("Busques una plaça per a la teva caravana?", "Sol·licita informació sense compromís"),
    ]


def page_serveis():
    def svc(ic, title, intro, items, key):
        return card([image(key, 190),
                     box([icon(ic, 24), h(title, 22, tag="h3")], row=True, gap=10, align="center"),
                     p(intro, size=14), checklist(items), btn("MÉS INFORMACIÓ", "/contacte/")],
                    25, justify="space-between")
    return [
        hero("Els nostres serveis", "Tot el que la teva caravana necessita",
             "A Caravaning Vilamacolum t'oferim molt més que un parking. Ens ocupem del manteniment, "
             "la neteja i les reparacions perquè la teva caravana estigui sempre a punt per gaudir de "
             "la pròxima escapada.",
             [btn("SOL·LICITAR INFORMACIÓ", "/contacte/", light=True),
              btn("VEURE INSTAL·LACIONS", "/installacions/", outline=True, icon_cls=None)],
             bg="exterior"),
        stats_row([("fas fa-wrench", "MANTENIMENT", "i revisions"),
                   ("fas fa-tint", "NETEJA", "interior i exterior"),
                   ("fas fa-cog", "REPARACIONS", "petites i mitjanes"),
                   ("fas fa-shield-alt", "TOT EN UN SOL LLOC", "professional i de confiança")]),
        head("Els nostres serveis", "Ens ocupem de la teva caravana",
             "Oferim un servei complet per mantenir la teva caravana en perfectes condicions "
             "durant tot l'any. Qualitat, experiència i un tracte proper."),
        grid([svc("fas fa-parking", "Parking", "Places cobertes i exteriors en un entorn segur i vigilat.",
                  ["Places cobertes i exteriors", "Accés fàcil i ampli", "Vigilància 24 hores",
                   "Ideal per estades llargues"], "coberts"),
              svc("fas fa-tint", "Neteja", "Neteja interior i exterior per tenir la teva caravana sempre a punt.",
                  ["Neteja exterior de carrosseria", "Neteja interior completa",
                   "Tractament de plàstics i gomes", "Preparació per a noves vacances"], None),
              svc("fas fa-cog", "Manteniment",
                  "Revisions periòdiques per garantir la seguretat i el bon estat del teu vehicle.",
                  ["Revisió general", "Control d'instal·lacions", "Bateria, pneumàtics i frens",
                   "Consells personalitzats"], None),
              svc("fas fa-wrench", "Reparacions", "Solucions per a petites i mitjanes reparacions.",
                  ["Electricitat i il·luminació", "Aigua i sanejament", "Substitució de peces",
                   "Posada a punt abans de viatjar"], None)]),
        section([box([image("exterior", 320)], width=45),
                 box([h("Viatja amb tranquil·litat"),
                      p("Confia la teva caravana a un equip amb experiència. Nosaltres ens encarreguem "
                        "de mantenir-la segura, neta i en perfectes condicions."),
                      box([stat("fas fa-shield-alt", "Seguretat", "durant tot l'any", 25),
                           stat("far fa-calendar-alt", "Estalvi de temps", "i preocupacions", 25),
                           stat("far fa-check-circle", "Més durabilitat", "del teu vehicle", 25),
                           stat("fas fa-sun", "Llesta per a", "la pròxima aventura", 25)],
                          row=True, gap=10, mob=2)],
                     width=55, justify="center")],
                bg=LIGHT, padding=pad(24, 24, 48), align="center"),
        section([box([eyebrow("Un servei personalitzat"), h("Assessorament i tracte proper"),
                      p("Cada caravana és diferent, per això t'oferim un servei adaptat a les teves "
                        "necessitats. T'assessorem sobre el manteniment, la neteja i qualsevol dubte que "
                        "tinguis, amb un tracte pròxim i professional."),
                      btn("CONTACTA AMB NOSALTRES", "/contacte/")], width=50, justify="center"),
                 box([image("coberts", 320)], width=50)],
                bg=LIGHT, padding=pad(24, 24, 48), align="center"),
        head("Galeria", "Serveis en imatges",
             button=btn("VEURE TOTES LES IMATGES", "/installacions/", outline=True), bg=WHITE),
        section([box([gallery(["coberts", "exterior", "aeria", "panoramica"])], width=100)],
                bg=WHITE, padding=pad(24, 24, 48)),
        cta("Vols saber més sobre els nostres serveis?", "Sol·licita informació sense compromís",
            "SOL·LICITAR INFORMACIÓ"),
    ]


def page_installacions():
    return [
        hero("Instal·lacions", "12.000 m² pensats per a la teva caravana",
             "Un recinte ampli, ben organitzat i vigilat, amb places cobertes i exteriors a Vilamacolum.",
             [btn("SOL·LICITAR PLAÇA", "/contacte/", light=True)], bg="panoramica"),
        stats_row([("fas fa-vector-square", "12.000 m²", "d'instal·lacions"),
                   ("fas fa-home", "PLACES COBERTES", "i exteriors"),
                   ("fas fa-shield-alt", "VIGILÀNCIA", "24 hores"),
                   ("fas fa-video", "ACCÉS CONTROLAT", "i tancat perimetralment")]),
        head("Galeria", "Les nostres instal·lacions"),
        section([box([gallery(["coberts", "exterior", "aeria", "panoramica"])], width=100)],
                bg=LIGHT, padding=pad(24, 24, 48)),
        cta("Busques una plaça per a la teva caravana?", "Sol·licita informació sense compromís"),
    ]


def page_sobre():
    return [
        hero("Sobre nosaltres", "Cuidem la teva caravana com si fos nostra",
             "A Caravaning Vilamacolum (Mas Font) ens dediquem al parking i la cura de caravanes "
             "a l'Alt Empordà.", [btn("CONTACTA AMB NOSALTRES", "/contacte/", light=True)], bg="aeria"),
        section([box([eyebrow("Qui som"), h("Un equip proper i de confiança"),
                      p("[Text a revisar amb el client: història de Mas Font, anys d'experiència i valors.]")],
                     width=55, justify="center"),
                 box([image("exterior", 340)], width=45)],
                bg=WHITE, padding=pad(48, 24), align="center"),
        head("Els nostres valors", "Per què confiar en nosaltres"),
        grid([icon_card("fas fa-shield-alt", "Seguretat", "Recinte vigilat i amb accés controlat.", 33, center=True),
              icon_card("fas fa-handshake", "Tracte proper", "T'assessorem amb un servei personalitzat.", 33, center=True),
              icon_card("fas fa-tools", "Servei complet", "Parking, neteja, manteniment i reparacions.", 33, center=True)]),
        cta("Vols saber-ne més?", "Sol·licita informació sense compromís"),
    ]


def page_contacte():
    return [
        hero("Contacte", "Parlem de la teva caravana",
             "Explica'ns què necessites i t'informarem sobre disponibilitat i serveis.",
             [btn("TRUCA'NS: " + TEL, "tel:+34677858096", light=True, icon_cls="fas fa-phone")],
             bg="exterior", min_h=360),
        section([box([eyebrow("Ubicació"), h("Com arribar")] + info_lines() + [btn("VEURE UBICACIÓ", MAPS)],
                     width=40, justify="center"),
                 box([map_block()], width=60, padding=pad(20), bg=LIGHT, radius=8)],
                bg=WHITE, padding=pad(48, 24), align="center"),
        contact_block("Sol·licita informació sense compromís"),
    ]


# ------------------------------------------------- header i footer (Pro)
def header():
    logo = box([widget("theme-site-logo", {"width": px(110), "width_mobile": px(80),
                                           "link_to": "custom", "link": {"url": "/"}})])
    nav = box([widget("nav-menu", {
        "menu": "menu-principal", "layout": "horizontal", "align_items": "center",
        "pointer": "underline", "animation_line": "fade", "dropdown": "tablet", "toggle": "burger",
        "full_width": "stretch", "toggle_align": "right",
        "menu_typography_typography": "custom", "menu_typography_font_family": FONT,
        "menu_typography_font_size": px(13), "menu_typography_font_weight": "500",
        "color_menu_item": NAVY, "color_menu_item_hover": NAVY, "color_menu_item_active": NAVY,
        "pointer_color_menu_item_hover": NAVY, "pointer_color_menu_item_active": NAVY,
        "menu_space_between": px(14),
        "toggle_color": NAVY, "toggle_size": px(26),
        "color_dropdown_item": NAVY, "background_color_dropdown_item": WHITE})],
        justify="center", align="center")
    cta_btn = box([btn("SOL·LICITAR INFORMACIÓ", "/contacte/", icon_cls="far fa-calendar-alt")])
    cta_btn["settings"]["hide_mobile"] = "hidden-mobile"
    root = box([logo, nav, cta_btn], row=True, inner=False, gap=20, padding=pad(10, 24),
               bg=WHITE, justify="space-between", align="center", shadow=True)
    root["settings"]["sticky"] = "top"
    root["settings"]["sticky_on"] = ["desktop", "tablet", "mobile"]
    root["settings"]["z_index"] = 99
    return [root]


def footer():
    def link_list(items, icons=False):
        lst = []
        for t, u, ic in items:
            it = {"text": t, "link": {"url": u}, "_id": _id()}
            it["selected_icon"] = {"value": ic or "fas fa-angle-right", "library": "fa-solid"}
            lst.append(it)
        return widget("icon-list", {
            "icon_list": lst, "space_between": px(10), "icon_color": WHITE, "icon_size": px(13),
            "text_color": WHITE, "text_indent": px(10),
            "icon_typography_typography": "custom", "icon_typography_font_family": FONT,
            "icon_typography_font_size": px(14)})
    top = section([
        box([h("Caravaning Vilamacolum", 22, WHITE, "h3"),
             p("Parking i cura de caravanes a Vilamacolum, en ple Alt Empordà.", WHITE, 14)], width=36),
        box([h("Enllaços", 16, WHITE, "h4"),
             link_list([("Inici", "/", None), ("Parking", "/parking/", None), ("Serveis", "/serveis/", None),
                        ("Instal·lacions", "/installacions/", None),
                        ("Sobre nosaltres", "/sobre-nosaltres/", None),
                        ("Contacte", "/contacte/", None)])], width=28),
        box([h("Contacte", 16, WHITE, "h4"),
             link_list([(ADDR, MAPS, "fas fa-map-marker-alt"), (TEL, "tel:+34677858096", "fas fa-phone"),
                        (MAIL, "mailto:" + MAIL, "fas fa-envelope")])], width=36)],
        bg=NAVY, padding=pad(50, 24, 30), gap=30)
    bottom = section([
        box([p("© 2026 Caravaning Vilamacolum. Tots els drets reservats.", "#C5D0E6", 13)], width=60),
        box([widget("text-editor", {
            "editor": '<p><a href="/politica-de-privacitat/" style="color:inherit">Política de privacitat</a></p>',
            "text_color": "#C5D0E6", "align": "right", "align_mobile": "left",
            "typography_typography": "custom", "typography_font_family": FONT,
            "typography_font_size": px(13)})], width=40)],
        bg=NAVY, padding=pad(18, 24), align="center")
    bottom["settings"]["border_border"] = "solid"
    bottom["settings"]["border_width"] = {"unit": "px", "top": "1", "right": "0", "bottom": "0",
                                          "left": "0", "isLinked": False}
    bottom["settings"]["border_color"] = "rgba(255,255,255,0.18)"
    return [top, bottom]


PAGES = {"inici": ("page", page_inici), "parking": ("page", page_parking),
         "serveis": ("page", page_serveis), "installacions": ("page", page_installacions),
         "sobre-nosaltres": ("page", page_sobre), "contacte": ("page", page_contacte),
         "header": ("header", header), "footer": ("footer", footer)}


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "elementor")
    os.makedirs(out, exist_ok=True)
    for slug, (kind, fn) in PAGES.items():
        content = [finalize(c) for c in fn()]
        doc = {"content": content, "page_settings": [], "version": "0.4",
               "title": slug.replace("-", " ").title(), "type": kind}
        path = os.path.join(out, f"{slug}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
        print("escrit", os.path.normpath(path))


if __name__ == "__main__":
    main()
