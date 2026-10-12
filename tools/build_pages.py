#!/usr/bin/env python3
"""Genera les plantilles Elementor (JSON) de Caravaning Vilamacolum.

Ús:  python3 tools/build_pages.py   ->  escriu els fitxers a ./elementor/
Importar a WordPress: Elementor > Plantilles > Plantilles desades > Importa.
"""
import hashlib
import json
import os

NAVY, LIGHT, TEXT, WHITE = "#061C49", "#F3F7FA", "#526078", "#FFFFFF"
FONT = "Montserrat"
UP = "https://proveswebsfigueres.com/caravaningvilamacolum/wp-content/uploads/2026/10/"

# Només les imatges que ja són a la mediateca (del JSON de l'inici).
# Les altres queden com a placeholder d'Elementor fins que es pugin.
IMG = {
    "aeria": (UP + "vista_aerea.webp", 18),
    "coberts": (UP + "places_cobertes.webp", 19),
    "exterior": (UP + "zona_exterior.webp", 20),
    "panoramica": (UP + "vista_aerea_panoramica.webp", 25),
}

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


def box(children, *, width=None, row=False, bg=None, padding=None, gap=16,
        boxed=False, inner=True, align=None, justify=None, radius=None,
        bg_image=None, overlay=None, min_h=None, css=None, wrap=True, mobile_stack=True):
    s = {
        "content_width": "boxed" if boxed else "full",
        "flex_direction": "row" if row else "column",
        "flex_gap": {"unit": "px", "size": gap, "column": str(gap), "row": str(gap), "isLinked": True},
    }
    if boxed:
        s["boxed_width"] = px(1200)
    if row and wrap:
        s["flex_wrap"] = "wrap"
    if row and mobile_stack:
        s["flex_direction_mobile"] = "column"
    if width:
        s["width"] = {"unit": "%", "size": width}
        s["width_tablet"] = {"unit": "%", "size": 100 if width > 33 else 50}
        s["width_mobile"] = {"unit": "%", "size": 100}
    if padding is not None:
        s["padding"] = padding
        s["padding_mobile"] = pad(30 if padding["top"] > 30 else padding["top"], 16)
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
        s["background_overlay_opacity"] = {"unit": "px", "size": overlay}
    if min_h:
        s["min_height"] = px(min_h)
    if align:
        s["align_items"] = align
    if justify:
        s["justify_content"] = justify
    if radius:
        s["border_radius"] = {"unit": "px", "top": radius, "right": radius, "bottom": radius,
                              "left": radius, "isLinked": True}
    if css:
        s["_css_classes"] = css
    return {"id": _id(), "settings": s, "elements": children, "isInner": inner, "elType": "container"}


def section(children, **kw):
    kw.setdefault("boxed", True)
    kw.setdefault("row", True)
    kw.setdefault("inner", False)
    kw.setdefault("padding", pad(48, 24))
    kw.setdefault("gap", 20)
    return box(children, **kw)


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
         "typography_font_size_mobile": px(max(20, int(size * 0.68))),
         "typography_font_size_tablet": px(max(22, int(size * 0.82)))}
    if align:
        s["align"] = align
    return widget("heading", s)


def p(text, color=TEXT, size=15, align=None):
    s = {"editor": f"<p>{text}</p>", "text_color": color,
         "typography_typography": "custom", "typography_font_family": FONT,
         "typography_font_size": px(size)}
    if align:
        s["align"] = align
    return widget("text-editor", s)


def btn(text, url, *, light=False, outline=False):
    s = {"text": text, "link": {"url": url},
         "typography_typography": "custom", "typography_font_family": FONT,
         "typography_font_weight": "600", "typography_font_size": px(13),
         "border_radius": {"unit": "px", "top": 6, "right": 6, "bottom": 6, "left": 6, "isLinked": True},
         "button_text_color": NAVY if light else WHITE,
         "background_color": WHITE if light else NAVY}
    if outline:
        s.update({"background_color": "rgba(255,255,255,0)", "button_text_color": WHITE,
                  "border_border": "solid", "border_width": {"unit": "px", "top": "1", "right": "1",
                  "bottom": "1", "left": "1", "isLinked": True}, "border_color": WHITE})
    return widget("button", s)


