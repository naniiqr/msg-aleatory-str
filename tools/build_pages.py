#!/usr/bin/env python3
"""Genera les plantilles Elementor (JSON) de Caravaning Vilamacolum.

Dissenys de referència: caravaning_vilamacolum.pdf (Inici, Parking, Serveis).
Ús:  python3 tools/build_pages.py   ->  escriu els fitxers a ./elementor/
"""
import hashlib
import json
import os

NAVY, LIGHT, SOFT, TEXT, WHITE = "#061C49", "#EEF3F8", "#F7FAFD", "#526078", "#FFFFFF"
FONT = "Montserrat"
UP = "https://proveswebsfigueres.com/caravaningvilamacolum/wp-content/uploads/2026/10/"

# Imatges que ja són a la mediateca. Els "slots" que encara no tenen foto pròpia
# reutilitzen una d'aquestes (vegeu README, taula d'imatges pendents).
IMG = {
    "aeria": (UP + "vista_aerea.webp", 18),
    "coberts": (UP + "places_cobertes.webp", 19),
    "exterior": (UP + "zona_exterior.webp", 20),
    "panoramica": (UP + "vista_aerea_panoramica.webp", 25),
}
ADDR1, ADDR2 = "Ctra. Figueres a La Bisbal, Km 28", "17474 Vilamacolum · Girona"
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


def rgba(a):
    return f"rgba(6,28,73,{a})"


def gradient(prefix, a, sa, b, sb, angle):
    return {f"{prefix}background": "gradient", f"{prefix}color": a,
            f"{prefix}color_stop": {"unit": "%", "size": sa}, f"{prefix}color_b": b,
            f"{prefix}color_b_stop": {"unit": "%", "size": sb},
            f"{prefix}gradient_type": "linear",
            f"{prefix}gradient_angle": {"unit": "deg", "size": angle}}


def widget(kind, settings):
    return {"id": _id(), "settings": settings, "elements": [], "isInner": False,
            "widgetType": kind, "elType": "widget"}


# ------------------------------------------------------------ contenidors
def box(children, *, width=None, row=False, bg=None, padding=None, gap=16, boxed=False,
        inner=True, align=None, justify=None, radius=None, bg_image=None, overlay=None,
        grad=None, min_h=None, css=None, mob=None, center=False, align_mobile=None,
        shadow=False, flush=False, grow=False, border_r=None, full_h=False):
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
    if overlay is not None:
        s["background_overlay_background"] = "classic"
        s["background_overlay_color"] = NAVY
        s["background_overlay_opacity"] = {"unit": "px", "size": overlay, "sizes": []}
    if grad:  # (color_a, stop_a, color_b, stop_b, angle)
        s.update(gradient("background_overlay_", *grad))
        s["background_overlay_opacity"] = {"unit": "px", "size": 1, "sizes": []}
    if min_h:
        s["min_height"] = px(min_h)
        s["min_height_tablet"] = px(int(min_h * 0.85))
        s["min_height_mobile"] = px(int(min_h * 0.7))
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
    if flush:
        s["overflow"] = "hidden"
    if grow:
        s["_flex_size"] = "grow"
    if border_r:
        s["border_border"] = "solid"
        s["border_width"] = {"unit": "px", "top": "0", "right": "1", "bottom": "0", "left": "0",
                             "isLinked": False}
        s["border_width_tablet"] = {"unit": "px", "top": "0", "right": "0", "bottom": "0",
                                    "left": "0", "isLinked": False}
        s["border_color"] = "#D5DEEA"
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
    """Responsive i alineació uniformes per a tot l'arbre."""
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
    if "padding" in s:
        t, r, b = s["padding"]["top"], s["padding"]["right"], s["padding"]["bottom"]
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
            uneven = n == 3 and len({x["settings"]["width"]["size"] for x in narrow}) > 1
            for k in sized:
                w = k["settings"]["width"]["size"]
                if w >= 90 or n <= 2 or (uneven and k is narrow[0]):
                    tw = 100
                elif uneven:
                    tw = 47
                else:
                    tw = 30 if n in (3, 5, 6) else 47
                mw = 46 if (mob == 2 and w < 90) else 100
                k["settings"]["width_tablet"] = {"unit": "%", "size": tw}
                k["settings"]["width_mobile"] = {"unit": "%", "size": mw}
    for k in kids:
        finalize(k)
    return node


# ---------------------------------------------------------------- widgets
def eyebrow(text, color=NAVY, upper=True, size=11):
    return widget("heading", {
        "title": text.upper() if upper else text, "header_size": "h6", "title_color": color,
        "typography_typography": "custom", "typography_font_family": FONT,
        "typography_font_size": px(size), "typography_font_weight": "600" if upper else "700",
        "typography_letter_spacing": px(2 if upper else 0)})


def h(text, size=30, color=NAVY, tag="h2", align=None):
    s = {"title": text, "header_size": tag, "title_color": color,
         "typography_typography": "custom", "typography_font_family": FONT,
         "typography_font_size": px(size), "typography_font_weight": "700",
         "typography_line_height": {"unit": "em", "size": 1.2},
         "typography_font_size_tablet": px(max(18, int(size * 0.85))),
         "typography_font_size_mobile": px(max(18, int(size * 0.68)))}
    if align:
        s["align"] = align
    return widget("heading", s)


def p(text, color=TEXT, size=15, align=None, weight=None):
    s = {"editor": f"<p>{text}</p>", "text_color": color,
         "typography_typography": "custom", "typography_font_family": FONT,
         "typography_font_size": px(size),
         "typography_line_height": {"unit": "em", "size": 1.55}}
    if weight:
        s["typography_font_weight"] = weight
    if align:
        s["align"] = align
    return widget("text-editor", s)


def btn(text, url, *, light=False, outline=False, dark_outline=False, arrow=True, hero=False,
        icon_cls=None):
    s = {"text": text, "link": {"url": url}, "size": "md",
         "typography_typography": "custom", "typography_font_family": FONT,
         "typography_font_weight": "600", "typography_font_size": px(13),
         "border_radius": {"unit": "px", "top": 6, "right": 6, "bottom": 6, "left": 6, "isLinked": True},
         "button_text_color": NAVY if light else WHITE,
         "background_color": WHITE if light else NAVY,
         "text_padding": pad(14, 22), "align_mobile": "stretch"}
    ic = icon_cls or ("fas fa-arrow-right" if arrow else None)
    if ic:
        s["selected_icon"] = {"value": ic, "library": "fa-solid" if ic.startswith("fas") else "fa-regular"}
        s["icon_align"] = "row-reverse" if arrow and not icon_cls else "row"
        s["icon_indent"] = px(10)
    bw = {"unit": "px", "top": "1", "right": "1", "bottom": "1", "left": "1", "isLinked": True}
    if hero:  # botó primari del hero: blau amb vora clara
        s.update({"border_border": "solid", "border_width": bw, "border_color": "rgba(255,255,255,0.45)"})
    if outline:  # secundari del hero: transparent, vora blanca
        s.update({"background_color": "rgba(255,255,255,0.06)", "button_text_color": WHITE,
                  "border_border": "solid", "border_width": bw, "border_color": "rgba(255,255,255,0.55)"})
    if dark_outline:  # "Veure totes les imatges"
        s.update({"background_color": "rgba(255,255,255,0)", "button_text_color": NAVY,
                  "border_border": "solid", "border_width": bw, "border_color": NAVY})
    return widget("button", s)


def btn_row(buttons):
    return box(buttons, row=True, gap=14)


def image(key, height=260, radius=8):
    return widget("image", {
        "image": img(key), "image_size": "full", "width": {"unit": "%", "size": 100},
        "height": px(height), "height_tablet": px(int(height * 0.9)),
        "height_mobile": px(int(height * 0.75)), "object-fit": "cover",
        "image_border_radius": {"unit": "px", "top": radius, "right": radius, "bottom": radius,
                                "left": radius, "isLinked": True}})


def checklist(items, size=13, light=False):
    return widget("icon-list", {
        "icon_list": [{"text": t, "selected_icon": {"value": "fas fa-check-circle", "library": "fa-solid"},
                       "_id": _id()} for t in items],
        "space_between": px(9), "icon_color": NAVY, "icon_size": px(size + 1), "text_color": TEXT,
        "text_indent": px(10),
        "icon_typography_typography": "custom", "icon_typography_font_family": FONT,
        "icon_typography_font_size": px(size)})


def icon(cls, size=34, color=NAVY, align="left"):
    return widget("icon", {"selected_icon": {"value": cls, "library": "fa-solid"},
                           "primary_color": color, "size": px(size), "align": align,
                           "_element_width": "auto"})