def image(key, css=None, height=None):
    s = {"image": img(key), "image_size": "full"}
    if css:
        s["_css_classes"] = css
    if height:
        s["object-fit"] = "cover"
        s["height"] = px(height)
    return widget("image", s)


def checklist(items, icon="fas fa-check-circle"):
    return widget("icon-list", {
        "icon_list": [{"text": t, "selected_icon": {"value": icon, "library": "fa-solid"},
                       "_id": _id()} for t in items],
        "icon_color": NAVY, "text_color": TEXT,
        "text_typography_typography": "custom", "text_typography_font_family": FONT,
        "text_typography_font_size": px(14)})


def icon(cls, size=34):
    return widget("icon", {"selected_icon": {"value": cls, "library": "fa-solid"},
                           "primary_color": NAVY, "size": px(size), "align": "left"})


def stat(ic, title, sub, width):
    return box([icon(ic, 28), h(title, 14, tag="h4"), p(sub, size=12)],
               width=width, padding=pad(16), gap=6, bg=LIGHT, radius=8)


def hero(eyebrow_t, title, text, btns, bg="aeria", min_h=460):
    return section([box([eyebrow(eyebrow_t, WHITE), h(title, 46, WHITE, "h1"),
                         p(text, WHITE, 16), box(btns, row=True, gap=14, mobile_stack=True)],
                        width=62, gap=18)],
                   bg_image=bg, overlay=0.5, min_h=min_h, padding=pad(70, 24),
                   justify="center")


def stats_row(items):
    w = 100 // len(items)
    return section([stat(*i, w) for i in items], bg=WHITE, padding=pad(20, 24))


def cta(eyebrow_t, title, label="CONTACTA ARA", url="/contacte/"):
    return section([box([eyebrow(eyebrow_t, WHITE), h(title, 32, WHITE)], width=65),
                    box([btn(label, url, light=True)], width=35, justify="center")],
                   bg=NAVY, padding=pad(50, 24), justify="space-between")


def gallery(keys):
    return widget("image-gallery", {
        "wp_gallery": [{"id": IMG[k][1] if k in IMG else "", "url": IMG[k][0] if k in IMG else ""}
                       for k in keys],
        "gallery_columns": "3", "gallery_link": "file", "thumbnail_size": "large"})


CONTACT_FORM = lambda: widget("form", {
    "form_name": "Contacte Caravaning Vilamacolum",
    "form_fields": [
        {"field_type": "text", "field_label": "Nom", "placeholder": "Nom", "required": "true",
         "_id": "nom", "width": "50"},
        {"field_type": "tel", "field_label": "Telèfon", "placeholder": "Telèfon", "required": "true",
         "_id": "telefon", "width": "50"},
        {"field_type": "email", "field_label": "Email", "placeholder": "Email", "required": "true",
         "_id": "email"},
        {"field_type": "select", "field_label": "Tipus de vehicle",
         "field_options": "Caravana\nAutocaravana\nRemolc\nAltres", "_id": "vehicle"},
        {"field_type": "textarea", "field_label": "Missatge", "placeholder": "Missatge", "_id": "missatge"},
        {"field_type": "acceptance", "field_label": "Accepto la política de privacitat",
         "required": "true", "_id": "privacitat"}],
    "button_text": "SOL·LICITAR INFORMACIÓ", "submit_actions": ["email"],
    "email_subject": "Nova consulta - Caravaning Vilamacolum", "email_content": "[all-fields]",
    "success_message": "Gràcies! Hem rebut la teva consulta.",
    "error_message": "S'ha produït un error. Torna-ho a provar.",
    "server_message": "Error del servidor. Torna-ho a provar.",
    "invalid_message": "El formulari no és vàlid.",
    "required_field_message": "Aquest camp és obligatori."})

ADDR = "Ctra. Figueres a la Bisbal, Km 28 · 17474 Vilamacolum · Girona"
TEL, MAIL = "677 858 096", "masfont@caravanvilamacolum.es"


def contact_block(title="Busques un lloc per a la teva caravana?"):
    return section([
        box([eyebrow("Contacte", WHITE), h(title, 30, WHITE),
             p("Explica'ns què necessites i t'informarem sobre disponibilitat i serveis.", WHITE)],
            width=40),
        box([CONTACT_FORM()], width=60, padding=pad(22), bg=WHITE, radius=10)],
        bg=NAVY, padding=pad(50, 24))