def map_block(height=300):
    return widget("google_maps", {"address": "Caravaning Vilamacolum, Vilamacolum, Girona",
                                  "zoom": {"unit": "px", "size": 13},
                                  "height": px(height), "height_mobile": px(260)})


def contact_line(ic, html):
    return box([icon(ic, 20), p(html, NAVY, 14, weight="600")], row=True, gap=14, align="flex-start")


def form():
    fld = {"width_mobile": "100"}
    return widget("form", {
        "form_name": "Contacte Caravaning Vilamacolum",
        "form_fields": [
            {"field_type": "text", "field_label": "Nom", "placeholder": "Nom", "required": "true",
             "_id": "nom", "width": "50", **fld},
            {"field_type": "tel", "field_label": "Telèfon", "placeholder": "Telèfon", "required": "true",
             "_id": "telefon", "width": "50", **fld},
            {"field_type": "email", "field_label": "Email", "placeholder": "Email", "required": "true",
             "_id": "email", "width": "100"},
            {"field_type": "select", "field_label": "Tipus de vehicle",
             "field_options": "Tipus de vehicle|\nCaravana\nAutocaravana\nRemolc\nAltres", "_id": "vehicle",
             "width": "100"},
            {"field_type": "textarea", "field_label": "Missatge", "placeholder": "Missatge", "rows": "3",
             "_id": "missatge", "width": "100"},
            {"field_type": "acceptance", "field_label": "Accepto la política de privacitat",
             "required": "true", "_id": "privacitat", "width": "100"}],
        "show_labels": "", "button_text": "SOL·LICITAR INFORMACIÓ", "button_size": "md",
        "button_align": "start",
        "selected_button_icon": {"value": "fas fa-arrow-right", "library": "fa-solid"},
        "button_icon_align": "row-reverse", "button_icon_indent": px(10),
        "field_background_color": "rgba(255,255,255,0.04)", "field_text_color": WHITE,
        "field_border_border": "solid", "field_border_color": "rgba(255,255,255,0.35)",
        "field_border_width": {"unit": "px", "top": "1", "right": "1", "bottom": "1", "left": "1",
                               "isLinked": True},
        "field_border_radius": {"unit": "px", "top": 4, "right": 4, "bottom": 4, "left": 4, "isLinked": True},
        "field_typography_typography": "custom", "field_typography_font_family": FONT,
        "field_typography_font_size": px(12),
        "button_text_color": NAVY, "button_background_color": WHITE,
        "button_border_radius": {"unit": "px", "top": 6, "right": 6, "bottom": 6, "left": 6, "isLinked": True},
        "button_typography_typography": "custom", "button_typography_font_family": FONT,
        "button_typography_font_weight": "600", "button_typography_font_size": px(13),
        "row_gap": px(12), "column_gap": px(12),
        "submit_actions": ["email"], "email_subject": "Nova consulta - Caravaning Vilamacolum",
        "email_content": "[all-fields]",
        "success_message": "Gràcies! Hem rebut la teva consulta.",
        "error_message": "S'ha produït un error. Torna-ho a provar.",
        "server_message": "Error del servidor. Torna-ho a provar.",
        "invalid_message": "El formulari no és vàlid.",
        "required_field_message": "Aquest camp és obligatori."})


# ----------------------------------------------------------------- blocs
HERO_GRAD = (rgba(0.80), 0, rgba(0.10), 72, 90)


def hero(eyebrow_t, title, text, buttons, bg="aeria", min_h=440):
    inner = ([eyebrow(eyebrow_t, WHITE, size=11)] if eyebrow_t else []) + [
        h(title, 44, WHITE, "h1"), p(text, WHITE, 16), btn_row(buttons)]
    return section([box(inner, width=62, gap=16)], bg_image=bg, grad=HERO_GRAD, min_h=min_h,
                   padding=pad(60, 24), align="center", justify="flex-end" if False else None)


def hero_btns(primary_label, primary_url, second_label, second_url):
    return [btn(primary_label, primary_url, hero=True), btn(second_label, second_url, outline=True, arrow=False)]


def stat_item(ic, title, sub, width, last=False):
    return box([icon(ic, 34), box([h(title, 13, tag="h4"), p(sub, size=11)], gap=2, grow=True)],
               row=True, width=width, gap=12, padding=pad(6, 16), align="center",
               border_r=not last)


def stats_row(items):
    w = 100 // len(items)
    return section([stat_item(*i, w, last=(k == len(items) - 1)) for k, i in enumerate(items)],
                   bg=WHITE, padding=pad(18, 24), mob=2)


def head(eyebrow_t, title, text=None, button=None, bg=LIGHT, upper=True):
    left = [eyebrow(eyebrow_t, upper=upper), h(title, 32)] + ([p(text)] if text else [])
    if button:
        return section([box(left, width=70), box([button], width=30, align="flex-end",
                                                 align_mobile="flex-start", justify="center")],
                       bg=bg, padding=pad(40, 24, 0), align="center")
    return section([box(left, width=100)], bg=bg, padding=pad(40, 24, 0))


def grid(cards, bg=LIGHT, mob=None, bottom=40):
    return section(cards, bg=bg, padding=pad(24, 24, bottom), mob=mob)


def card(children, width, **kw):
    return box(children, width=width, bg=WHITE, padding=pad(20), gap=12, radius=8, shadow=True, **kw)


def icon_card(ic, title, text, width, size=34, tsize=18, center=False):
    return card([icon(ic, size), h(title, tsize, tag="h3"), p(text, size=13)], width, center=center)


def photo_card(key, title, text, width, h_min=215):
    """Imatge a tota la targeta amb degradat inferior i text a sobre (Inici)."""
    return box([h(title, 20, WHITE, "h3"), p(text, "#E3EAF5", 12)], width=width, bg_image=key,
               grad=(rgba(0), 30, rgba(0.88), 100, 180), min_h=h_min, justify="flex-end",
               padding=pad(22), gap=6, radius=8, flush=True)


def flush_card(top, body, width):
    """Targeta amb imatge a dalt sense marges (Parking / Serveis)."""
    return box([top, box(body, padding=pad(20), gap=14, grow=True, justify="space-between")],
               width=width, bg=WHITE, gap=0, radius=8, shadow=True, flush=True, padding=pad(0))


def cta(eyebrow_t, title, label="CONTACTA ARA", url="/contacte/"):
    return section(
        [box([eyebrow(eyebrow_t, WHITE, size=10), h(title, 30, WHITE)], width=62),
         box([btn(label, url, light=True)], width=38, align="flex-end", align_mobile="flex-start",
             justify="center")],
        bg=NAVY, padding=pad(54, 24), align="center", css="cta-vilamacolum")


def location_row(bg=WHITE):
    """Un sol contenidor amb 3 columnes: ubicació | mapa | formulari (com al PDF)."""
    info = box([eyebrow("Ubicació", upper=False, size=12),
                h("En un punt estratègic de l'Alt Empordà", 28),
                p("Caravaning Vilamacolum està situat a Vilamacolum, molt a prop de Sant Pere Pescador "
                  "i de les principals zones de la Costa Brava, amb fàcil accés des de Figueres i la "
                  "resta de la comarca.", size=13),
                contact_line("fas fa-map-marker-alt",
                             f"Caravaning Vilamacolum – Mas Font<br><span style='font-weight:400'>{ADDR1}<br>{ADDR2}</span>"),
                contact_line("fas fa-phone", f'<a href="tel:+34677858096" style="color:inherit">{TEL}</a>'),
                contact_line("fas fa-envelope", f'<a href="mailto:{MAIL}" style="color:inherit">{MAIL}</a>')],
               width=34, gap=14, justify="center")
    mapa = box([map_block(300)], width=30, radius=10, flush=True, justify="center")
    card_form = box([
        box([eyebrow("Contacte", WHITE, size=10), h("Busques un lloc per a la teva caravana?", 18, WHITE, "h3")],
            row=True, gap=14, align="center"),
        p("Explica'ns què necessites i t'informarem sobre disponibilitat i serveis.", "#DCE5F3", 11),
        form()], width=36, bg=NAVY, padding=pad(22), gap=14, radius=10)
    sec = section([info, mapa, card_form], bg=bg, padding=pad(40, 24), align="stretch", gap=24)
    sec["settings"]["_element_id"] = "contacte"
    return sec