def map_block():
    return widget("google_maps", {"address": "Caravaning Vilamacolum, Vilamacolum, Girona",
                                  "zoom": {"unit": "px", "size": 13},
                                  "height": px(320)})


def info_lines():
    return [p(f"<strong>Caravaning Vilamacolum – Mas Font</strong><br>{ADDR}", NAVY),
            p(f'<a href="tel:+34677858096">{TEL}</a>', NAVY),
            p(f'<a href="mailto:{MAIL}">{MAIL}</a>', NAVY)]


# ---------------------------------------------------------------- PÀGINES
def page_inici():
    return [
        hero("Caravaning Vilamacolum", "La teva caravana, sempre en bones mans",
             "Parking i cura de caravanes a Vilamacolum, en ple Alt Empordà.",
             [btn("SOL·LICITAR PLAÇA", "#contacte", light=True),
              btn("VEURE INSTAL·LACIONS", "/installacions/", outline=True)], bg="aeria", min_h=520),
        section([stat("fas fa-vector-square", "12.000 m²", "d'instal·lacions", 20),
                 stat("fas fa-home", "PLACES COBERTES", "i exteriors", 20),
                 stat("fas fa-shield-alt", "VIGILÀNCIA", "per a la teva tranquil·litat", 20),
                 stat("fas fa-wrench", "MANTENIMENT", "i reparacions", 20),
                 stat("fas fa-tint", "NETEJA", "per tenir-la sempre a punt", 20)],
                bg=WHITE, padding=pad(20, 24)),
        section([
            box([eyebrow("Molt més que un parking"), h("Un espai pensat per a la teva tranquil·litat"),
                 p("A Caravaning Vilamacolum t'oferim un espai ampli, segur i ben equipat per guardar "
                   "la teva caravana durant tot l'any, amb serveis de manteniment, neteja i reparacions."),
                 btn("DESCOBREIX ELS NOSTRES SERVEIS", "/serveis/")], width=40, padding=pad(22)),
            box([image("coberts", "foto-parking_cobert"), h("Parking cobert", 23, tag="h3"),
                 p("Protecció durant tot l'any.")], width=30, bg=WHITE, padding=pad(20)),
            box([image("exterior", "foto-parking_exterior"), h("Parking exterior", 23, tag="h3"),
                 p("Amples zones per a caravanes i altres vehicles.")], width=30, bg=WHITE, padding=pad(20)),
        ], bg=LIGHT, padding=pad(30, 24)),
        section([box([eyebrow("Els nostres serveis"), h("Ens ocupem de la teva caravana")], width=100),
                 box([icon("fas fa-parking"), h("Parking", 23, tag="h3"),
                      p("Espais amplis, còmodes i segurs.")], width=25, bg=WHITE, padding=pad(20)),
                 box([icon("fas fa-tint"), h("Neteja", 23, tag="h3"),
                      p("La preparem perquè estigui llesta per a les teves properes vacances.")],
                     width=25, bg=WHITE, padding=pad(20)),
                 box([icon("fas fa-wrench"), h("Manteniment", 23, tag="h3"),
                      p("Revisió i manteniment per conservar-la en les millors condicions.")],
                     width=25, bg=WHITE, padding=pad(20)),
                 box([icon("fas fa-cog"), h("Reparacions", 23, tag="h3"),
                      p("Solucions per a petites reparacions i posada a punt.")],
                     width=25, bg=WHITE, padding=pad(20))],
                bg=LIGHT, padding=pad(48, 24)),
        section([box([image("panoramica", "foto-vista_aeria")], width=55, padding=pad(22)),
                 box([eyebrow("Tranquil·litat tot l'any", WHITE),
                      h("Tu gaudeix del viatge. Nosaltres cuidem de la teva caravana.", 40, WHITE),
                      btn("SOL·LICITAR INFORMACIÓ", "#contacte", light=True)],
                     width=45, padding=pad(22), justify="center")],
                bg=NAVY, padding=pad(22, 24)),
        section([box([eyebrow("Ubicació"), h("En un punt estratègic de l'Alt Empordà"),
                      p("Caravaning Vilamacolum està situat a Vilamacolum, molt a prop de Sant Pere "
                        "Pescador i de les principals zones de la Costa Brava, amb fàcil accés des de "
                        "Figueres i la resta de la comarca.")] + info_lines(), width=40, padding=pad(22)),
                 box([map_block(), btn("VEURE UBICACIÓ", "https://www.google.com/maps/search/?api=1&query=Caravaning+Vilamacolum")],
                     width=60, padding=pad(22), bg=LIGHT)],
                bg=WHITE, padding=pad(30, 24)),
        _anchored(contact_block(), "contacte"),
    ]