# ------------------------------------------------------------ pàgines
def page_inici():
    return [
        hero("", "La teva caravana, sempre en bones mans",
             "Parking i cura de caravanes a Vilamacolum, en ple Alt Empordà.",
             hero_btns("SOL·LICITAR PLAÇA", "#contacte", "VEURE INSTAL·LACIONS", "/installacions/"),
             bg="aeria", min_h=440),
        stats_row([("far fa-square", "12.000 m²", "d'instal·lacions"),
                   ("fas fa-home", "PLACES COBERTES", "i exteriors"),
                   ("fas fa-shield-alt", "VIGILÀNCIA", "per a la teva tranquil·litat"),
                   ("fas fa-wrench", "MANTENIMENT", "i reparacions"),
                   ("fas fa-tint", "NETEJA", "per tenir-la sempre a punt")]),
        section([
            box([eyebrow("Molt més que un parking", size=10), h("Un espai pensat per a la teva tranquil·litat", 28),
                 p("A Caravaning Vilamacolum t'oferim un espai ampli, segur i ben equipat per guardar "
                   "la teva caravana durant tot l'any, amb serveis de manteniment, neteja i reparacions.",
                   size=14),
                 btn("DESCOBREIX ELS NOSTRES SERVEIS", "/serveis/")], width=40, gap=14, justify="center"),
            photo_card("coberts", "Parking cobert", "Protecció durant tot l'any.", 30),
            photo_card("exterior", "Parking exterior", "Amples zones per a caravanes i altres vehicles.", 30),
        ], bg=SOFT, padding=pad(36, 24), align="center"),
        section([box([eyebrow("Els nostres serveis", size=10, color=NAVY), h("Ens ocupem de la teva caravana", 30)],
                     width=100, align="center", gap=8, center=True)],
                bg=LIGHT, padding=pad(40, 24, 0)),
        grid([card([icon("fas fa-parking", 34), h("Parking", 20, tag="h3"),
                    p("Espais amplis, còmodes i segurs.", size=13)], 25),
              card([icon("fas fa-tint", 34), h("Neteja", 20, tag="h3"),
                    p("La preparem perquè estigui llesta per a les teves properes vacances.", size=13)], 25),
              card([icon("fas fa-wrench", 34), h("Manteniment", 20, tag="h3"),
                    p("Revisió i manteniment per conservar-la en les millors condicions.", size=13)], 25),
              card([icon("fas fa-cog", 34), h("Reparacions", 20, tag="h3"),
                    p("Solucions per a petites reparacions i posada a punt.", size=13)], 25)]),
        # banda: imatge a l'esquerra que es fon en blau cap a la dreta (degradat)
        box([box([], width=62, min_h=200),
             box([eyebrow("Tranquil·litat tot l'any", WHITE, size=10),
                  h("Tu gaudeix del viatge. Nosaltres cuidem de la teva caravana.", 30, WHITE),
                  btn("SOL·LICITAR INFORMACIÓ", "#contacte", light=True)],
                 width=38, bg=NAVY, padding=pad(36, 40), gap=16, justify="center")],
            row=True, inner=False, gap=0, bg_image="panoramica", min_h=300, padding=pad(0),
            grad=(rgba(0), 40, NAVY, 62, 90), align="stretch"),
        location_row(WHITE),
    ]


def mosaic():
    big = box([], width=44, bg_image="coberts", min_h=340, radius=8)
    col1 = box([box([], bg_image="exterior", min_h=164, radius=8),
                box([], bg_image="panoramica", min_h=164, radius=8)], width=28, gap=12)
    col2 = box([box([], bg_image="aeria", min_h=164, radius=8),
                box([], bg_image="coberts", min_h=164, radius=8)], width=28, gap=12)
    return section([big, col1, col2], bg=WHITE, padding=pad(24, 24, 44), gap=12)


def page_parking():
    def col(key, title, items, label):
        return flush_card(image(key, 200, 0),
                          [h(title, 22, tag="h3"), checklist(items), btn(label, "/contacte/")], 50)
    return [
        hero("Parking de caravanes", "Un espai segur per a la teva caravana",
             "A Caravaning Vilamacolum posem a la teva disposició un ampli espai amb places cobertes i "
             "exteriors perquè la teva caravana estigui sempre protegida i llesta per a la teva "
             "pròxima aventura.",
             hero_btns("SOL·LICITAR PLAÇA", "/contacte/", "VEURE INSTAL·LACIONS", "/installacions/"),
             bg="coberts", min_h=440),
        stats_row([("far fa-square", "12.000 m²", "d'instal·lacions"),
                   ("fas fa-home", "PLACES COBERTES", "i exteriors"),
                   ("fas fa-shield-alt", "VIGILÀNCIA", "24 hores"),
                   ("fas fa-camera", "ACCÉS CONTROLAT", "i tancat perimetralment")]),
        section([box([eyebrow("Dos tipus de places", size=10), h("Parking cobert i exterior", 34),
                      p("Oferim solucions adaptades a les teves necessitats amb places cobertes i "
                        "exteriors, totes dins d'un recinte tancat, vigilat i amb fàcil accés durant tot l'any.",
                        size=14)], width=58, gap=12, justify="center"),
                 box([box([icon("fas fa-parking", 44),
                           box([h("Espais amplis i còmodes", 17, tag="h3"),
                                p("Dissenyats per a tot tipus de caravanes, autocaravanes i altres vehicles d'oci.",
                                  size=12)], gap=6, grow=True)], row=True, gap=16, align="center")],
                     width=42, bg="#E4ECF7", padding=pad(24), radius=8, justify="center")],
                bg=SOFT, padding=pad(44, 24, 0), align="center"),
        grid([col("coberts", "Parking cobert",
                  ["Protecció davant del sol, la pluja i les inclemències del temps",
                   "Manté la teva caravana en les millors condicions",
                   "Ideal per a estades de llarga durada", "Accés fàcil i ampli"],
                  "SOL·LICITAR PLAÇA COBERTA"),
              col("exterior", "Parking exterior",
                  ["Zones àmplies i ben delimitades", "Bona maniobrabilitat",
                   "Espais per a caravanes, autocaravanes i remolcs", "Entorn tranquil i segur"],
                  "SOL·LICITAR PLAÇA EXTERIOR")], bg=SOFT, bottom=44),
        section([box([eyebrow("12.000 m²", WHITE, size=10), h("12.000 m²", 44, WHITE),
                      h("dedicats a la teva tranquil·litat", 20, WHITE, "h3"),
                      p("Un gran espai, ben organitzat i equipat, per garantir la seguretat i el bon "
                        "estat de la teva caravana durant tot l'any.", WHITE, 14)], width=42, gap=10)],
                bg_image="panoramica", grad=(rgba(0.78), 0, rgba(0), 60, 90), min_h=300,
                padding=pad(50, 24), align="center"),
        head("Per què triar-nos", "Màxima seguretat i comoditat", bg=SOFT),
        grid([card([icon("fas fa-shield-alt", 38), h("Vigilància 24 hores", 16, tag="h3"),
                    p("Recinte tancat amb control d'accessos.", size=13)], 25),
              card([icon("fas fa-camera", 38), h("Entorn segur", 16, tag="h3"),
                    p("Càmeres de seguretat i il·luminació.", size=13)], 25),
              card([icon("fas fa-map-marker-alt", 38), h("Fàcil accés", 16, tag="h3"),
                    p("Accés ampli per a tot tipus de vehicles.", size=13)], 25),
              card([icon("fas fa-cog", 38), h("Servei addicional", 16, tag="h3"),
                    p("Neteja, manteniment i reparacions.", size=13)], 25)], bg=SOFT),
        head("Galeria", "Les nostres instal·lacions",
             button=btn("VEURE TOTES LES IMATGES", "/installacions/", dark_outline=True), bg=WHITE),
        mosaic(),
        cta("Busques una plaça per a la teva caravana?", "Sol·licita informació sense compromís"),
    ]