def _anchored(sec, anchor):
    sec["settings"]["_element_id"] = anchor
    return sec


def page_parking():
    def col(key, title, items, label, url):
        return box([image(key), h(title, 24, tag="h3"), checklist(items), btn(label, url)],
                   width=50, bg=WHITE, padding=pad(20), gap=18)
    return [
        hero("Parking de caravanes", "Un espai segur per a la teva caravana",
             "A Caravaning Vilamacolum posem a la teva disposició un ampli espai amb places cobertes i "
             "exteriors perquè la teva caravana estigui sempre protegida i llesta per a la teva "
             "pròxima aventura.",
             [btn("SOL·LICITAR PLAÇA", "/contacte/", light=True),
              btn("VEURE INSTAL·LACIONS", "/installacions/", outline=True)], bg="coberts"),
        stats_row([("fas fa-vector-square", "12.000 m²", "d'instal·lacions"),
                   ("fas fa-home", "PLACES COBERTES", "i exteriors"),
                   ("fas fa-shield-alt", "VIGILÀNCIA", "24 hores"),
                   ("fas fa-video", "ACCÉS CONTROLAT", "i tancat perimetralment")]),
        section([box([eyebrow("Dos tipus de places"), h("Parking cobert i exterior"),
                      p("Oferim solucions adaptades a les teves necessitats amb places cobertes i "
                        "exteriors, totes dins d'un recinte tancat, vigilat i amb fàcil accés durant tot l'any.")],
                     width=60),
                 box([icon("fas fa-parking", 40), h("Espais amplis i còmodes", 18, tag="h3"),
                      p("Dissenyats per a tot tipus de caravanes, autocaravanes i altres vehicles d'oci.", size=13)],
                     width=40, bg="#E8EFF7", padding=pad(20), radius=8)],
                bg=LIGHT, padding=pad(48, 24, 10)),
        section([col("coberts", "Parking cobert",
                     ["Protecció davant del sol, la pluja i les inclemències del temps",
                      "Manté la teva caravana en les millors condicions",
                      "Ideal per a estades de llarga durada", "Accés fàcil i ampli"],
                     "SOL·LICITAR PLAÇA COBERTA", "/contacte/"),
                 col("exterior", "Parking exterior",
                     ["Zones àmplies i ben delimitades", "Bona maniobrabilitat",
                      "Espais per a caravanes, autocaravanes i remolcs", "Entorn tranquil i segur"],
                     "SOL·LICITAR PLAÇA EXTERIOR", "/contacte/")],
                bg=LIGHT, padding=pad(10, 24, 48)),
        section([box([eyebrow("12.000 m²", WHITE), h("12.000 m²", 44, WHITE),
                      h("dedicats a la teva tranquil·litat", 22, WHITE, "h3"),
                      p("Un gran espai, ben organitzat i equipat, per garantir la seguretat i el bon "
                        "estat de la teva caravana durant tot l'any.", WHITE)], width=45)],
                bg_image="panoramica", overlay=0.45, min_h=380, padding=pad(60, 24), justify="center"),
        section([box([eyebrow("Per què triar-nos"), h("Màxima seguretat i comoditat")], width=100),
                 box([icon("fas fa-shield-alt", 40), h("Vigilància 24 hores", 17, tag="h3"),
                      p("Recinte tancat amb control d'accessos.", size=13)], width=25, bg=WHITE, padding=pad(20)),
                 box([icon("fas fa-video", 40), h("Entorn segur", 17, tag="h3"),
                      p("Càmeres de seguretat i il·luminació.", size=13)], width=25, bg=WHITE, padding=pad(20)),
                 box([icon("fas fa-map-marker-alt", 40), h("Fàcil accés", 17, tag="h3"),
                      p("Accés ampli per a tot tipus de vehicles.", size=13)], width=25, bg=WHITE, padding=pad(20)),
                 box([icon("fas fa-cog", 40), h("Servei addicional", 17, tag="h3"),
                      p("Neteja, manteniment i reparacions.", size=13)], width=25, bg=WHITE, padding=pad(20))],
                bg=LIGHT, padding=pad(48, 24)),
        section([box([eyebrow("Galeria"), h("Les nostres instal·lacions")], width=70),
                 box([btn("VEURE TOTES LES IMATGES", "/installacions/", outline=True)], width=30, justify="center"),
                 box([gallery(["coberts", "exterior", "aeria", "panoramica"])], width=100)],
                bg=WHITE, padding=pad(48, 24)),
        cta("Busques una plaça per a la teva caravana?", "Sol·licita informació sense compromís"),
    ]


def page_serveis():
    def card(ic, title, intro, items, key):
        return box([image(key), box([icon(ic, 26), h(title, 22, tag="h3")], row=True, gap=10, mobile_stack=False),
                    p(intro, size=14), checklist(items), btn("MÉS INFORMACIÓ", "/contacte/")],
                   width=25, bg=WHITE, padding=pad(16), gap=14)
    return [
        hero("Els nostres serveis", "Tot el que la teva caravana necessita",
             "A Caravaning Vilamacolum t'oferim molt més que un parking. Ens ocupem del manteniment, "
             "la neteja i les reparacions perquè la teva caravana estigui sempre a punt per gaudir de "
             "la pròxima escapada.",
             [btn("SOL·LICITAR INFORMACIÓ", "/contacte/", light=True),
              btn("VEURE INSTAL·LACIONS", "/installacions/", outline=True)], bg="exterior"),
        stats_row([("fas fa-wrench", "MANTENIMENT", "i revisions"),
                   ("fas fa-tint", "NETEJA", "interior i exterior"),
                   ("fas fa-cog", "REPARACIONS", "petites i mitjanes"),
                   ("fas fa-shield-alt", "TOT EN UN SOL LLOC", "professional i de confiança")]),
        section([box([eyebrow("Els nostres serveis"), h("Ens ocupem de la teva caravana"),
                      p("Oferim un servei complet per mantenir la teva caravana en perfectes condicions "
                        "durant tot l'any. Qualitat, experiència i un tracte proper.")], width=100),
                 card("fas fa-parking", "Parking", "Places cobertes i exteriors en un entorn segur i vigilat.",
                      ["Places cobertes i exteriors", "Accés fàcil i ampli", "Vigilància 24 hores",
                       "Ideal per estades llargues"], "coberts"),
                 card("fas fa-tint", "Neteja", "Neteja interior i exterior per tenir la teva caravana sempre a punt.",
                      ["Neteja exterior de carrosseria", "Neteja interior completa",
                       "Tractament de plàstics i gomes", "Preparació per a noves vacances"], None),
                 card("fas fa-cog", "Manteniment", "Revisions periòdiques per garantir la seguretat i el bon estat del teu vehicle.",
                      ["Revisió general", "Control d'instal·lacions", "Bateria, pneumàtics i frens",
                       "Consells personalitzats"], None),
                 card("fas fa-wrench", "Reparacions", "Solucions per a petites i mitjanes reparacions.",
                      ["Electricitat i il·luminació", "Aigua i sanejament", "Substitució de peces",
                       "Posada a punt abans de viatjar"], None)],
                bg=LIGHT, padding=pad(48, 24)),
        section([box([image("exterior")], width=45),
                 box([h("Viatja amb tranquil·litat"),
                      p("Confia la teva caravana a un equip amb experiència. Nosaltres ens encarreguem "
                        "de mantenir-la segura, neta i en perfectes condicions."),
                      box([stat("fas fa-shield-alt", "Seguretat", "durant tot l'any", 25),
                           stat("far fa-calendar-alt", "Estalvi de temps", "i preocupacions", 25),
                           stat("far fa-check-circle", "Més durabilitat", "del teu vehicle", 25),
                           stat("fas fa-sun", "Llesta per a", "la pròxima aventura", 25)],
                          row=True, gap=10)], width=55, padding=pad(22))],
                bg=LIGHT, padding=pad(0, 24, 30)),
        section([box([eyebrow("Un servei personalitzat"), h("Assessorament i tracte proper"),
                      p("Cada caravana és diferent, per això t'oferim un servei adaptat a les teves "
                        "necessitats. T'assessorem sobre el manteniment, la neteja i qualsevol dubte que "
                        "tinguis, amb un tracte pròxim i professional."),
                      btn("CONTACTA AMB NOSALTRES", "/contacte/")], width=50, padding=pad(22)),
                 box([image("coberts")], width=50)],
                bg=LIGHT, padding=pad(30, 24)),
        section([box([eyebrow("Galeria"), h("Serveis en imatges")], width=70),
                 box([btn("VEURE TOTES LES IMATGES", "/installacions/", outline=True)], width=30, justify="center"),
                 box([gallery(["coberts", "exterior", "aeria", "panoramica"])], width=100)],
                bg=WHITE, padding=pad(40, 24)),
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
        section([box([eyebrow("Galeria"), h("Les nostres instal·lacions")], width=100),
                 box([gallery(["coberts", "exterior", "aeria", "panoramica"])], width=100)],
                bg=LIGHT, padding=pad(48, 24)),
        cta("Busques una plaça per a la teva caravana?", "Sol·licita informació sense compromís"),
    ]