def page_serveis():
    def svc(ic, title, intro, items, key):
        return flush_card(image(key, 160, 0),
                          [box([icon(ic, 26), h(title, 20, tag="h3")], row=True, gap=12, align="center"),
                           p(intro, size=13), checklist(items, 12), btn("MÉS INFORMACIÓ", "/contacte/")], 25)
    small = lambda ic, t, sub: card([icon(ic, 26, align="center"), h(t, 12, tag="h4", align="center"),
                                     p(sub, size=11, align="center")], 25, center=True)
    return [
        hero("Els nostres serveis", "Tot el que la teva caravana necessita",
             "A Caravaning Vilamacolum t'oferim molt més que un parking. Ens ocupem del manteniment, "
             "la neteja i les reparacions perquè la teva caravana estigui sempre a punt per gaudir de "
             "la pròxima escapada.",
             hero_btns("SOL·LICITAR INFORMACIÓ", "/contacte/", "VEURE INSTAL·LACIONS", "/installacions/"),
             bg="exterior", min_h=440),
        stats_row([("fas fa-wrench", "MANTENIMENT", "i revisions"),
                   ("fas fa-tint", "NETEJA", "interior i exterior"),
                   ("fas fa-cog", "REPARACIONS", "petites i mitjanes"),
                   ("fas fa-shield-alt", "TOT EN UN SOL LLOC", "professional i de confiança")]),
        head("Els nostres serveis", "Ens ocupem de la teva caravana",
             "Oferim un servei complet per mantenir la teva caravana en perfectes condicions "
             "durant tot l'any. Qualitat, experiència i un tracte proper.", bg=SOFT),
        grid([svc("fas fa-parking", "Parking", "Places cobertes i exteriors en un entorn segur i vigilat.",
                  ["Places cobertes i exteriors", "Accés fàcil i ampli", "Vigilància 24 hores",
                   "Ideal per estades llargues"], "coberts"),
              svc("fas fa-tint", "Neteja", "Neteja interior i exterior per tenir la teva caravana sempre a punt.",
                  ["Neteja exterior de carrosseria", "Neteja interior completa",
                   "Tractament de plàstics i gomes", "Preparació per a noves vacances"], "exterior"),
              svc("fas fa-cog", "Manteniment",
                  "Revisions periòdiques per garantir la seguretat i el bon estat del teu vehicle.",
                  ["Revisió general", "Control d'instal·lacions", "Bateria, pneumàtics i frens",
                   "Consells personalitzats"], "aeria"),
              svc("fas fa-wrench", "Reparacions", "Solucions per a petites i mitjanes reparacions.",
                  ["Electricitat i il·luminació", "Aigua i sanejament", "Substitució de peces",
                   "Posada a punt abans de viatjar"], "panoramica")], bg=SOFT, bottom=36),
        # imatge a sagnat esquerre (flush) + text
        box([box([], width=48, bg_image="exterior", min_h=260),
             box([h("Viatja amb tranquil·litat", 28),
                  p("Confia la teva caravana a un equip amb experiència. Nosaltres ens encarreguem "
                    "de mantenir-la segura, neta i en perfectes condicions.", size=14),
                  box([small("fas fa-shield-alt", "Seguretat", "durant tot l'any"),
                       small("far fa-calendar-alt", "Estalvi de temps", "i preocupacions"),
                       small("far fa-check-circle", "Més durabilitat", "del teu vehicle"),
                       small("fas fa-sun", "Llesta per a", "la pròxima aventura")],
                      row=True, gap=10, mob=2)],
                 width=52, gap=14, padding=pad(30, 32), justify="center")],
            row=True, inner=False, gap=0, bg=SOFT, padding=pad(0), align="stretch"),
        # text + imatge a sagnat dret (flush)
        box([box([eyebrow("Un servei personalitzat", size=10), h("Assessorament i tracte proper", 28),
                  p("Cada caravana és diferent, per això t'oferim un servei adaptat a les teves "
                    "necessitats. T'assessorem sobre el manteniment, la neteja i qualsevol dubte que "
                    "tinguis, amb un tracte pròxim i professional.", size=14),
                  btn("CONTACTA AMB NOSALTRES", "/contacte/")],
                 width=52, gap=14, padding=pad(40, 40), justify="center"),
             box([], width=48, bg_image="coberts", min_h=240)],
            row=True, inner=False, gap=0, bg=SOFT, padding=pad(0), align="stretch"),
        head("Galeria", "Serveis en imatges",
             button=btn("VEURE TOTES LES IMATGES", "/installacions/", dark_outline=True), bg=WHITE),
        section([box([], width=16, bg_image=k, min_h=135, radius=8)
                 for k in ("coberts", "exterior", "aeria", "panoramica", "coberts", "exterior")],
                bg=WHITE, padding=pad(24, 24, 44), gap=12),
        cta("Vols saber més sobre els nostres serveis?", "Sol·licita informació sense compromís",
            "SOL·LICITAR INFORMACIÓ"),
    ]


def page_installacions():
    return [
        hero("Instal·lacions", "12.000 m² pensats per a la teva caravana",
             "Un recinte ampli, ben organitzat i vigilat, amb places cobertes i exteriors a Vilamacolum.",
             [btn("SOL·LICITAR PLAÇA", "/contacte/", hero=True)], bg="panoramica", min_h=400),
        stats_row([("far fa-square", "12.000 m²", "d'instal·lacions"),
                   ("fas fa-home", "PLACES COBERTES", "i exteriors"),
                   ("fas fa-shield-alt", "VIGILÀNCIA", "24 hores"),
                   ("fas fa-camera", "ACCÉS CONTROLAT", "i tancat perimetralment")]),
        head("Galeria", "Les nostres instal·lacions", bg=WHITE),
        mosaic(),
        cta("Busques una plaça per a la teva caravana?", "Sol·licita informació sense compromís"),
    ]