def page_sobre():
    return [
        hero("Sobre nosaltres", "Cuidem la teva caravana com si fos nostra",
             "A Caravaning Vilamacolum (Mas Font) ens dediquem al parking i la cura de caravanes "
             "a l'Alt Empordà.", [btn("CONTACTA AMB NOSALTRES", "/contacte/", light=True)], bg="aeria"),
        section([box([eyebrow("Qui som"), h("Un equip proper i de confiança"),
                      p("[Text a revisar amb el client: història de Mas Font, anys d'experiència i valors.]")],
                     width=55, padding=pad(22)),
                 box([image("exterior")], width=45)], bg=WHITE, padding=pad(48, 24)),
        section([box([eyebrow("Els nostres valors"), h("Per què confiar en nosaltres")], width=100),
                 box([icon("fas fa-shield-alt", 40), h("Seguretat", 18, tag="h3"),
                      p("Recinte vigilat i amb accés controlat.", size=13)], width=33, bg=WHITE, padding=pad(20)),
                 box([icon("fas fa-handshake", 40), h("Tracte proper", 18, tag="h3"),
                      p("T'assessorem amb un servei personalitzat.", size=13)], width=33, bg=WHITE, padding=pad(20)),
                 box([icon("fas fa-tools", 40), h("Servei complet", 18, tag="h3"),
                      p("Parking, neteja, manteniment i reparacions.", size=13)], width=33, bg=WHITE, padding=pad(20))],
                bg=LIGHT, padding=pad(48, 24)),
        cta("Vols saber-ne més?", "Sol·licita informació sense compromís"),
    ]


def page_contacte():
    return [
        hero("Contacte", "Parlem de la teva caravana",
             "Explica'ns què necessites i t'informarem sobre disponibilitat i serveis.",
             [btn("TRUCA'NS: " + TEL, "tel:+34677858096", light=True)], bg="exterior", min_h=360),
        section([box([eyebrow("Ubicació"), h("Com arribar")] + info_lines() +
                     [btn("VEURE UBICACIÓ", "https://www.google.com/maps/search/?api=1&query=Caravaning+Vilamacolum")],
                     width=40, padding=pad(22)),
                 box([map_block()], width=60, padding=pad(22), bg=LIGHT)], bg=WHITE, padding=pad(40, 24)),
        _anchored(contact_block("Sol·licita informació sense compromís"), "contacte"),
    ]


PAGES = {"inici": page_inici, "parking": page_parking, "serveis": page_serveis,
         "installacions": page_installacions, "sobre-nosaltres": page_sobre, "contacte": page_contacte}


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "elementor")
    os.makedirs(out, exist_ok=True)
    for slug, fn in PAGES.items():
        doc = {"content": fn(), "page_settings": [], "version": "0.4",
               "title": slug.replace("-", " ").title(), "type": "page"}
        path = os.path.join(out, f"{slug}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
        print("escrit", os.path.normpath(path))


if __name__ == "__main__":
    main()