def page_sobre():
    return [
        hero("Sobre nosaltres", "Cuidem la teva caravana com si fos nostra",
             "A Caravaning Vilamacolum (Mas Font) ens dediquem al parking i la cura de caravanes "
             "a l'Alt Empordà.", [btn("CONTACTA AMB NOSALTRES", "/contacte/", hero=True)], bg="aeria",
             min_h=400),
        box([box([eyebrow("Qui som", size=10), h("Un equip proper i de confiança", 28),
                  p("[Text a revisar amb el client: història de Mas Font, anys d'experiència i valors.]",
                    size=14)], width=52, gap=14, padding=pad(40, 40), justify="center"),
             box([], width=48, bg_image="exterior", min_h=300)],
            row=True, inner=False, gap=0, bg=SOFT, padding=pad(0), align="stretch"),
        head("Els nostres valors", "Per què confiar en nosaltres", bg=LIGHT),
        grid([card([icon("fas fa-shield-alt", 38), h("Seguretat", 16, tag="h3"),
                    p("Recinte vigilat i amb accés controlat.", size=13)], 33),
              card([icon("fas fa-handshake", 38), h("Tracte proper", 16, tag="h3"),
                    p("T'assessorem amb un servei personalitzat.", size=13)], 33),
              card([icon("fas fa-tools", 38), h("Servei complet", 16, tag="h3"),
                    p("Parking, neteja, manteniment i reparacions.", size=13)], 33)]),
        cta("Vols saber-ne més?", "Sol·licita informació sense compromís"),
    ]


def page_contacte():
    return [
        hero("Contacte", "Parlem de la teva caravana",
             "Explica'ns què necessites i t'informarem sobre disponibilitat i serveis.",
             [btn("TRUCA'NS: " + TEL, "tel:+34677858096", hero=True, arrow=False, icon_cls="fas fa-phone")],
             bg="exterior", min_h=360),
        location_row(WHITE),
    ]


# ------------------------------------------------- header i footer (Pro)
def header():
    logo = box([widget("theme-site-logo", {
        "width": px(118), "width_tablet": px(100), "width_mobile": px(76),
        "link_to": "custom", "link": {"url": "/"},
        "_margin": {"unit": "px", "top": "4", "right": "0", "bottom": "-46", "left": "0", "isLinked": False},
        "_margin_mobile": {"unit": "px", "top": "2", "right": "0", "bottom": "-14", "left": "0", "isLinked": False},
        "_z_index": 100})], align="flex-start")
    nav = box([widget("nav-menu", {
        "menu": "menu-principal", "layout": "horizontal", "align_items": "center",
        "pointer": "underline", "animation_line": "fade", "dropdown": "tablet", "toggle": "burger",
        "full_width": "stretch", "toggle_align": "right",
        "menu_typography_typography": "custom", "menu_typography_font_family": FONT,
        "menu_typography_font_size": px(13), "menu_typography_font_weight": "500",
        "color_menu_item": NAVY, "color_menu_item_hover": NAVY, "color_menu_item_active": NAVY,
        "pointer_color_menu_item_hover": NAVY, "pointer_color_menu_item_active": NAVY,
        "menu_space_between": px(16), "toggle_color": NAVY, "toggle_size": px(26),
        "color_dropdown_item": NAVY, "background_color_dropdown_item": WHITE})],
        justify="center", align="center", grow=True)
    cta_btn = box([btn("SOL·LICITAR INFORMACIÓ", "/contacte/", arrow=False, icon_cls="far fa-calendar-alt")])
    cta_btn["settings"]["hide_mobile"] = "hidden-mobile"
    root = box([logo, nav, cta_btn], row=True, inner=False, gap=20, padding=pad(0, 24),
               bg=WHITE, justify="space-between", align="center", min_h=76)
    root["settings"]["sticky"] = "top"
    root["settings"]["sticky_on"] = ["desktop", "tablet", "mobile"]
    root["settings"]["z_index"] = 99
    return [root]


def footer():
    def link_list(items):
        lst = [{"text": t, "link": {"url": u},
                "selected_icon": {"value": ic or "fas fa-angle-right", "library": "fa-solid"},
                "_id": _id()} for t, u, ic in items]
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
             link_list([(f"{ADDR1} · {ADDR2}", MAPS, "fas fa-map-marker-alt"),
                        (TEL, "tel:+34677858096", "fas fa-phone"),
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
