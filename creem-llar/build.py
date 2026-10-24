#!/usr/bin/env python3
"""
Creem Llar -> Elementor generator.

Cada component es defineix UNA sola vegada i d'ell se'n deriven:
  - el JSON de plantilla d'Elementor  (output/json/*.json)
  - la previsualització HTML          (output/html/*.html)
Així l'HTML i el JSON no poden divergir.
"""
import hashlib
import itertools
import json
import os
import shutil
from html import escape

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "output")

# URL on s'han de pujar les imatges a WordPress (Mitjans). Canvia-ho si cal.
BASE_URL = "https://proveswebsfigueres.com/creemllar/wp-content/uploads/2026/10/"
SITE = "/creemllar"  # prefix dels enllaços interns

# ---------------------------------------------------------------- tokens
C_DARK, C_TEXT, C_TAN, C_BROWN, C_NAVY = "#141413", "#5E5A57", "#E3C39C", "#5B452D", "#1F2A44"
C_BG, C_BG2, C_BG3, C_BEIGE, C_LINE = "#F8F5F0", "#F0EDE8", "#F5F4F1", "#F0E9E3", "#D9D2C9"
C_METODE = "#F1ECE6"
SANS, SERIF, SCRIPT, IGFONT = "DM Sans", "Playfair Display", "Mrs Saint Delafield", "Grand Hotel"

MENU = [("Inici", "/"), ("Projectes", "/projectes/"), ("Cuines", "/cuines/"), ("Banys", "/banys/"),
        ("Interiorisme", "/interiorisme/"), ("Parquets", "/parquets/"), ("Nosaltres", "/nosaltres/"),
        ("Contacte", "/contacte/")]
MENU_SLUG = "menu-principal"

# Ritme espacial: graella de 8 px, amplada de contingut i gutters comuns a totes les seccions
BOX = 1312                       # amplada màxima del contingut (centrat)
GUT = (64, 40, 24)               # marge lateral: escriptori / tauleta / mòbil


def snap(v, step=8):
    """Arrodoneix a múltiples de 8 (4 si el valor és petit). Accepta nombre, tupla o R."""
    if isinstance(v, R):
        return R(*[snap(x, step) if x is not None else None for x in (v.v[""], v.v["_tablet"], v.v["_mobile"])])
    if isinstance(v, (tuple, list)):
        return tuple(snap(x, step) for x in v)
    if isinstance(v, (int, float)):
        if v <= 0:
            return 0
        if v < 8:
            return 4 * max(1, round(v / 4))
        return int(step * int(v / step + 0.5))
    return v


def P(kind, top=None, bottom=None):
    """Padding de secció amb gutters comuns. kind: 'sec' (80/64/48) o 'band' (48/40/32)."""
    vt = {"sec": (48, 40, 32), "band": (48, 40, 32)}[kind]
    t = [top if top is not None else v for v in vt] if not isinstance(top, tuple) else list(top)
    b = [bottom if bottom is not None else v for v in vt] if not isinstance(bottom, tuple) else list(bottom)
    return R((t[0], GUT[0], b[0], GUT[0]), (t[1], GUT[1], b[1], GUT[1]), (t[2], GUT[2], b[2], GUT[2]))


# ---------------------------------------------------------------- infra
_cnt = itertools.count(1)


def nid():
    return hashlib.md5(f"cl{next(_cnt)}".encode()).hexdigest()[:7]


class R:
    """Valor responsive: R(d=desktop, t=tablet, m=mobile)."""

    def __init__(self, d, t=None, m=None):
        self.v = {"": d, "_tablet": t, "_mobile": m}


def devs(x):
    if isinstance(x, R):
        return {k: v for k, v in x.v.items() if v is not None}
    return {"": x}


def sz(n, unit="px"):
    return {"unit": unit, "size": n, "sizes": []}


def box(v):
    if isinstance(v, (int, float)):
        v = (v, v, v, v)
    t, r, b, l = v
    return {"unit": "px", "top": str(t), "right": str(r), "bottom": str(b), "left": str(l),
            "isLinked": t == r == b == l}


def boxcss(v):
    if isinstance(v, (int, float)):
        v = (v, v, v, v)
    return " ".join(f"{x}px" for x in v)


def gapv(n):
    return {"column": str(n), "row": str(n), "isLinked": True, "unit": "px", "size": n}


def img_url(key):
    return BASE_URL + key


def link(url, ext=False):
    return {"url": url, "is_external": "on" if ext else "", "nofollow": "", "custom_attributes": ""}


def icon_val(name):
    lib = {"fas": "fa-solid", "far": "fa-regular", "fab": "fa-brands"}[name.split()[0]]
    return {"value": name, "library": lib}


class Node:
    def __init__(self, el, html, rules, children=()):
        self.el, self.html, self.rules = el, html, rules
        self.children = list(children)


def put(s, key, v, conv=lambda x: x):
    for d, val in devs(v).items():
        s[key + d] = conv(val)


def rule(rules, sel, prop, v, conv=lambda x: x):
    for d, val in devs(v).items():
        rules.append((d, sel, f"{prop}:{conv(val)}"))


def typo(s, rules, sel, p, font=None, size=None, weight=None, lh=None, ls=None, tf=None, style=None):
    """Tipografia -> claus d'Elementor `<p>typography_*` + CSS equivalent."""
    s[f"{p}typography_typography"] = "custom"
    decl = []
    if font:
        s[f"{p}typography_font_family"] = font
        decl.append(f"font-family:'{font}',sans-serif")
    if size is not None:
        put(s, f"{p}typography_font_size", size, sz)
        rule(rules, sel, "font-size", size, lambda v: f"{v}px")
    if weight:
        s[f"{p}typography_font_weight"] = str(weight)
        decl.append(f"font-weight:{weight}")
    if lh is not None:
        put(s, f"{p}typography_line_height", lh, lambda v: sz(v, "em"))
        rule(rules, sel, "line-height", lh, lambda v: f"{v}em")
    if ls is not None:
        put(s, f"{p}typography_letter_spacing", ls, sz)
        rule(rules, sel, "letter-spacing", ls, lambda v: f"{v}px")
    if tf:
        s[f"{p}typography_text_transform"] = tf
        decl.append(f"text-transform:{tf}")
    if style:
        s[f"{p}typography_font_style"] = style
        decl.append(f"font-style:{style}")
    for dcl in decl:
        rules.append(("", sel, dcl))


def widget(wtype, settings, inner_html, rules, extra_cls=""):
    i = nid()
    cls = f"e{i}"
    el = {"id": i, "elType": "widget", "settings": settings, "elements": [], "widgetType": wtype}
    if extra_cls:
        settings["_css_classes"] = extra_cls
    html = (f'<div class="elementor-element {cls} elementor-widget elementor-widget-{wtype} {extra_cls}">'
            f'<div class="elementor-widget-container">{inner_html}</div></div>')
    return i, cls, el, html


# ---------------------------------------------------------------- widgets
def _rot(s, rules, sel, deg):
    """Rotació (Avançat → Transformar → Rotar) per als textos manuscrits inclinats."""
    s["_transform_rotate_popover"] = "transform"
    s["_transform_rotateZ_effect"] = {"unit": "px", "size": deg, "sizes": []}
    rules.append(("", sel, f"transform:rotate({deg}deg)"))


def heading(text, tag="h2", font=SANS, size=16, weight=400, color="#000000", lh=1.2, ls=None, tf=None,
            style=None, align=None, href=None, cls="", hide=None, margin=None, rot=None):
    s = {"title": text, "header_size": tag, "title_color": color}
    rules = []
    i = nid()
    sel = f".e{i} .elementor-heading-title"
    typo(s, rules, sel, "", font, size, weight, lh, ls, tf, style)
    rules.append(("", sel, f"color:{color}"))
    if align:
        put(s, "align", align)
        rule(rules, f".e{i}", "text-align", align)
    if href:
        s["link"] = link(href)
    _hide(s, rules, f".e{i}", hide)
    if rot:
        _rot(s, rules, f".e{i}", rot)
    if cls:
        s["_css_classes"] = cls
    el = {"id": i, "elType": "widget", "settings": s, "elements": [], "widgetType": "heading"}
    inner = f'<{tag} class="elementor-heading-title elementor-size-default">{text}</{tag}>'
    if href:
        inner = (f'<{tag} class="elementor-heading-title elementor-size-default">'
                 f'<a href="{SITE}{href}">{text}</a></{tag}>')
    html = (f'<div class="elementor-element e{i} elementor-widget elementor-widget-heading {cls}">'
            f'<div class="elementor-widget-container">{inner}</div></div>')
    return Node(el, html, rules)


def button(text, url="#", bg=None, color="#fff", size=15, weight=400, ls=0, pad=(14, 28, 14, 28),
           border=None, bw=(1, 1, 1, 1), radius=2, icon=None, tf=None, cls="", align=None, font=SANS,
           hover_bg=None, hover_color=None, hide=None):
    i = nid()
    sel = f".e{i} .elementor-button"
    pad = snap(pad, 4)
    bb = bw[2] if border else 0
    mpv = max(pad[0], -(-(44 - size - bb) // 2))          # alçada mínima 44 px en mòbil
    mpad = (mpv, pad[1], mpv, pad[3])
    s = {"text": text, "link": link(url), "button_text_color": color,
         "background_color": bg or "#FFFFFF00",
         "border_radius": box(radius), "size": "sm"}
    rules = []
    typo(s, rules, sel, "", font, size, weight, 1, ls, tf)
    put(s, "text_padding", R(pad, None, mpad), box)
    rules += [("", sel, f"color:{color}"), ("", sel, f"background-color:{bg or 'transparent'}"),
              ("", sel, f"border-radius:{boxcss(radius)}")]
    rule(rules, sel, "padding", R(pad, None, mpad), boxcss)
    if border:
        s["border_border"] = "solid"
        s["border_width"] = box(bw)
        s["border_color"] = border
        rules += [("", sel, f"border:solid {border}"), ("", sel, f"border-width:{boxcss(bw)}")]
    s["button_background_hover_color"] = hover_bg or bg or "#FFFFFF00"
    s["hover_color"] = hover_color or color
    rules.append(("", sel + ":hover", f"background-color:{hover_bg or bg or 'transparent'}"))
    rules.append(("", sel + ":hover", f"color:{hover_color or color}"))
    if align:
        put(s, "align", align)
        rule(rules, f".e{i} .elementor-button-wrapper", "text-align", align)
    ic = ""
    if icon:
        s["selected_icon"] = icon_val(icon)
        s["icon_align"] = "right"
        s["icon_indent"] = sz(10)
        ic = f'<span class="elementor-button-icon"><i class="{icon}"></i></span>'
    _hide(s, rules, f".e{i}", hide)
    if cls:
        s["_css_classes"] = cls
    el = {"id": i, "elType": "widget", "settings": s, "elements": [], "widgetType": "button"}
    href = url if url.startswith(("#", "http", "tel:", "mailto:")) else SITE + url
    html = (f'<div class="elementor-element e{i} elementor-widget elementor-widget-button {cls}">'
            f'<div class="elementor-widget-container"><div class="elementor-button-wrapper">'
            f'<a class="elementor-button elementor-button-link elementor-size-sm" href="{href}">'
            f'<span class="elementor-button-content-wrapper"><span class="elementor-button-text">{text}</span>{ic}'
            f'</span></a></div></div></div>')
    return Node(el, html, rules)


def icon(name, size=30, color="#000", align=None, pos=None, link_url=None, view=None, bgc=None, pad=None,
         shape=None, cls=""):
    """Widget Icona. view='stacked' + shape='circle' => botó rodó (WhatsApp)."""
    i = nid()
    s = {"selected_icon": icon_val(name), "primary_color": color, "size": sz(size)}
    rules = []
    sel = f".e{i} .elementor-icon"
    rules += [("", sel, f"font-size:{size}px"), ("", sel, f"color:{color}"), ("", sel, "line-height:1")]
    if align:
        put(s, "align", align)
        rule(rules, f".e{i} .elementor-icon-wrapper", "text-align", align)
    if view == "stacked":
        s["view"] = "stacked"
        s["shape"] = shape or "circle"
        s["secondary_color"] = "#FFFFFF"
        s["primary_color"] = bgc
        s["icon_padding"] = sz(pad)
        rules += [("", sel, f"background-color:{bgc}"), ("", sel, "color:#fff"),
                  ("", sel, f"padding:{pad}px"), ("", sel, "border-radius:50%"),
                  ("", sel, "display:inline-flex"), ("", sel, "box-shadow:0 4px 14px rgba(0,0,0,.25)")]
    if link_url:
        s["link"] = link(link_url, True)
    if pos:
        s["_position"] = "fixed"
        s["_offset_orientation_h"] = "end"
        s["_offset_x"] = sz(pos[0])
        s["_offset_orientation_v"] = "end"
        s["_offset_y"] = sz(pos[1])
        s["_z_index"] = 999
        rules += [("", f".e{i}", "position:fixed"), ("", f".e{i}", f"right:{pos[0]}px"),
                  ("", f".e{i}", f"bottom:{pos[1]}px"), ("", f".e{i}", "z-index:999")]
    if cls:
        s["_css_classes"] = cls
    el = {"id": i, "elType": "widget", "settings": s, "elements": [], "widgetType": "icon"}
    ic = f'<i class="{name}"></i>'
    if link_url:
        ic = f'<a href="{link_url}" target="_blank">{ic}</a>'
    html = (f'<div class="elementor-element e{i} elementor-widget elementor-widget-icon {cls}">'
            f'<div class="elementor-widget-container"><div class="elementor-icon-wrapper">'
            f'<div class="elementor-icon{" elementor-view-stacked" if view else ""}">{ic}</div></div></div></div>')
    return Node(el, html, rules)


def image(key, h=None, w=100, alt="", fit="cover", align=None, wunit="%", cls="", hide=None, radius=None,
          href=None, lightbox=False):
    i = nid()
    s = {"image": {"url": img_url(key), "id": "", "size": "", "alt": alt, "source": "library"},
         "image_size": "full", "width": sz(w, wunit), "object-fit": fit}
    rules = []
    sel = f".e{i} img"
    rules.append(("", sel, f"width:{w}{wunit}"))
    if h is not None:
        put(s, "height", h, sz)
        rule(rules, sel, "height", h, lambda v: f"{v}px")
        rules.append(("", sel, f"object-fit:{fit}"))
    if radius:
        s["image_border_radius"] = box(radius)
        rules.append(("", sel, f"border-radius:{boxcss(radius)}"))
    if align:
        put(s, "align", align)
        rule(rules, f".e{i}", "text-align", align)
    _hide(s, rules, f".e{i}", hide)
    if cls:
        s["_css_classes"] = cls
    tag = f'<img src="../../assets/{key}" alt="{escape(alt)}">'
    if href:
        s["link_to"] = "custom"
        s["link"] = link(href)
        tag = f'<a href="{SITE}{href}">{tag}</a>'
    elif lightbox:
        s["link_to"] = "file"
        s["open_lightbox"] = "yes"
        tag = f'<a href="../../assets/{key}" class="elementor-lightbox">{tag}</a>'
    el = {"id": i, "elType": "widget", "settings": s, "elements": [], "widgetType": "image"}
    html = (f'<div class="elementor-element e{i} elementor-widget elementor-widget-image {cls}">'
            f'<div class="elementor-widget-container">{tag}</div></div>')
    return Node(el, html, rules)


def icon_list(items, icon_color="#000", icon_size=14, color="#000", font=SANS, size=15, weight=400, ls=None,
              tf=None, indent=8, cls="", space=0):
    """items: [(text, icon, url|None)]"""
    i = nid()
    s = {"icon_list": [], "view": "traditional", "icon_color": icon_color, "icon_size": sz(icon_size),
         "text_color": color, "text_indent": sz(indent), "space_between": sz(space)}
    rules = []
    sel = f".e{i} .elementor-icon-list-text"
    typo(s, rules, sel, "icon_", font, size, weight, 1.3, ls, tf)
    rules += [("", sel, f"color:{color}"), ("", f".e{i} .elementor-icon-list-icon", f"color:{icon_color}"),
              ("", f".e{i} .elementor-icon-list-icon", f"font-size:{icon_size}px"),
              ("", sel, f"padding-left:{indent}px"),
              ("", f".e{i} .elementor-icon-list-item:not(:last-child)", f"margin-bottom:{space}px")]
    lis = ""
    for text, ic, url in items:
        s["icon_list"].append({"text": text, "selected_icon": icon_val(ic), "_id": nid(),
                               "link": link(url or "")})
        t = f'<span class="elementor-icon-list-text">{text}</span>'
        if url:
            t = f'<a href="{url}">{t}</a>'
        lis += (f'<li class="elementor-icon-list-item"><span class="elementor-icon-list-icon">'
                f'<i class="{ic}"></i></span>{t}</li>')
    if cls:
        s["_css_classes"] = cls
    el = {"id": i, "elType": "widget", "settings": s, "elements": [], "widgetType": "icon-list"}
    html = (f'<div class="elementor-element e{i} elementor-widget elementor-widget-icon-list {cls}">'
            f'<div class="elementor-widget-container"><ul class="elementor-icon-list-items">{lis}</ul></div></div>')
    return Node(el, html, rules)


def divider(w=100, weight=1, color=C_LINE, grow=False, hide=None, rot=None, wunit="%"):
    i = nid()
    s = {"style": "solid", "weight": sz(weight), "color": color, "width": sz(w, wunit), "gap": sz(0)}
    rules = [("", f".e{i} .elementor-divider", "padding:0"),
             ("", f".e{i} .elementor-divider-separator", f"border-top:{weight}px solid {color}"),
             ("", f".e{i} .elementor-divider-separator", f"width:{w}{wunit}")]
    if grow:
        s["_flex_size"] = "grow"
        rules.append(("", f".e{i}", "flex:1 1 auto"))
    _hide(s, rules, f".e{i}", hide)
    if rot:
        _rot(s, rules, f".e{i}", rot)
    el = {"id": i, "elType": "widget", "settings": s, "elements": [], "widgetType": "divider"}
    html = (f'<div class="elementor-element e{i} elementor-widget elementor-widget-divider">'
            f'<div class="elementor-widget-container"><div class="elementor-divider">'
            f'<span class="elementor-divider-separator"></span></div></div></div>')
    return Node(el, html, rules)


def nav_menu(active="Inici", size=15, weight=300, color="#fff", space=4, vpad=5, hpad=9):
    i = nid()
    s = {"layout": "horizontal", "menu": MENU_SLUG, "align_items": "center", "pointer": "framed",
         "animation_framed": "fade", "color_menu_item": color, "color_menu_item_hover": color,
         "pointer_color_menu_item_hover": color, "color_menu_item_active": color,
         "pointer_color_menu_item_active": color, "pointer_width": sz(1),
         "padding_horizontal_menu_item": sz(hpad), "padding_vertical_menu_item": sz(vpad),
         "menu_space_between": sz(space), "dropdown": "tablet", "toggle": "burger",
         "full_width": "stretch", "toggle_color": color,
         "dropdown_typography_typography": "custom", "background_color_dropdown_item": "#2A221C",
         "color_dropdown_item": "#FFFFFF"}
    rules = []
    sel = f".e{i} .elementor-nav-menu a"
    typo(s, rules, sel, "menu_", SANS, size, weight, 1.2)
    li = ""
    for name, url in MENU:
        c = " active" if name == active else ""
        li += f'<li class="menu-item{c}"><a class="elementor-item{c}" href="{SITE}{url}">{name}</a></li>'
    rules += [("", sel, f"color:{color}"), ("", sel, f"padding:{vpad}px {hpad}px"),
              ("", f".e{i} .elementor-nav-menu", f"gap:{space}px")]
    el = {"id": i, "elType": "widget", "settings": s, "elements": [], "widgetType": "nav-menu"}
    html = (f'<div class="elementor-element e{i} elementor-widget elementor-widget-nav-menu">'
            f'<div class="elementor-widget-container"><nav class="elementor-nav-menu--main">'
            f'<ul class="elementor-nav-menu">{li}</ul></nav>'
            f'<button class="elementor-menu-toggle" aria-label="Menú" onclick="this.closest(\'.elementor-widget-nav-menu\').classList.toggle(\'open\')">'
            f'<i class="fas fa-bars"></i></button></div></div>')
    return Node(el, html, rules)


def html_widget(code):
    i = nid()
    el = {"id": i, "elType": "widget", "settings": {"html": code}, "elements": [], "widgetType": "html"}
    html = (f'<div class="elementor-element e{i} elementor-widget elementor-widget-html">'
            f'<div class="elementor-widget-container">{code}</div></div>')
    return Node(el, html, [])


def _hide(s, rules, sel, hide):
    if not hide:
        return
    for h in hide:
        s[f"hide_{h}"] = f"hidden-{h}"
        if h == "tablet":
            rules.append(("_tablet_only", sel, "display:none!important"))
        elif h == "mobile":
            rules.append(("_mobile", sel, "display:none!important"))
        elif h == "desktop":
            rules.append(("_desktop_only", sel, "display:none!important"))


# ---------------------------------------------------------------- container
def container(children, dir="column", gap=20, justify="flex-start", align="stretch", wrap=False, pad=0,
              boxed=None, bg=None, bgimg=None, bgpos="center center", grad=None, overlay=None, minh=None,
              width=None, grid=None, border=None, bw=None, radius=None, pos=None, z=None, cls="",
              inner=False, hide=None, margin=None, hold=False):
    i = nid()
    cls_e = f"e{i}"
    gap, pad = snap(gap), snap(pad)
    if margin is not None:
        margin = snap(margin)
    s, rules = {}, []
    outer = f".{cls_e}"
    lay = f".{cls_e}>.e-con-inner" if boxed else outer

    if boxed:
        s["content_width"] = "boxed"
        s["boxed_width"] = sz(boxed)
        rules.append(("", lay, f"max-width:{boxed}px"))
    else:
        s["content_width"] = "full"

    if grid:
        s["container_type"] = "grid"
        cols, rows = grid
        put(s, "grid_columns_grid", cols, lambda v: sz(v, "fr"))
        put(s, "grid_rows_grid", rows, lambda v: sz(v, "fr"))
        put(s, "grid_gaps", gap, gapv)
        rules.append(("", lay, "display:grid"))
        rule(rules, lay, "grid-template-columns", cols, lambda v: f"repeat({v},1fr)")
        rule(rules, lay, "grid-template-rows", rows, lambda v: f"repeat({v},1fr)")
        rule(rules, lay, "gap", gap, lambda v: f"{v}px")
        s["grid_auto_flow"] = "row"
        s["grid_justify_items"] = "stretch" if align == "stretch" else align
        s["grid_align_items"] = "stretch" if align == "stretch" else align
        rules.append(("", lay, f"align-items:{align}"))
    else:
        put(s, "flex_direction", dir)
        rule(rules, lay, "flex-direction", dir)
        put(s, "flex_gap", gap, gapv)
        rule(rules, lay, "gap", gap, lambda v: f"{v}px")
        put(s, "flex_justify_content", justify)
        rule(rules, lay, "justify-content", justify)
        put(s, "flex_align_items", align)
        rule(rules, lay, "align-items", align)
        if wrap:
            s["flex_wrap"] = "wrap"
            rules.append(("", lay, "flex-wrap:wrap"))

    put(s, "padding", pad, box)
    rule(rules, outer, "padding", pad, boxcss)
    if margin is not None:
        put(s, "margin", margin, box)
        rule(rules, outer, "margin", margin, boxcss)
    if minh is not None:
        s["height"] = "min-height"
        put(s, "min_height", minh, sz)
        rule(rules, outer, "min-height", minh, lambda v: f"{v}px")
    if width is not None:
        put(s, "width", width, lambda v: sz(v[0], v[1]) if isinstance(v, tuple) else sz(v, "%"))
        rule(rules, outer, "--w", width, lambda v: f"{v[0]}{v[1]}" if isinstance(v, tuple) else f"{v}%")
    if bg or bgimg or overlay or grad:
        s["background_background"] = "gradient" if grad else "classic"
    if bg:
        s["background_color"] = bg
        rules.append(("", outer, f"background-color:{bg}"))
    if grad:
        s["background_color"], s["background_color_b"] = grad["a"], grad["b"]
        s["background_color_stop"], s["background_color_b_stop"] = sz(grad.get("ap", 0), "%"), sz(grad.get("bp", 100), "%")
        s["background_gradient_type"] = "linear"
        s["background_gradient_angle"] = sz(grad["angle"], "deg")
        rules.append(("", outer, f"background-image:linear-gradient({grad['angle']}deg,{grad['a']} {grad.get('ap',0)}%,{grad['b']} {grad.get('bp',100)}%)"))
    if bgimg:
        s["background_image"] = {"url": img_url(bgimg), "id": "", "size": "", "alt": "", "source": "library"}
        s["background_position"], s["background_repeat"], s["background_size"] = bgpos, "no-repeat", "cover"
        rules.append(("", outer, f"background-image:url(../../assets/{bgimg})"))
        rules.append(("", outer, f"background-position:{bgpos}"))
        rules.append(("", outer, "background-repeat:no-repeat"))
        rules.append(("", outer, "background-size:cover"))
    has_ov = False
    if overlay:
        has_ov = True
        s["background_overlay_background"] = "gradient"
        s["background_overlay_color"] = overlay["a"]
        s["background_overlay_color_b"] = overlay["b"]
        s["background_overlay_color_stop"] = sz(overlay.get("ap", 0), "%")
        s["background_overlay_color_b_stop"] = sz(overlay.get("bp", 100), "%")
        s["background_overlay_gradient_type"] = "linear"
        s["background_overlay_gradient_angle"] = sz(overlay["angle"], "deg")
        s["background_overlay_opacity"] = sz(1)
        rules.append(("", f"{outer}::before",
                      f"background-image:linear-gradient({overlay['angle']}deg,{overlay['a']} {overlay.get('ap',0)}%,{overlay['b']} {overlay.get('bp',100)}%)"))
    if border:
        s["border_border"] = "solid"
        put(s, "border_width", bw, box)
        s["border_color"] = border
        rules.append(("", outer, f"border-style:solid;border-color:{border}"))
        rule(rules, outer, "border-width", bw, boxcss)
    if radius is not None:
        s["border_radius"] = box(radius)
        rules.append(("", outer, f"border-radius:{boxcss(radius)}"))
    if pos:
        s["position"] = s["_position"] = pos["type"]
        s["_offset_orientation_h"], s["_offset_x"] = "start", sz(pos.get("x", 0))
        s["_offset_orientation_v"], s["_offset_y"] = "start", sz(pos.get("y", 0))
        s["width"] = sz(100, "%")
        rules += [("", outer, f"position:{pos['type']}"), ("", outer, f"left:{pos.get('x',0)}px"),
                  ("", outer, f"top:{pos.get('y',0)}px"), ("", outer, "--w:100%")]
    if z is not None:
        s["z_index"] = s["_z_index"] = z
        rules.append(("", outer, f"z-index:{z}"))
    _hide(s, rules, outer, hide)
    if cls:
        s["css_classes"] = cls
    el = {"id": i, "elType": "container", "settings": s, "elements": [c.el for c in children],
          "isInner": inner}
    body = "".join(c.html for c in children)
    klass = f"e-con {cls_e} {'e-child' if inner else 'e-parent'} {'has-ov' if has_ov else ''} {cls}"
    if boxed:
        html = f'<div class="{klass}"><div class="e-con-inner">{body}</div></div>'
    else:
        html = f'<div class="{klass}">{body}</div>'
    allrules = list(rules)
    for c in children:
        allrules += c.rules
    return Node(el, html, allrules, children)


# ================================================================ SECCIONS
def hdr(active):
    logo = image("logo-creemllar.jpg", w=180, wunit="px", alt="Creem Llar - espais per viure",
                 hide=None)
    nav = nav_menu(active)
    btn = button("Demana pressupost", "/contacte/", bg=C_BROWN, color="#fff", size=18, weight=400,
                 pad=(14, 24, 14, 24), border="#8C7358", radius=2, hide=["mobile"])
    return container([logo, nav, btn], dir="row", justify="space-between", align="center",
                     gap=24, boxed=1440, pad=R((16, 20, 16, 96), (16, GUT[1], 16, GUT[1]), (16, GUT[2], 16, GUT[2])),
                     pos={"type": "absolute", "x": 0, "y": 0}, z=100, cls="cl-header")


def ftr():
    eyebrow = heading("COMENCEM?", "p", SANS, 13, 400, "#FFFFFFCC", 1.2, 2.5)
    h = heading("Parlem del teu projecte", "h2", SERIF, R(49.4, 40, 34), 400, "#FFFFFF", 1.15)
    p = heading("Explica'ns la teva idea i t'assessorem sense compromís.", "p", SANS, 17.5, 400,
                "#FFFFFFE6", 1.4)
    left = container([eyebrow, h, p], gap=12, inner=True, width=R(50, 100), pad=0)

    cta = button("Demana pressupost", "/contacte/", bg="#F7F4F0", color=C_DARK, size=17, weight=400,
                 pad=(16, 34, 16, 34), radius=2, icon="fas fa-long-arrow-alt-right")
    items = [("+34 972 684 896", "fas fa-phone-alt", "tel:+34972684896"),
             ("info@creemllar.com", "far fa-envelope", "mailto:info@creemllar.com"),
             ("Figueres, Girona", "fas fa-map-marker-alt", None),
             ("+34 972 519 324", "fas fa-phone-alt", "tel:+34972519324"),
             ("info@creemllar.com", "far fa-envelope", "mailto:info@creemllar.com"),
             ("Banyoles, Girona", "fas fa-map-marker-alt", None)]
    cells = [icon_list([it], "#FFFFFF", 15, "#FFFFFFD9", SANS, 15, 300) for it in items]
    contact = container(cells, grid=(R(3, 2, 1), R(2, 3, 6)), gap=R(16, 16, 8), inner=True, pad=0)
    right = container([cta, contact], gap=28, inner=True, width=R((480, "px"), 100), pad=0,
                      align=R("flex-start", "flex-start", "flex-start"))
    top = container([left, right], dir=R("row", "column", "column"), justify="space-between", align="center",
                    gap=R(60, 36, 32), inner=True, pad=0)
    copy = container([heading("Copyright CREEM LLAR", "p", SANS, 14, 300, "#FFFFFFB3", 1.2),
                      heading("Política de privacitat", "p", SANS, 14, 300, "#FFFFFFB3", 1.2,
                              href="/politica-de-privacitat/")],
                     dir="row", justify="space-between", align="center", gap=16, inner=True, pad=0)
    wa = icon("fab fa-whatsapp", 32, "#fff", pos=(24, 24), link_url="https://wa.me/34972684896",
              view="stacked", bgc="#25D366", pad=15, shape="circle")
    return container([top, copy, wa], gap=32, boxed=BOX,
                     pad=R((48, 98, 24, 98), (40, GUT[1], 24, GUT[1]), (32, GUT[2], 24, GUT[2])),
                     cls="cl-footer")


def ftr_wrap():
    """El footer porta fons a tot l'ample: contenidor exterior ple + contingut boxed."""
    inner = ftr()
    return container([inner], gap=0, pad=0,
                     grad={"a": "#4B3F36", "b": "#2A2420", "angle": 125, "ap": 0, "bp": 100}, cls="cl-footer-wrap")


def hero(img, ph, p_text, btn_text, btn_url, eyebrow=None, minh=572, py=(112, 48), arrow=True,
         title="Espais<br>fets a mida"):
    kids = []
    if eyebrow:
        kids.append(heading(eyebrow, "p", SANS, R(20, 18, 15), 400, "#FFFFFFE6", 1.2, R(4.5, 4, 3)))
    kids.append(heading(title, "h1", SANS, R(93, 76, 52), 300, "#FFFFFF", R(0.88, 0.9, 0.95)))
    kids.append(heading(p_text, "p", SANS, R(28, 24, 19), 400, "#FFFFFFF2", R(1.4, 1.35, 1.3)))
    kids.append(button(btn_text, btn_url, bg=C_TAN, color="#2B2118", size=16, weight=500, ls=1.5,
                       pad=(20, 40, 20, 40), radius=1, tf="uppercase" if arrow else None,
                       icon="fas fa-long-arrow-alt-right"))
    text = container(kids, gap=R(24, 24, 16), justify="center", align="flex-start", inner=True,
                     pad=R((0, 0, 0, 64), (0, 0, 0, 0), (0, 0, 0, 0)), width=R(60, 100))
    return container([text], gap=0, justify="center", align="flex-start", boxed=BOX,
                     pad=R((py[0], GUT[0], py[1], GUT[0]), (112, GUT[1], 48, GUT[1]), (112, GUT[2], 48, GUT[2])),
                     minh=R(minh, 520, 520), bgimg=img, bgpos="right center", cls="cl-hero",
                     overlay={"a": "#1A120CCC", "b": "#1A120C00", "angle": 90, "ap": 0, "bp": 62})


def tile(img, title, text):
    return container([image(img, h=R(229, 220, 200), alt=title),
                      heading(title, "h3", SANS, 25.5, 500, "#141413", 1.2),
                      heading(text, "p", SANS, R(19.4, 18, 17), 400, C_TEXT, 1.22)],
                     gap=10, inner=True, pad=0, align="stretch")


def categories():
    tiles = [tile("cat-cuines.jpg", "Cuines", "Dissenys funcionals i elegants per al teu dia a dia."),
             tile("cat-banys.jpg", "Banys", "Espais moderns, còmodes i plens de benestar."),
             tile("cat-interiorisme.jpg", "Interiorisme", "Solucions a mida per a cada estil de vida."),
             tile("cat-reformes.jpg", "Reformes", "Transformem els teus espais amb garantia i experiència.")]
    grid = container(tiles, grid=(R(4, 2, 1), 1), gap=R(37, 28, 28), inner=True, pad=0)
    return container([grid], boxed=BOX, bg=C_BG2, pad=P("band"),
                     gap=0, cls="cl-cats")


def props():
    data = [("fas fa-pencil-ruler", "Disseny a mida", "Idees que s'adapten a tu"),
            ("fas fa-home", "Experiència local", "A Figueres i Banyoles"),
            ("fas fa-leaf", "Qualitat i confiança", "Materials i professionals"),
            ("fas fa-users", "Acompanyament total", "De la idea fins al resultat")]
    cells = []
    for n, (ic, t, d) in enumerate(data):
        last = n == 3
        cells.append(container([icon(ic, 32, "#2B2B2B", align="center"),
                                heading(t, "h3", SERIF, 20, 400, "#141413", 1.2, align="center"),
                                heading(d, "p", SANS, 15.3, 400, C_TEXT, 1.4, align="center")],
                               gap=10, inner=True, align="center", margin=R((32, 0, 32, 0), (24, 0, 24, 0), (0, 0, 0, 0)),
                               pad=R((8, 24, 8, 24), (8, 24, 8, 24), (24, 16, 24, 16)),
                               border=C_LINE,
                               bw=R((0, 0 if last else 1, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0))))
    grid = container(cells, grid=(R(4, 2, 1), 1), gap=0, inner=True, pad=0)
    return container([grid], boxed=BOX, bg=C_BG3, pad=P("band", top=0, bottom=0),
                     gap=0, cls="cl-props")


def feat_card(img, title, city, arrow_url="/projectes/", href=None):
    text = container([heading(title, "h3", SERIF, 21.5, 400, "#141413", 1.2, href=href),
                      heading(city.upper(), "p", SANS, 14, 400, C_TEXT, 1.2, 2.4)],
                     gap=6, inner=True, pad=0, width=80)
    row = container([text, icon("fas fa-long-arrow-alt-right", 22, "#141413", align="right")],
                    dir="row", justify="space-between", align="center", gap=10, inner=True, pad=0)
    return container([image(img, h=R(262, 240, 220), alt=title, href=href), row], gap=14, inner=True, pad=0)


def featured():
    head_l = container([heading("PROJECTES DESTACATS", "p", SANS, 15, 400, C_TEXT, 1.2, 3.9),
                        heading("Espais que inspiren", "h2", SERIF, R(50, 44, 36), 400, "#111111", 1.1)],
                       gap=8, inner=True, pad=0, width=R(60, 60, 100))
    head_r = button("Veure tots els projectes", "/projectes/", None, C_DARK, 14, 400, 0, (4, 0, 4, 0),
                    border=C_DARK, bw=(0, 0, 1, 0), radius=0, icon="fas fa-long-arrow-alt-right")
    head = container([head_l, head_r], dir=R("row", "row", "column"), justify="space-between",
                     align=R("flex-end", "flex-end", "flex-start"), gap=20, inner=True, pad=0)
    cards = [feat_card("home-proj-1.jpg", "Cuina contemporània", "Figueres", href="/projecte/"),
             feat_card("home-proj-2.jpg", "Bany amb caràcter", "Banyoles"),
             feat_card("home-proj-3.jpg", "Reforma integral", "Figueres")]
    grid = container(cards, grid=(R(3, 2, 1), 1), gap=R(18, 18, 28), inner=True, pad=0)
    return container([head, grid], gap=26, boxed=BOX, bg="#FFFFFF",
                     pad=P("sec"), cls="cl-featured")


def metode(titol="Un procés senzill,<br>amb grans resultats", passos=None):
    left = container([heading("EL NOSTRE MÈTODE", "p", SANS, 15, 400, C_TEXT, 1.2, 3.1),
                      heading(titol, "h2", SERIF, R(41.8, 36, 32), 400, C_NAVY, 1.2)],
                     gap=14, inner=True, width=R(30, 100), pad=0)
    steps = []
    p = passos or [("Escoltem", "Analitzem les teves necessitats i et proposem idees a mida."),
                   ("Dissenyem", "Planifiquem cada detall amb rigor i transparència."),
                   ("Fem realitat", "Ens ocupem de tot perquè només gaudeixis del resultat.")]
    data = [("01", "far fa-comment") + p[0], ("02", "far fa-file-alt") + p[1], ("03", "fas fa-wrench") + p[2]]
    for num, ic, t, d in data:
        top = container([heading(num, "p", SERIF, 34, 400, "#5A5550", 1, style="italic"),
                         icon(ic, 30, "#2B2B2B"), divider(98, 1, "#8F877D", wunit="px")],
                        dir="row", align="center", gap=14, inner=True, pad=0)
        steps.append(container([top, heading(t, "h3", SANS, 18.5, 500, "#141413", 1.2),
                                heading(d, "p", SANS, 15.3, 400, C_TEXT, 1.6)],
                               gap=10, inner=True, pad=0))
    steps_grid = container(steps, grid=(R(3, 1, 1), 1), gap=R(34, 28, 28), inner=True,
                           pad=R((0, 0, 0, 44), (0, 0, 0, 0), (0, 0, 0, 0)), border=C_LINE,
                           bw=R((0, 0, 0, 1), (0, 0, 0, 0), (0, 0, 0, 0)), width=R(70, 100))
    row = container([left, steps_grid], dir=R("row", "column", "column"), align="center",
                    gap=R(44, 32, 28), inner=True, pad=0)
    return container([row], boxed=BOX, bg=C_METODE, gap=0,
                     pad=P("band"), cls="cl-metode")


def quote(text, size=42):
    """Frase manuscrita del PDF: lletra fina i inclinada (~ -8°), amb el traç curt a sota."""
    return container([heading(text, "p", SCRIPT, R(size, size - 4, size - 8), 400, "#3A3A3A", 1.05, rot=-8),
                      divider(50, 1, "#3A3A3A", rot=-8)], gap=16, inner=True, pad=0, width=R((170, "px"), 100),
                     align="flex-start", hide=None)


def interiorisme(titulo="Dissenyem espais<br>per cada estil de vida", eyebrow="INTERIORISME A FIGUERES | BANYOLES",
                 text="Creem cuines, banys i espais que combinen estètica, funcionalitat i benestar, sempre "
                      "adaptats al teu estil de vida i a l'entorn on vius.",
                 boto="Parlem del teu projecte", cita="“ La teva llar,<br>el nostre<br>compromís ”", img_key="interiorisme.jpg"):
    img = container([], inner=True, width=R(45.5, 100), bgimg=img_key, minh=R(434, 300),
                    pad=0)
    kids = [heading(eyebrow, "p", SANS, 15, 400, "#4A443F", 1.2, 3.2),
            heading(titulo, "h2", SERIF, R(43.5, 40, 34), 400, "#141413", 1.26),
            heading(text, "p", SANS, 17, 400, "#2E2A27", 1.6),
            button(boto, "/contacte/", bg=C_DARK, color="#fff", size=16, weight=400,
                   pad=(18, 34, 18, 34), radius=1, icon="fas fa-long-arrow-alt-right")]
    text = container(kids, gap=24, inner=True, pad=0, width=R((440, "px"), 100), align="flex-start")
    q = quote(cita, 42)
    right = container([text, q], dir=R("row", "column", "column"), align=R("center", "flex-start", "flex-start"),
                      gap=R(30, 28, 24), inner=True, width=R(54.5, 100), bg=C_BEIGE,
                      pad=R((40, 56, 40, 56), (48, 40, 48, 40), (40, 24, 40, 24)), justify="center")
    return container([img, right], dir=R("row", "column", "column"), gap=0, align="stretch", pad=0,
                     cls="cl-split")


def equip(titol="Un equip al teu costat", text=None, enllac=True):
    img = container([image("equip.jpg", h=R(255, 240, 220), alt="L'equip de Creem Llar")],
                    inner=True, width=R((490, "px"), 100), pad=0)
    text = container([heading("PERSONES QUE FAN POSSIBLE CREEM LLAR", "p", SANS, 15, 400, "#4A443F", 1.2, 2.1),
                      heading(titol, "h2", SERIF, R(36, 32, 30), 400, "#141413", 1.15),
                      heading(text or ("Som un estudi d'interiorisme amb arrels a Figueres, apassionats pel disseny i la "
                                       "qualitat. Treballem amb proximitat, escolta i compromís per crear espais únics, "
                                       "pensats per a tu."), "p", SANS, 15.6, 400, "#2E2A27", 1.76),
                      ] + ([button("Coneix el nostre equip", "/nosaltres/", None, C_DARK, 14, 400, 0, (4, 0, 4, 0),
                             border=C_DARK, bw=(0, 0, 1, 0), radius=0, icon="fas fa-long-arrow-alt-right")] if enllac else []),
                     gap=16, inner=True, pad=0, width=R((560, "px"), 100), align="flex-start")
    q = quote("“ Llar<br>és molt més<br>que un lloc ”", 42)
    return container([img, text, q], dir=R("row", "column", "column"), align=R("center", "flex-start", "flex-start"),
                     gap=R(48, 28, 24), boxed=BOX, bg="#FFFFFF",
                     pad=P("band"), cls="cl-team")


def insta_head():
    ico = icon("fab fa-instagram", 34, "#E1306C")
    name = heading("Instagram", "p", IGFONT, 30, 400, "#262626", 1)
    txt = heading("SEGUEIX-NOS A INSTAGRAM I ESTIGUES ACTUALITZAT DE LES TENDÈNCIES", "p", "Josefin Sans",
                  R(18.5, 16, 13), 400, "#141413", 1.3, 0)
    return container([container([ico, name], dir="row", align="center", gap=8, inner=True, pad=0,
                                 width=R(17, 100)), txt],
                     dir=R("row", "row", "column"), align=R("center", "center", "flex-start"), gap=R(36, 24, 12),
                     boxed=BOX, bg="#FFFFFF", pad=P("band", top=(8, 8, 8), bottom=(8, 8, 8)),
                     cls="cl-ig-head")


def insta_feed():
    feed = image("instagram-feed.jpg", h=None, w=100, alt="Feed d'Instagram de Creem Llar")
    more = button("Veure més", "https://www.instagram.com/", None, "#FFFFFF", 14, 400, 0, (6, 0, 6, 0),
                  radius=0, align="right")
    return container([feed, more], gap=0, boxed=BOX, bg="#0A0D12", pad=P("band", top=0, bottom=(16, 16, 8)),
                     cls="cl-ig-feed")


# ---------------------------------------------------------------- projectes
PROJECTS = [("Cuina moderna amb illa", "Banyoles", "cuina"), ("Cuina contemporània", "Figueres", "cuina"),
            ("Cuina oberta al menjador", "Porqueres", "cuina"), ("Cuina en tons naturals", "Besalú", "cuina"),
            ("Cuina minimalista", "Cornellà del Terri", "cuina"), ("Cuina amb fusta i pedra", "Roses", "cuina"),
            ("Bany d'estil natural", "Banyoles", "banys"), ("Bany amb dutxa", "Serinyà", "banys"),
            ("Bany contemporani", "Figueres", "banys"), ("Interiorisme integral", "Fontcoberta", "interiorisme"),
            ("Sala d'estar i menjador", "Castelló d'Empúries", "interiorisme"),
            ("Dormitori principal", "Navata", "interiorisme"), ("Reforma casa de poble", "Llers", "reformes"),
            ("Parquet d'interior", "Empuriabrava", "parquets"), ("Reforma integral", "L'Escala", "reformes")]

FILTER_JS = """<style>
.cl-filter.is-active .elementor-button{background-color:#141413!important;color:#fff!important;border-color:#141413!important}
.cl-hide{display:none!important}
</style>
<script>
(function(){
  function init(){
    var btns=document.querySelectorAll('.cl-filter a'), cards=document.querySelectorAll('.cl-card');
    btns.forEach(function(a){
      a.addEventListener('click',function(e){
        e.preventDefault();
        var f=(a.getAttribute('href')||'#tots').replace('#','');
        document.querySelectorAll('.cl-filter').forEach(function(w){w.classList.remove('is-active');});
        a.closest('.cl-filter').classList.add('is-active');
        cards.forEach(function(c){c.classList.toggle('cl-hide', f!=='tots' && !c.classList.contains('cat-'+f));});
      });
    });
  }
  if(document.readyState!=='loading'){init();}else{document.addEventListener('DOMContentLoaded',init);}
})();
</script>"""


def proj_card(n, title, city, cat):
    return container([heading(title, "h3", SERIF, 26, 400, "#FFFFFF", 1.2),
                      icon_list([(city, "fas fa-map-marker-alt", None)], "#E3B988", 14, "#FFFFFF", SANS, 15, 300)],
                     inner=True, gap=6, justify="flex-end", align="flex-start",
                     pad=R((24, 24, 24, 24), (24, 24, 24, 24), (24, 24, 24, 24)),
                     minh=R(240, 230, 220), bgimg=f"proj-{n:02d}.jpg",
                     overlay={"a": "#00000000", "b": "#000000BF", "angle": 180, "ap": 38, "bp": 100},
                     cls=f"cl-card cat-{cat}")


def proj_intro():
    left = container([heading("ELS NOSTRES", "p", SANS, 13, 400, C_TEXT, 1.2, 2.5),
                      heading("Projectes", "h1", SERIF, R(84, 64, 52), 400, "#111111", 1)],
                     gap=6, inner=True, pad=0, width=R(50, 100))
    right = container([heading("Descobreix una selecció dels nostres projectes de cuines, banys, interiorisme, "
                               "reformes i parquets a Figueres, Banyoles i altres localitats de l'Empordà i el "
                               "Pla de l'Estany.", "p", SANS, 17, 300, "#4A443F", 1.5)],
                      inner=True, pad=0, width=R(36, 100), align="flex-start")
    return container([left, right], dir=R("row", "column", "column"), justify="space-between",
                     align=R("flex-end", "flex-start", "flex-start"), gap=R(40, 24, 20), boxed=BOX,
                     pad=P("sec", bottom=(32, 32, 24)), bg=C_BG, cls="cl-pintro")


def proj_filters():
    labels = [("Tots", "tots"), ("Cuina", "cuina"), ("Banys", "banys"), ("Interiorisme", "interiorisme"),
              ("Reformes", "reformes"), ("Parquets", "parquets")]
    btns = []
    for lab, key in labels:
        btns.append(button(lab, f"#{key}", bg="#FFFFFF00", color="#1E1B19", size=17, weight=400,
                           pad=(15, 28, 15, 28), border="#CFC8BF", radius=1,
                           cls="cl-filter is-active" if key == "tots" else "cl-filter",
                           hover_bg="#FFFFFF00"))
    return container(btns, dir="row", justify="center", align="center", wrap=True, gap=16, boxed=BOX,
                     pad=P("sec", top=0, bottom=(40, 32, 24)), bg=C_BG, cls="cl-filters")


def proj_grid():
    cards = [proj_card(n + 1, t, c, k) for n, (t, c, k) in enumerate(PROJECTS)]
    grid = container(cards, grid=(R(3, 2, 1), 5), gap=R(24, 20, 18), inner=True, pad=0)
    return container([grid, html_widget(FILTER_JS)], boxed=BOX, bg=C_BG, gap=0,
                     pad=P("sec", top=0), cls="cl-pgrid")


# ---------------------------------------------------------------- Projectes amb pestanyes (widget Tabs niuat)
CATS = ["Cuina", "Banys", "Interiorisme", "Reformes", "Parquets"]


def load_projects():
    import csv
    out = []
    with open(f"{ROOT}/data/projectes.csv", encoding="utf-8-sig") as f:
        for r in csv.reader(f, delimiter=";"):
            if not r or r[0] == "id":
                continue
            cats = [c.strip() for c in r[3].replace("/", ",").split(",") if c.strip()]
            out.append({"id": r[0], "guia": r[1], "loc": r[2], "cats": cats, "nota": r[4] if len(r) > 4 else ""})
    return out


TABS_CSS = """<style>
.cl-tabs.elementor-widget .e-n-tabs-heading{display:flex;flex-wrap:wrap;justify-content:center;gap:16px;margin-bottom:40px}
.cl-tabs.elementor-widget .e-n-tab-title{background:transparent;border:1px solid #CFC8BF;border-radius:1px;color:#1E1B19;font:400 17px/1 'DM Sans',sans-serif;padding:16px 32px;cursor:pointer}
.cl-tabs.elementor-widget .e-n-tab-title[aria-selected="true"]{background:#141413!important;color:#fff!important;border-color:#141413!important}
.cl-tabs.elementor-widget .e-n-tab-title-text{color:inherit;font:inherit}
.cl-tabs.elementor-widget .e-n-tabs-content>.e-con:not(.e-active){display:none!important}
.cl-guia-nota{opacity:.7}
</style>"""


def tabs_widget(tabs, cls="cl-tabs"):
    """tabs: [(titol, Node-contenidor)]. Genera el widget 'nested-tabs' d'Elementor i el seu equivalent HTML."""
    i = nid()
    items, heads, body, rules = [], "", "", []
    for n, (titol, panel) in enumerate(tabs):
        items.append({"tab_title": titol, "_id": nid()})
        panel.el["settings"]["_title"] = titol
        heads += (f'<button class="e-n-tab-title" role="tab" aria-selected="{"true" if n == 0 else "false"}" '
                  f'data-tab="{n}"><span class="e-n-tab-title-text">{titol}</span></button>')
        body += panel.html.replace('<div class="', f'<div role="tabpanel" data-panel="{n}" class="{"e-active " if n == 0 else ""}', 1)
        rules += panel.rules
    s = {"tabs": items, "tabs_justify_horizontal": "center", "tabs_title_space_between": sz(16),
         "_css_classes": cls}
    el = {"id": i, "elType": "widget", "settings": s, "elements": [p.el for _, p in tabs],
          "widgetType": "nested-tabs"}
    html = (f'<div class="elementor-element e{i} elementor-widget elementor-widget-n-tabs {cls}">'
            f'<div class="elementor-widget-container"><div class="e-n-tabs"><div class="e-n-tabs-heading" role="tablist">'
            f'{heads}</div><div class="e-n-tabs-content">{body}</div></div></div></div>')
    return Node(el, html, rules, [p for _, p in tabs])


def guia_card(idx, p):
    """Targeta d'un projecte. El títol porta el nom de la carpeta com a guia (s'esborra en carregar el projecte)."""
    n = (idx % 15) + 1
    return proj_card(n, f"[{p['guia']}]", p["loc"] or "—", "x")


def proj_pestanyes():
    projs = load_projects()
    cards_all = [guia_card(i, p) for i, p in enumerate(projs)]

    def panel(cards, missatge):
        if not cards:
            return container([heading(missatge, "p", SANS, 17, 300, C_TEXT, 1.5, align="center", cls="cl-guia-nota")],
                             inner=True, pad=R((24, 0, 24, 0), (24, 0, 24, 0), (16, 0, 16, 0)))
        rows = -(-len(cards) // 3)
        return container(cards, grid=(R(3, 2, 1), rows), gap=R(24, 24, 16), inner=True, pad=0)

    tabs = [("Tots", panel(cards_all, ""))]
    for c in CATS:
        # cada targeta es crea de nou: els nodes no es poden reutilitzar entre pestanyes
        sel = [guia_card(i, p) for i, p in enumerate(projs) if c in p["cats"]]
        tabs.append((c, panel(sel, f"[GUIA] Encara no hi ha cap projecte assignat a «{c}». Copia i enganxa aquí les "
                                   "targetes de la pestanya «Tots» que corresponguin.")))
    pend = [guia_card(i, p) for i, p in enumerate(projs) if not p["cats"]]
    tabs.append(("Per classificar", panel(pend, "")))
    w = tabs_widget(tabs)
    return container([w, html_widget(TABS_CSS)], boxed=BOX, bg=C_BG, gap=0, pad=P("sec", top=0), cls="cl-ptabs")


# ================================================================ PÀGINES
def page_inici():
    return [hero("hero-inici.jpg", None, "Cuines, banys i interiorisme<br>per crear llars úniques",
                 "Veure projectes", "/projectes/", eyebrow="FIGUERES  |  BANYOLES"),
            categories(), props(), featured(), metode(), interiorisme(), equip(), insta_head(), insta_feed()]


def page_projectes():
    return [hero("hero-projectes.jpg", None, "Cuines, banys, interiorisme, reformes<br>i parquets per crear llars "
                 "úniques", "Contactar amb nosaltres", "/contacte/", minh=505, arrow=False),
            proj_intro(), proj_pestanyes(),
            interiorisme("Dissenyem espais<br>per a persones reals"), equip()]


def gmap(address, h=200):
    i = nid()
    s = {"address": address, "zoom": sz(15), "height": sz(h)}
    q = address.replace(" ", "+")
    rules = [("", f".e{i} iframe", f"width:100%;height:{h}px;border:0;display:block")]
    el = {"id": i, "elType": "widget", "settings": s, "elements": [], "widgetType": "google_maps"}
    html = (f'<div class="elementor-element e{i} elementor-widget elementor-widget-google_maps">'
            f'<div class="elementor-widget-container"><div class="elementor-custom-embed">'
            f'<iframe loading="lazy" src="https://maps.google.com/maps?q={q}&t=m&z=15&output=embed&iwloc=near" '
            f'title="{escape(address)}"></iframe></div></div></div>')
    return Node(el, html, rules)


# ---------------------------------------------------------------- formulari
def form(fields, button_text, email_to, name="Contacte Creem Llar"):
    """Widget Formulari d'Elementor Pro. fields: [(tipus, etiqueta, ample, requerit, opcions)]"""
    i = nid()
    s = {"form_name": name, "form_fields": [], "show_labels": "true", "button_text": button_text,
         "button_size": "md", "button_width": "100", "submit_actions": ["email"], "email_to": email_to,
         "email_subject": f"Nova consulta des de {name}", "email_content": "[all-fields]",
         "email_from_name": "Creem Llar", "success_message": "Gràcies! Hem rebut la teva consulta.",
         "column_gap": sz(16), "row_gap": sz(16),
         "field_text_color": C_DARK, "field_background_color": "#FFFFFF", "field_border_color": "#CFC8BF",
         "field_border_width": box(1), "field_border_radius": box(2), "label_color": "#4A443F",
         "button_text_color": "#FFFFFF", "button_background_color": C_DARK, "button_border_radius": box(1),
         "button_text_padding": box((18, 34, 18, 34)),
         "button_background_hover_color": "#2B2926", "button_hover_color": "#FFFFFF"}
    rules = []
    typo(s, rules, f".e{i} .elementor-field", "field_", SANS, 16, 300, 1.3)
    typo(s, rules, f".e{i} label", "label_", SANS, 14, 400, 1.3)
    typo(s, rules, f".e{i} .elementor-button", "button_", SANS, 16, 400, 1)
    rules += [("", f".e{i} .elementor-field", f"color:{C_DARK}"), ("", f".e{i} .elementor-field", "background:#fff"),
              ("", f".e{i} .elementor-field", "border:1px solid #CFC8BF;border-radius:2px;padding:14px 16px;width:100%"),
              ("", f".e{i} label", "color:#4A443F;display:block;margin-bottom:6px"),
              ("", f".e{i} .elementor-button", f"background:{C_DARK};color:#fff;padding:18px 34px;border-radius:1px;border:0;width:100%;cursor:pointer"),
              ("", f".e{i} .elementor-form-fields-wrapper", "display:flex;flex-wrap:wrap;gap:16px"),
              ("", f".e{i} .elementor-field-group", "flex:1 1 100%"),
              ("", f".e{i} .elementor-col-50", "flex:1 1 calc(50% - 8px)")]
    rules.append(("_mobile", f".e{i} .elementor-col-50", "flex:1 1 100%"))
    groups = ""
    for n, (typ, label, width, req, opts) in enumerate(fields):
        f = {"custom_id": f"field_{n}", "field_label": label, "placeholder": label if typ in ("text", "tel", "email", "textarea") else "",
             "_id": nid(), "width": str(width), "width_mobile": "100"}
        if typ != "text":
            f["field_type"] = typ
        if req:
            f["required"] = "true"
        if opts:
            f["field_options"] = "\n".join(opts)
        if typ == "acceptance":
            f["acceptance_text"] = label
        s["form_fields"].append(f)
        r = " required" if req else ""
        if typ == "select":
            ctl = '<select class="elementor-field"><option>' + label + "</option>" + "".join(f"<option>{o}</option>" for o in opts) + "</select>"
        elif typ == "textarea":
            ctl = f'<textarea class="elementor-field" rows="5" placeholder="{label}"{r}></textarea>'
        elif typ == "acceptance":
            ctl = f'<label style="display:flex;gap:10px;align-items:center"><input type="checkbox"{r}> {label}</label>'
        else:
            ctl = f'<input class="elementor-field" type="{typ}" placeholder="{label}"{r}>'
        lab = "" if typ == "acceptance" else f'<label>{label}</label>'
        col = " elementor-col-50" if width == 50 else ""
        groups += f'<div class="elementor-field-group{col}">{lab}{ctl}</div>'
    el = {"id": i, "elType": "widget", "settings": s, "elements": [], "widgetType": "form"}
    html = (f'<div class="elementor-element e{i} elementor-widget elementor-widget-form">'
            f'<div class="elementor-widget-container"><form class="elementor-form" onsubmit="return false">'
            f'<div class="elementor-form-fields-wrapper">{groups}'
            f'<div class="elementor-field-group"><button class="elementor-button" type="submit">{button_text}</button></div>'
            f'</div></form></div></div>')
    return Node(el, html, rules)


# ---------------------------------------------------------------- pàgines de servei (CONTINGUT PROVISIONAL)
INTRO_TXT = ("Creem cuines, banys i espais que combinen estètica, funcionalitat i benestar, sempre adaptats al "
             "teu estil de vida i a l'entorn on vius.")


def sec_intro(eyebrow, titol, text):
    left = container([heading(eyebrow, "p", SANS, 15, 400, C_TEXT, 1.2, 3.5),
                      heading(titol, "h2", SERIF, R(56, 46, 38), 400, "#111111", 1.1)],
                     gap=8, inner=True, pad=0, width=R(50, 100))
    right = container([heading(text, "p", SANS, 17, 400, "#4A443F", 1.6)], inner=True, pad=0,
                      width=R(36, 100), align="flex-start")
    return container([left, right], dir=R("row", "column", "column"), justify="space-between",
                     align=R("flex-end", "flex-start", "flex-start"), gap=R(40, 24, 20), boxed=BOX,
                     pad=P("sec", bottom=(48, 40, 32)), bg=C_BG, cls="cl-intro")


def cat_grid(cat):
    items = [(n + 1, t, c) for n, (t, c, k) in enumerate(PROJECTS) if k == cat]
    cards = [proj_card(n, t, c, cat) for n, t, c in items]
    rows = (len(cards) + 2) // 3
    grid = container(cards, grid=(R(3, 2, 1), rows), gap=R(24, 20, 18), inner=True, pad=0)
    return container([grid], boxed=BOX, bg=C_BG, gap=0,
                     pad=P("sec", top=0), cls="cl-pgrid")


SERVEIS = {
    "cuines": dict(
        titol="Cuines", cat="cuina", hero="hero-inici.jpg", split_img="cat-cuines.jpg",
        tagline="Dissenys funcionals i elegants<br>per al teu dia a dia.",
        eyebrow="CUINES A FIGUERES I BANYOLES", h2="El cor<br>de la llar",
        intro=("Dissenyem cuines a mida que s'adapten a com vius: una distribució pensada per al dia a dia, mobiliari "
               "amb bons acabats, materials de qualitat i una il·luminació que crea ambient. T'acompanyem des de la "
               "primera idea fins al muntatge final."),
        metode_h="La teva cuina,<br>pas a pas",
        passos=[("Escoltem", "Veiem com cuines, quant espai tens i què necessites en el teu dia a dia."),
                ("Dissenyem", "Plantegem la distribució, els materials i els electrodomèstics amb rigor i transparència."),
                ("Fem realitat", "Ens ocupem de tot el muntatge perquè només hagis de gaudir de la teva nova cuina.")],
        split_h="Cuines pensades<br>per viure-hi", split_eb="CUINES A FIGUERES | BANYOLES",
        split_p=("Una cuina ben pensada canvia el teu dia a dia. Explica'ns com la vols i et proposarem la solució que "
                 "millor encaixa amb el teu espai i el teu estil de vida."),
        split_b="Parlem de la teva cuina", cita="“ La teva cuina,<br>a la teva<br>mida ”"),
    "banys": dict(
        titol="Banys", cat="banys", hero="home-proj-2.jpg", split_img="cat-banys.jpg",
        tagline="Espais moderns, còmodes<br>i plens de benestar.",
        eyebrow="BANYS A BANYOLES I FIGUERES", h2="Espais de<br>benestar",
        intro=("Dissenyem banys moderns, còmodes i funcionals: una distribució ben aprofitada, revestiments duradors, "
               "il·luminació cuidada i detalls a mida. Ens encarreguem de tota la reforma perquè el teu bany et faci "
               "la vida més fàcil."),
        metode_h="El teu bany,<br>pas a pas",
        passos=[("Escoltem", "Valorem com utilitzes el bany i quines necessitats de confort i accessibilitat tens."),
                ("Dissenyem", "Proposem distribució, revestiments i sanitaris, cuidant l'aigua, la llum i l'espai."),
                ("Fem realitat", "Coordinem tota l'obra perquè el teu nou bany estigui a punt, amb garantia.")],
        split_h="Banys per gaudir<br>cada dia", split_eb="BANYS A BANYOLES | FIGUERES",
        split_p=("Reformem i creem banys moderns, còmodes i plens de benestar, amb materials resistents i un disseny "
                 "que t'acompanya durant anys."),
        split_b="Parlem del teu bany", cita="“ Benestar<br>en cada<br>detall ”"),
    "interiorisme": dict(
        titol="Interiorisme", cat="interiorisme", hero="hero-projectes.jpg", split_img="interiorisme.jpg",
        tagline="Solucions a mida<br>per a cada estil de vida.",
        eyebrow="INTERIORISME A BANYOLES I FIGUERES", h2="Espais<br>a la teva mida",
        intro=("Treballem l'interiorisme de manera global: mobiliari, colors, materials i il·luminació pensats junts "
               "perquè cada estança sigui bonica, funcional i coherent amb la teva manera de viure."),
        metode_h="El teu interior,<br>fins al darrer detall",
        passos=[("Escoltem", "Coneixem el teu estil de vida i com vols viure i sentir cada espai."),
                ("Dissenyem", "Definim ambients, mobiliari, colors i il·luminació amb coherència i criteri."),
                ("Fem realitat", "Executem el projecte fins a l'últim detall perquè el resultat sigui el que has imaginat.")],
        split_h="Dissenyem espais<br>per a persones reals", split_eb="INTERIORISME A FIGUERES | BANYOLES",
        split_p=("Creem espais que combinen estètica, funcionalitat i benestar, sempre adaptats al teu estil de vida "
                 "i a l'entorn on vius."),
        split_b="Parlem del teu projecte", cita="“ La teva llar,<br>el nostre<br>compromís ”"),
    "parquets": dict(
        titol="Parquets", cat="parquets", hero="proj-14.jpg", split_img="proj-14.jpg",
        tagline="Paviments càlids<br>pensats per a la teva llar.",
        eyebrow="PARQUETS A FIGUERES I BANYOLES", h2="Terres amb<br>caràcter",
        intro=("Assessorem i col·loquem parquets i paviments de fusta que aporten calidesa i durabilitat a qualsevol "
               "estança. Et ajudem a triar el to, l'acabat i el tipus més adequats per a cada espai."),
        metode_h="El teu parquet,<br>ben col·locat",
        passos=[("Escoltem", "Analitzem l'estança, l'ús que se'n farà i l'estil que busques."),
                ("Dissenyem", "Et proposem tipus de parquet, acabats i tons que combinin amb la resta de l'espai."),
                ("Fem realitat", "Col·loquem el parquet amb cura i t'ho deixem tot llest per estrenar.")],
        split_h="Terres càlids<br>per a cada estança", split_eb="PARQUETS A FIGUERES | BANYOLES",
        split_p=("Triem amb tu el parquet que millor s'adapta a l'estil i a l'ús de cada espai, i ens encarreguem de "
                 "col·locar-lo perquè duri."),
        split_b="Parlem del teu parquet", cita="“ Una llar càlida<br>comença<br>pel terra ”"),
}


def page_servei(k):
    c = SERVEIS[k]
    return [hero(c["hero"], None, c["tagline"], "Demana pressupost", "/contacte/", minh=505, arrow=False,
                 title=c["titol"], eyebrow="FIGUERES  |  BANYOLES"),
            sec_intro(c["eyebrow"], c["h2"], c["intro"]), cat_grid(c["cat"]), metode(c["metode_h"], c["passos"]),
            interiorisme(c["split_h"], c["split_eb"], c["split_p"], c["split_b"], c["cita"], c["split_img"])]


def page_cuines():
    return page_servei("cuines")


def page_banys():
    return page_servei("banys")


def page_interiorisme():
    return page_servei("interiorisme")


def page_parquets():
    return page_servei("parquets")


def page_nosaltres():
    text = ("Després d'una llarga trajectòria vinculada al món de la construcció, tres emprenedors de Figueres, "
            "Carlos, Xavi i Samuel, decideixen posar tot aquest bagatge al servei d'una idea: crear espais per "
            "viure, crear llar. Ens envoltem d'un gran equip d'interioristes, paletes, muntadors i lampistes que "
            "donen el millor de si mateixos perquè els nostres clients facin realitat els seus somnis.")
    return [hero("hero-nosaltres.jpg", None, "Dissenyem espais per viure.<br>Crear espais, crear llar.",
                 "Parlem del teu projecte", "/contacte/", minh=505, arrow=False, title="Nosaltres"),
            equip("L'equip de Creem Llar", text, enllac=False), props(), metode(), interiorisme()]


def office(titol, adreca, tel, mail, maps_q):
    return container([heading(titol, "h3", SERIF, 30, 400, "#111111", 1.2),
                      icon_list([(adreca, "fas fa-map-marker-alt", None), (tel, "fas fa-phone-alt", "tel:" + tel.replace(" ", "")),
                                 (mail, "far fa-envelope", "mailto:" + mail)], C_BROWN, 16, "#2E2A27", SANS, 17, 300),
                      gmap(maps_q, 220)], gap=14, inner=True, pad=0)


def page_contacte():
    fm = form([("text", "Nom", 100, True, None), ("email", "Correu electrònic", 100, True, None),
               ("text", "Assumpte", 100, True, None), ("textarea", "Missatge", 100, True, None),
               ("acceptance", "Accepto la política de privacitat", 100, True, None)],
              "Enviar", "info@creemllar.com")
    left = container([heading("ESCRIU-NOS", "p", SANS, 13, 400, C_TEXT, 1.2, 2.5),
                      heading("Parlem del<br>teu projecte", "h2", SERIF, R(48, 42, 36), 400, "#111111", 1.1),
                      container([fm], inner=True, bg="#FFFFFF", pad=R((40, 40, 40, 40), (32, 32, 32, 32), (24, 24, 24, 24)))],
                     gap=16, inner=True, pad=0, width=R(48, 100))
    right = container([heading("ON TROBAR-NOS", "p", SANS, 13, 400, C_TEXT, 1.2, 2.5),
                       office("Figueres", "C. Hortes, 34 – 17600 Figueres", "+34 972 684 896", "info@creemllar.com",
                              "C. Hortes, 34, 17600 Figueres"),
                       office("Banyoles", "C/ Pare Claret, 1 – 17820 Banyoles", "+34 972 519 324", "info@creemllar.com",
                              "C/ Pare Claret, 1, 17820 Banyoles")],
                      gap=26, inner=True, pad=0, width=R(52, 100))
    body = container([left, right], dir=R("row", "column", "column"), gap=R(60, 40, 36), align="flex-start",
                     boxed=BOX, bg=C_BG, pad=P("sec"),
                     cls="cl-contact")
    return [hero("hero-contacte.jpg", None, "Explica'ns la teva idea i t'assessorem<br>sense compromís.",
                 "Truca'ns", "tel:+34972684896", minh=505, arrow=False, title="Contacte"),
            body]


# ---------------------------------------------------------------- FITXA DE PROJECTE (plantilla estàtica + dinàmica)
import urllib.parse

GEN = False          # True => versió estàtica amb textos generals (plantilla per duplicar)
DYN = False          # True => la fitxa es construeix amb etiquetes dinàmiques d'Elementor Pro (plantilla "Entrada única")
TAXO, CPT = "categoria_projecte", "projecte"

# textos generals (valors de reserva quan un camp del projecte està buit)
FB = dict(
    excerpt="Un projecte dissenyat a mida per viure millor cada espai, amb funcionalitat, estètica i benestar.",
    repte=("Cada projecte parteix d'una necessitat concreta: aprofitar millor l'espai, guanyar comoditat i crear un "
           "ambient que reflecteixi la manera de viure de qui l'habita."),
    solucio=("Hem dissenyat una solució a mida, amb materials de qualitat i una distribució pensada per al confort "
             "diari, cuidant cada detall de principi a fi."),
    punts=["Disseny a mida", "Materials de qualitat", "Il·luminació cuidada", "Espais ben aprofitats",
           "Acabats i detalls a mida"],
    loc="—", sup="—")


def tag(_name, **settings):
    """Etiqueta dinàmica d'Elementor Pro: [elementor-tag id=".." name=".." settings=".."]"""
    sj = urllib.parse.quote(json.dumps(settings, ensure_ascii=False, separators=(",", ":")), safe="")
    return f'[elementor-tag id="{nid()}" name="{_name}" settings="{sj}"]'


def bind(node, _campo, _tag, **settings):
    """Enllaça un camp d'un element amb una etiqueta dinàmica (només en mode DYN)."""
    if DYN:
        node.el["settings"].setdefault("__dynamic__", {})[_campo] = tag(_tag, **settings)
    return node


def bind_item(node, n, _campo, _tag, **settings):
    """Igual que bind() però per a un element d'una llista (Llista d'icones)."""
    if DYN:
        node.el["settings"]["icon_list"][n].setdefault("__dynamic__", {})[_campo] = tag(_tag, **settings)
    return node


def cf(key, fallback):
    return dict(key="", custom_key=key, fallback=fallback)       # etiqueta "Camp personalitzat" (meta del projecte)


def acf_img(slug):
    return dict(key=f"field_cl_{slug}:{slug}")                   # etiqueta "ACF Imatge"


def pj_spec(ic, etiqueta, valor, last=False, dyn=None):
    v = heading(valor, "p", SANS, 14, 400, C_TEXT, 1.2)
    if dyn:
        bind(v, "title", dyn[0], **dyn[1])
    return container([icon(ic, 28, "#2B2B2B"), heading(etiqueta, "p", SANS, 15, 500, "#141413", 1.2), v],
                     gap=8, inner=True, align="flex-start", pad=R((0, 24, 0, 24), (0, 16, 0, 16), (0, 16, 0, 16)),
                     border=C_LINE, bw=R((0, 0 if last else 1, 0, 0), (0, 0 if last else 1, 0, 0), (0, 0, 0, 0)))


def T(c, key, sample, generic):
    """Text d'una secció: el del servei (c) si n'hi ha; si no, mostra (estàtica) o general (GEN/DYN)."""
    if c:
        return c[key]
    return sample if not (DYN or GEN) else generic


def pj_hero(c=None):
    back = heading("← Tots els projectes", "p", SANS, 15, 400, "#FFFFFFD9", 1.2, href="/projectes/")
    eyebrow = heading(T(c, "eyebrow", "PROJECTE · CUINA", "PROJECTE D'INTERIORISME"), "p", SANS, 15, 400, "#FFFFFFCC",
                      1.2, 3.5, tf="uppercase")
    bind(eyebrow, "title", "post-terms", taxonomy=TAXO, separator=", ", link="", before="Projecte · ")
    titol = heading(T(c, "h1", "Cuina contemporània<br>a Figueres", "Títol del<br>projecte"), "h1", SERIF,
                    R(64, 52, 40), 400, "#FFFFFF", 1.1)
    bind(titol, "title", "post-title")
    ex = heading(T(c, "excerpt", "Una cuina moderna i funcional, dissenyada per gaudir del dia a dia amb elegància, llum "
                   "i espais oberts.", FB["excerpt"]), "p", SANS, 19, 400, "#FFFFFFF2", 1.5)
    bind(ex, "title", "post-excerpt", fallback=FB["excerpt"])
    btn = button("Demana un pressupost similar", "/contacte/", bg=None, color="#FFFFFF", size=16, weight=400,
                 pad=(16, 32, 16, 32), border="#FFFFFFB3", radius=1, icon="fas fa-long-arrow-alt-right")
    text = container([back, eyebrow, titol, ex, btn], gap=24, inner=True, pad=0, align="flex-start", width=R(50, 100))
    hero_c = container([text], justify="center", align="flex-start", boxed=BOX,
                       pad=R((112, GUT[0], 64, GUT[0]), (112, GUT[1], 48, GUT[1]), (112, GUT[2], 48, GUT[2])),
                       minh=R(640, 560, 560), bgimg=(c or {}).get("img_hero", "hero-inici.jpg"), bgpos="center center",
                       cls="cl-hero cl-pj-hero",
                       overlay={"a": "#120C08D9", "b": "#120C0826", "angle": 90, "ap": 0, "bp": 70})
    return bind(hero_c, "background_image", "post-featured-image")


def pj_repte(c=None):
    p = heading(T(c, "repte_p", "L'objectiu d'aquest projecte era crear una cuina integrada a l'espai de dia, amb una "
                  "estètica contemporània i una gran funcionalitat, aprofitant al màxim la llum natural i la connexió "
                  "amb el menjador i el jardí.", FB["repte"]), "p", SANS, 17, 400, "#2E2A27", 1.6)
    bind(p, "title", "post-custom-field", **cf("repte_text", FB["repte"]))
    h2 = heading(T(c, "repte_h", "Una cuina oberta,<br>pràctica i amb caràcter", "Un projecte pensat<br>a la teva mida"),
                 "h2", SERIF, R(40, 36, 32), 400, "#111111", 1.2)
    if c:   # plantilla per servei: Ubicació (s'escriu) + Tipus (fix) + «Inclou» (general, sense dades a omplir)
        tercer = pj_spec("fas fa-pencil-ruler", "Inclou", c["inclou"], last=True)
        tipus = pj_spec("fas fa-home", "Tipus de projecte", c["tipus"])
    else:
        tercer = pj_spec("fas fa-ruler-combined", "Superfície", "28 m²" if not GEN else "— m²", last=True,
                         dyn=("post-custom-field", cf("superficie", FB["sup"])))
        tipus = pj_spec("fas fa-home", "Tipus de projecte", "Cuina" if not GEN else "Cuina / Banys / Reforma",
                        dyn=("post-terms", dict(taxonomy=TAXO, separator=", ", link="")))
    specs = container([
        pj_spec("fas fa-map-marker-alt", "Ubicació", "Figueres" if not (GEN or c) else "Localitat",
                dyn=("post-custom-field", cf("localitat", FB["loc"]))), tipus, tercer],
        grid=(3, 1), gap=0, inner=True, pad=R((16, 0, 0, 0), (16, 0, 0, 0), (16, 0, 0, 0)))
    txt = container([heading("EL REPTE", "p", SANS, 15, 400, C_TEXT, 1.2, 3.5), h2, p, specs],
                    gap=24, inner=True, pad=0, width=R(50, 100), justify="center")
    im = image((c or {}).get("img_repte", "home-proj-1.jpg"), h=R(448, 360, 280), alt="El repte del projecte", lightbox=True)
    bind(im, "image", "acf-image", **acf_img("imatge_repte"))
    img = container([im], inner=True, pad=0, width=R(50, 100))
    return container([txt, img], dir=R("row", "column", "column"), align="center", gap=R(64, 40, 32), boxed=BOX,
                     bg="#FFFFFF", pad=P("sec"), cls="cl-pj-repte")


def pj_solucio(c=None):
    img_sol = (c or {}).get("img_sol", "interiorisme.jpg")
    if GEN or c:
        foto = container([image(img_sol, h=R(560, 360, 280), alt="La solució")], inner=True, width=R(50, 100), pad=0)
    else:
        foto = container([], inner=True, width=R(50, 100), bgimg=img_sol, minh=R(560, 360, 280), pad=0)
        bind(foto, "background_image", "acf-image", **acf_img("imatge_solucio"))
    punts = (c["punts"] if c else (["Mobiliari a mida", "Materials d'alta qualitat", "Il·luminació integrada",
                                    "Gran capacitat d'emmagatzematge", "Connexió amb l'exterior"]
                                   if not (DYN or GEN) else FB["punts"]))
    checks = icon_list([(t, "far fa-check-circle", None) for t in punts],
                       C_BROWN, 18, "#2E2A27", SANS, 16, 400, indent=12, space=16)
    for n in range(5):
        bind_item(checks, n, "text", "post-custom-field", **cf(f"punt_{n + 1}", FB["punts"][n]))
    p = heading(T(c, "sol_p", "Hem dissenyat una cuina amb línies netes, materials naturals i una distribució pensada "
                  "per al confort diari. L'illa central esdevé el punt de trobada, combinant zona de cuina, "
                  "preparació i espai social.", FB["solucio"]), "p", SANS, 17, 400, "#2E2A27", 1.6)
    bind(p, "title", "post-custom-field", **cf("solucio_text", FB["solucio"]))
    panel = container([heading("LA SOLUCIÓ", "p", SANS, 15, 400, "#4A443F", 1.2, 3.5),
                       heading(T(c, "sol_h", "Disseny i funcionalitat<br>en perfecta harmonia",
                                 "Disseny i funcionalitat<br>en perfecta harmonia"), "h2", SERIF, R(40, 36, 32), 400,
                               "#141413", 1.2), p, checks],
                      inner=True, width=R(50, 100), bg=C_BEIGE, justify="center", align="flex-start", gap=24,
                      pad=R((64, 72, 64, 72), (48, 40, 48, 40), (40, 24, 40, 24)))
    return container([foto, panel], dir=R("row", "column", "column"), gap=0, align="stretch", pad=0,
                     cls="cl-split cl-pj-solucio")


def pj_galeria(c=None):
    cap = container([heading("GALERIA D'IMATGES", "p", SANS, 15, 400, C_TEXT, 1.2, 3.5),
                     heading("Detalls que fan la diferència", "h2", SERIF, R(40, 36, 32), 400, "#111111", 1.2)],
                    gap=8, inner=True, pad=0)
    keys = (c or {}).get("gal", ["home-proj-3.jpg", "home-proj-2.jpg", "proj-01.jpg", "proj-04.jpg", "proj-10.jpg"])
    ims = []
    for n, k in enumerate(keys, 1):
        im = image(k, h=R(480, 360, 280) if n == 1 else R(232, 176, 140), alt=f"Galeria {n}", lightbox=True)
        bind(im, "image", "acf-image", **acf_img(f"galeria_{n}"))
        ims.append(im)
    gran = container([ims[0]], inner=True, pad=0, width=R(50, 100))
    petites = container(ims[1:], grid=(2, 2), gap=16, inner=True, pad=0, width=R(50, 100))
    mosaic = container([gran, petites], dir=R("row", "column", "column"), gap=16, inner=True, pad=0)
    return container([cap, mosaic], gap=32, boxed=BOX, bg="#FFFFFF", pad=P("sec"), cls="cl-pj-galeria")


def pj_cta(c=None):
    txt = container([heading(T(c, "cta_eb", "TENS UN PROJECTE SIMILAR?", "TENS UN PROJECTE SIMILAR?"), "p", SANS, 15,
                             400, C_TEXT, 1.2, 3.5),
                     heading(T(c, "cta_h", "Fem realitat la cuina dels teus somnis", "Fem realitat el teu projecte"),
                             "h2", SERIF, R(40, 36, 32), 400, "#111111", 1.2),
                     heading(T(c, "cta_p", "T'assessorem en tot el procés, des de la idea inicial fins a l'últim detall. "
                               "Demana un pressupost sense compromís.", "T'assessorem en tot el procés, des de la idea "
                               "inicial fins a l'últim detall. Demana un pressupost sense compromís."),
                             "p", SANS, 17, 400, "#2E2A27", 1.6),
                     button(T(c, "cta_b", "Demana pressupost", "Demana pressupost"), "/contacte/", bg=C_DARK,
                            color="#fff", size=16, weight=400, pad=(16, 32, 16, 32), radius=1,
                            icon="fas fa-long-arrow-alt-right")],
                    gap=24, inner=True, pad=0, width=R(64, 100), align="flex-start")
    q = quote(T(c, "cita", "“ Espais que<br>s'adapten a tu ”", "“ Espais que<br>s'adapten a tu ”"), 42)
    return container([txt, q], dir=R("row", "column", "column"), justify="space-between",
                     align=R("center", "flex-start", "flex-start"), gap=R(48, 32, 24), boxed=BOX, bg=C_BG2,
                     pad=P("sec"), cls="cl-pj-cta")


def page_projecte():
    return [pj_hero(), pj_repte(), pj_solucio(), pj_galeria(), pj_cta()]


PJ_SERVEIS = {
    "cuina": dict(
        eyebrow="PROJECTE DE CUINA", h1="Cuina a<br>Localitat", tipus="Cuina", inclou="Disseny i muntatge",
        excerpt="Una cuina a mida, funcional i pensada per al dia a dia, amb materials de qualitat i molta llum.",
        repte_h="Una cuina pensada<br>per a viure-hi",
        repte_p=("Cada cuina parteix d'una necessitat: aprofitar l'espai, guanyar comoditat i crear un lloc agradable on "
                 "cuinar, menjar i compartir. Partim de com viu cada família per dissenyar una cuina a la seva mida."),
        sol_h="Disseny i funcionalitat<br>en perfecta harmonia",
        sol_p=("Hem dissenyat una cuina amb línies netes, bons materials i una distribució pensada per al dia a dia: "
               "zona de treball còmoda, bon emmagatzematge i una il·luminació que crea ambient."),
        punts=["Mobiliari a mida", "Materials d'alta qualitat", "Il·luminació integrada",
               "Gran capacitat d'emmagatzematge", "Zona de treball còmoda"],
        cta_eb="T'INTERESSA UNA CUINA COM AQUESTA?", cta_h="Fem realitat la teva cuina",
        cta_p="Explica'ns com la imagines i t'assessorem sense compromís, des de la primera idea fins al muntatge final.",
        cta_b="Demana pressupost de cuina", cita="“ La teva cuina,<br>a la teva<br>mida ”",
        img_hero="hero-inici.jpg", img_repte="home-proj-1.jpg", img_sol="cat-cuines.jpg",
        gal=["home-proj-1.jpg", "proj-01.jpg", "proj-02.jpg", "proj-04.jpg", "proj-05.jpg"]),
    "banys": dict(
        eyebrow="PROJECTE DE BANY", h1="Bany a<br>Localitat", tipus="Banys", inclou="Disseny i reforma",
        excerpt="Un bany modern i còmode, pensat per al benestar de cada dia, amb materials resistents i un disseny cuidat.",
        repte_h="Un bany pensat<br>per al benestar",
        repte_p=("Cada bany parteix d'una necessitat: guanyar espai, comoditat i funcionalitat sense renunciar a un "
                 "ambient agradable i fàcil de mantenir."),
        sol_h="Confort i disseny<br>en cada detall",
        sol_p=("Hem dissenyat un bany amb una distribució ben aprofitada, revestiments duradors i una il·luminació "
               "cuidada, perquè el dia a dia sigui més còmode."),
        punts=["Distribució ben aprofitada", "Revestiments de qualitat", "Il·luminació cuidada",
               "Mobiliari i accessoris a mida", "Fàcil de mantenir"],
        cta_eb="T'INTERESSA UN BANY COM AQUEST?", cta_h="Fem realitat el teu bany",
        cta_p="Explica'ns què necessites i et proposem la reforma que millor s'adapta al teu espai.",
        cta_b="Demana pressupost de bany", cita="“ Benestar<br>en cada<br>detall ”",
        img_hero="home-proj-2.jpg", img_repte="cat-banys.jpg", img_sol="proj-07.jpg",
        gal=["home-proj-2.jpg", "proj-07.jpg", "proj-08.jpg", "proj-09.jpg", "cat-banys.jpg"]),
    "interiorisme": dict(
        eyebrow="PROJECTE D'INTERIORISME", h1="Interiorisme a<br>Localitat", tipus="Interiorisme",
        inclou="Disseny i execució",
        excerpt="Un espai pensat de dalt a baix: mobiliari, colors, materials i il·luminació al servei de la teva manera de viure.",
        repte_h="Un espai pensat<br>a la teva mida",
        repte_p=("Cada projecte d'interiorisme parteix de la manera de viure de qui l'habita: com es fa servir l'espai, "
                 "quin ambient es vol i quins detalls el fan especial."),
        sol_h="Ambients amb criteri<br>i coherència",
        sol_p=("Hem treballat mobiliari, colors, materials i il·luminació de manera conjunta perquè cada estança sigui "
               "bonica, funcional i coherent amb la resta de la llar."),
        punts=["Mobiliari a mida", "Paleta de colors i materials", "Il·luminació d'ambient",
               "Distribució de l'espai", "Acabats cuidats"],
        cta_eb="T'INTERESSA UN PROJECTE COM AQUEST?", cta_h="Fem realitat el teu interior",
        cta_p="Explica'ns com vols viure el teu espai i el dissenyem plegats.",
        cta_b="Demana pressupost", cita="“ La teva llar,<br>el nostre<br>compromís ”",
        img_hero="hero-projectes.jpg", img_repte="cat-interiorisme.jpg", img_sol="interiorisme.jpg",
        gal=["home-proj-3.jpg", "proj-10.jpg", "proj-11.jpg", "proj-12.jpg", "cat-interiorisme.jpg"]),
    "reformes": dict(
        eyebrow="PROJECTE DE REFORMA", h1="Reforma a<br>Localitat", tipus="Reformes", inclou="Gestió i execució",
        excerpt="Una reforma gestionada de principi a fi, per transformar l'espai amb garantia i sense preocupacions.",
        repte_h="Una reforma pensada<br>de principi a fi",
        repte_p=("Cada reforma parteix d'un espai que cal renovar: guanyar comoditat, aprofitar millor els metres i "
                 "donar-li una imatge nova, coordinant tot el procés."),
        sol_h="Transformació amb garantia<br>i bons acabats",
        sol_p=("Hem coordinat tot el procés d'obra, des del disseny fins a l'acabat final, per transformar l'espai amb "
               "ordre, calidesa i atenció al detall."),
        punts=["Gestió integral de l'obra", "Materials de qualitat", "Acabats cuidats", "Seguiment constant",
               "Garantia i experiència"],
        cta_eb="T'INTERESSA UNA REFORMA COM AQUESTA?", cta_h="Fem realitat la teva reforma",
        cta_p="Explica'ns què vols canviar i t'assessorem sense compromís, amb tot el procés coordinat.",
        cta_b="Demana pressupost de reforma", cita="“ Transformem<br>els teus<br>espais ”",
        img_hero="proj-13.jpg", img_repte="cat-reformes.jpg", img_sol="proj-15.jpg",
        gal=["proj-13.jpg", "proj-15.jpg", "cat-reformes.jpg", "proj-12.jpg", "proj-14.jpg"]),
    "parquets": dict(
        eyebrow="PROJECTE DE PARQUET", h1="Parquet a<br>Localitat", tipus="Parquets",
        inclou="Assessorament i col·locació",
        excerpt="Un terra de fusta càlid i resistent, triat per donar caràcter i confort a cada estança.",
        repte_h="Un terra pensat<br>per a cada estança",
        repte_p=("Cada projecte de parquet parteix de l'espai i de l'ús que se'n farà: triar el to, l'acabat i la "
                 "col·locació adequats perquè el terra duri i s'integri amb la resta."),
        sol_h="Calidesa i durabilitat<br>sota els teus peus",
        sol_p=("Hem seleccionat un parquet que combina amb l'estil de l'espai i l'hem col·locat amb cura perquè el "
               "resultat sigui uniforme, càlid i fàcil de mantenir."),
        punts=["Fusta càlida i resistent", "To i acabat a mida", "Col·locació acurada", "Fàcil de mantenir",
               "Combina amb tot l'espai"],
        cta_eb="T'INTERESSA UN PARQUET COM AQUEST?", cta_h="Fem realitat el teu terra",
        cta_p="Explica'ns com és l'espai i t'ajudem a triar el parquet que millor encaixa.",
        cta_b="Demana pressupost de parquet", cita="“ Una llar càlida<br>comença<br>pel terra ”",
        img_hero="proj-14.jpg", img_repte="proj-14.jpg", img_sol="proj-14.jpg",
        gal=["proj-14.jpg", "proj-13.jpg", "proj-15.jpg", "proj-12.jpg", "proj-11.jpg"]),
}


def page_projecte_servei(k):
    c = PJ_SERVEIS[k]
    return [pj_hero(c), pj_repte(c), pj_solucio(c), pj_galeria(c), pj_cta(c)]


def page_projecte_general():
    global GEN
    GEN = True
    try:
        return page_projecte()
    finally:
        GEN = False


def page_projecte_dinamic():
    global DYN
    DYN = True
    try:
        return page_projecte()
    finally:
        DYN = False


# ---- targeta per al Loop Grid (plantilla "Loop Item"): cada projecte del llistat
def loop_card():
    titol = heading("Títol del projecte", "h3", SERIF, 26, 400, "#FFFFFF", 1.2, href="/projecte/")
    loc = icon_list([("Localitat", "fas fa-map-marker-alt", None)], "#E3B988", 14, "#FFFFFF", SANS, 15, 400)
    global DYN
    DYN = True
    try:
        bind(titol, "title", "post-title")
        bind(titol, "link", "post-url")
        bind_item(loc, 0, "text", "post-custom-field", **cf("localitat", ""))
        card = container([titol, loc], inner=False, gap=6, justify="flex-end", align="flex-start",
                         pad=R((24, 24, 24, 24), (24, 24, 24, 24), (24, 24, 24, 24)),
                         minh=R(240, 230, 220), bgimg="proj-01.jpg",
                         overlay={"a": "#00000000", "b": "#000000BF", "angle": 180, "ap": 38, "bp": 100},
                         cls="cl-card")
        bind(card, "background_image", "post-featured-image")
        bind(card, "link", "post-url")
    finally:
        DYN = False
    return card


def page_loop_item():
    return [loop_card()]


def loop_widgets():
    """Llistat dinàmic de projectes: filtre per categoria + Loop Grid (cal triar la plantilla de targeta)."""
    i, j = nid(), nid()
    filt = {"id": i, "elType": "widget", "widgetType": "taxonomy-filter", "elements": [],
            "settings": {"taxonomy": TAXO, "selected_element": "cl-projectes-grid", "show_all_option": "yes",
                         "all_label": "Tots"}}
    grid = {"id": j, "elType": "widget", "widgetType": "loop-grid", "elements": [],
            "settings": {"_element_id": "cl-projectes-grid", "template_id": "", "columns": "3", "columns_tablet": "2",
                         "columns_mobile": "1", "posts_per_page": 12, "post_query_post_type": CPT,
                         "pagination_type": "numbers", "row_gap": sz(24), "column_gap": sz(24)}}
    return Node(filt, "", []), Node(grid, "", [])


def page_projectes_dinamic():
    base = page_projectes()                       # capçalera, intro i franges finals de la pàgina actual
    filt, grid = loop_widgets()
    llistat = container([filt, grid], boxed=BOX, bg=C_BG, gap=32, pad=P("sec", top=0), cls="cl-ptabs")
    out = []
    for n in base:
        if "cl-ptabs" in n.html:                  # substitueix les pestanyes estàtiques pel llistat dinàmic
            out.append(llistat)
        else:
            out.append(n)
    return out


# ================================================================ SORTIDA
BASE_CSS = """
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:#F8F5F0;font-family:'DM Sans',sans-serif;-webkit-font-smoothing:antialiased;position:relative;overflow-x:hidden}
img{max-width:100%;height:auto;vertical-align:middle;display:inline-block;border:0}
a{text-decoration:none;color:inherit}
.e-con{display:flex;flex-direction:column;position:relative;width:100%;min-width:0;--w:100%}
.e-con>.e-con-inner{display:flex;flex-direction:column;width:100%;margin:0 auto;min-width:0;flex-grow:1}
.e-con.e-child{width:var(--w);flex:0 1 auto;max-width:100%}
.e-con.e-parent{width:100%}
.e-con::before{content:'';position:absolute;inset:0;pointer-events:none}
.e-con:not(.has-ov)::before{display:none}
.has-ov>*,.has-ov>.e-con-inner{position:relative;z-index:1}
.elementor-widget{min-width:0;position:relative}
.elementor-heading-title{margin:0;padding:0}
.elementor-button{display:inline-block;text-align:center;fill:#fff;transition:all .3s}
.elementor-button-content-wrapper{display:flex;justify-content:center;align-items:center}
.elementor-button-icon{margin-left:10px;display:inline-flex;font-size:1em}
.elementor-icon-wrapper{display:block}
.elementor-icon{display:inline-block;line-height:1;text-align:center}
.elementor-icon-list-items{list-style:none;margin:0;padding:0}
.elementor-icon-list-item{display:flex;align-items:center}
.elementor-icon-list-icon{display:inline-flex}
.elementor-nav-menu{list-style:none;margin:0;padding:0;display:flex;align-items:center}
.elementor-nav-menu a{display:block;border:1px solid transparent;white-space:nowrap}
.elementor-nav-menu .active a,.elementor-nav-menu a:hover{border-color:#fff}
.elementor-menu-toggle{display:none;background:none;border:0;color:#fff;font-size:24px;cursor:pointer;min-width:44px;min-height:44px}
.elementor-divider{display:block}
.elementor-divider-separator{display:flex;margin:0}
.cl-header .elementor-widget-nav-menu{flex:0 0 auto}
@media (max-width:1024px){
  .elementor-nav-menu--main{display:none}
  .elementor-menu-toggle{display:block}
  .elementor-widget-nav-menu.open .elementor-nav-menu--main{display:block;position:absolute;top:100%;right:0;background:#2A221C;padding:12px;z-index:50}
  .elementor-widget-nav-menu.open .elementor-nav-menu{flex-direction:column;align-items:stretch;gap:4px!important}
}
"""


def collect_css(rules):
    base, tab, mob = [], [], []
    for d, sel, decl in rules:
        if d == "":
            base.append(f"{sel}{{{decl}}}")
        elif d == "_tablet":
            tab.append(f"{sel}{{{decl}}}")
        elif d == "_mobile" or d == "_mobile_only":
            mob.append(f"{sel}{{{decl}}}")
    css = "\n".join(base)
    css += "\n@media (max-width:1024px){\n" + "\n".join(tab) + "\n}"
    css += "\n@media (max-width:767px){\n" + "\n".join(mob) + "\n}"
    return css


GFONTS = ("https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&"
          "family=Playfair+Display:ital,wght@0,400;0,500;1,400&family=Josefin+Sans:wght@400&family=Mrs+Saint+Delafield&family=Grand+Hotel&display=swap")


def write_html(name, title, parts):
    rules = []
    for p in parts:
        rules += p.rules
    body = "".join(p.html for p in parts)
    page = f"""<!doctype html>
<html lang="ca"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · previsualització Elementor</title>
<link href="{GFONTS}" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
<style>{BASE_CSS}
{collect_css(rules)}</style></head><body>
{body}
<script>document.addEventListener('click',function(e){{var b=e.target.closest('.e-n-tab-title');if(!b)return;var w=b.closest('.e-n-tabs');
w.querySelectorAll('.e-n-tab-title').forEach(function(x){{x.setAttribute('aria-selected',x===b?'true':'false');}});
w.querySelectorAll(':scope>.e-n-tabs-content>.e-con').forEach(function(p){{p.classList.toggle('e-active',p.dataset.panel===b.dataset.tab);}});}});</script>
</body></html>"""
    os.makedirs(f"{OUT}/html", exist_ok=True)
    with open(f"{OUT}/html/{name}.html", "w", encoding="utf-8") as f:
        f.write(page)


def write_json(name, title, ttype, nodes, page_settings=None):
    data = {"version": "0.4", "title": title, "type": ttype, "content": [n.el for n in nodes],
            "page_settings": page_settings or [], "metadata": []}
    os.makedirs(f"{OUT}/json", exist_ok=True)
    with open(f"{OUT}/json/{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_acf():
    """Grup de camps d'ACF (gratuït) per als projectes. Importació: ACF → Eines → Importar."""
    def w(width=""): return {"width": width, "class": "", "id": ""}
    def base(key, label, name, typ, instr="", req=0):
        return {"key": f"field_cl_{key}", "label": label, "name": name, "aria-label": "", "type": typ,
                "instructions": instr, "required": req, "conditional_logic": 0, "wrapper": w()}
    def text(key, label, instr="", req=0, ph=""):
        f = base(key, label, key, "text", instr, req)
        f.update({"default_value": "", "maxlength": "", "placeholder": ph, "prepend": "", "append": ""})
        return f
    def area(key, label, instr=""):
        f = base(key, label, key, "textarea", instr)
        f.update({"default_value": "", "maxlength": "", "rows": 4, "placeholder": "", "new_lines": ""})
        return f
    def img(key, label, instr=""):
        f = base(key, label, key, "image", instr)
        f.update({"return_format": "array", "library": "all", "min_width": "", "min_height": "", "min_size": "",
                  "max_width": "", "max_height": "", "max_size": "", "mime_types": "", "preview_size": "medium"})
        return f
    def tab(key, label):
        f = base("tab_" + key, label, "", "tab")
        f.update({"placement": "top", "endpoint": 0})
        return f
    fields = [tab("dades", "Dades bàsiques"),
              text("localitat", "Localitat", "Ej.: Figueres. Se muestra en la ficha y en la tarjeta del listado.", 1, "Figueres"),
              text("superficie", "Superfície", "Opcional. Ej.: 28 m². Si lo dejas vacío se muestra «—».", 0, "28 m²"),
              tab("textos", "Textos (opcionales)"),
              area("repte_text", "El repte", "2-3 líneas. Si lo dejas vacío se muestra un texto general."),
              area("solucio_text", "La solució", "2-3 líneas. Si lo dejas vacío se muestra un texto general."),
              ] + [text(f"punt_{n}", f"Punt de la solució {n}", "Opcional. Si lo dejas vacío se muestra un texto general.")
                   for n in range(1, 6)] + [
              tab("imatges", "Imatges (opcionals)"),
              img("imatge_repte", "Imatge del repte", "Imagen junto a «El repte»."),
              img("imatge_solucio", "Imatge de la solució", "Imagen grande de «La solució»."),
              ] + [img(f"galeria_{n}", f"Galeria {n}" + (" (la gran)" if n == 1 else ""),
                       "Se abre ampliada al hacer clic.") for n in range(1, 6)]
    group = [{"key": "group_cl_projecte", "title": "Dades del projecte", "fields": fields,
              "location": [[{"param": "post_type", "operator": "==", "value": CPT}]],
              "menu_order": 0, "position": "normal", "style": "default", "label_placement": "top",
              "instruction_placement": "label", "hide_on_screen": "", "active": True, "description": "",
              "show_in_rest": 0}]
    os.makedirs(f"{OUT}/acf", exist_ok=True)
    with open(f"{OUT}/acf/camps-projecte.json", "w", encoding="utf-8") as f:
        json.dump(group, f, ensure_ascii=False, indent=2)


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(f"{OUT}/html", exist_ok=True)
    # el HTML viu a output/html/, les imatges a ../../assets
    ps = {"template": "elementor_header_footer", "hide_title": "yes"}

    # --- plantilles globals (els mateixos nodes serveixen per al JSON i per a l'HTML)
    footer = ftr_wrap()
    write_json("footer", "Creem Llar - Footer", "footer", [footer])
    write_json("header", "Creem Llar - Header", "header", [hdr("Inici")])

    # --- pàgines (JSON) + previsualització (HTML = header + pàgina + footer)
    pages = [("inici", "Inici", "Inici", page_inici), ("projectes", "Projectes", "Projectes", page_projectes),
             ("cuines", "Cuines", "Cuines", page_cuines), ("banys", "Banys", "Banys", page_banys),
             ("interiorisme", "Interiorisme", "Interiorisme", page_interiorisme),
             ("parquets", "Parquets", "Parquets", page_parquets), ("nosaltres", "Nosaltres", "Nosaltres", page_nosaltres),
             ("contacte", "Contacte", "Contacte", page_contacte),
             ("projecte", "Projecte (plantilla)", "Projectes", page_projecte)] + [
        (f"projecte-{k}", f"Projecte ({k})", "Projectes", (lambda k=k: page_projecte_servei(k))) for k in PJ_SERVEIS]
    for slug, title, active, fn in pages:
        nodes = fn()
        write_json(slug, f"Creem Llar - {title}", "page", nodes, ps)
        write_html(slug, title, [hdr(active)] + nodes + [footer])

    write_json("projecte-general", "Creem Llar - Projecte (general)", "page", page_projecte_general(), ps)
    write_acf()
    # --- plantilles dinàmiques (només JSON; no tenen previsualització estàtica)
    write_json("projecte-dinamic", "Creem Llar - Projecte (plantilla dinàmica)", "single-post", page_projecte_dinamic())
    write_json("projecte-targeta-loop", "Creem Llar - Targeta de projecte (Loop Item)", "loop-item", page_loop_item())
    write_json("projectes-dinamic", "Creem Llar - Projectes (llistat dinàmic)", "page", page_projectes_dinamic(), ps)

    with open(f"{OUT}/html/index.html", "w", encoding="utf-8") as f:
        f.write("<!doctype html><meta charset=utf-8><title>Creem Llar</title>"
                "<body style='font-family:sans-serif;padding:40px'><h1>Previsualitzacions</h1><ul>"
                + "".join(f"<li><a href='{s}.html'>{t}</a></li>" for s, t, _, _ in pages) + "</ul>")
    standalone([p[0] for p in pages])
    write_docs([p[0] for p in pages])
    print("OK ->", OUT)


def standalone(slugs):
    """HTML autocontingut (imatges en base64) per descarregar i obrir directament."""
    import base64, re
    os.makedirs(f"{OUT}/descarregar", exist_ok=True)
    for slug in slugs:
        h = open(f"{OUT}/html/{slug}.html", encoding="utf-8").read()

        def rep(m):
            fn = m.group(1)
            b = base64.b64encode(open(f"{ROOT}/assets/{fn}", "rb").read()).decode()
            return f"data:image/jpeg;base64,{b}"
        h = re.sub(r"\.\./\.\./assets/([\w\-\.]+\.jpg)", rep, h)
        open(f"{OUT}/descarregar/{slug}.html", "w", encoding="utf-8").write(h)


def write_docs(slugs):
    """Web navegable per a GitHub Pages: /docs (index = Inici, el menú enllaça les pàgines entre elles)."""
    import re
    docs = os.path.join(os.path.dirname(ROOT), "docs")
    shutil.rmtree(docs, ignore_errors=True)
    os.makedirs(f"{docs}/assets")
    for f in os.listdir(f"{ROOT}/assets"):
        shutil.copy(f"{ROOT}/assets/{f}", f"{docs}/assets/{f}")
    pages = set(slugs)

    def rewrite(m):
        slug = m.group(1).strip("/")
        if slug == "":
            return 'href="index.html"'
        return f'href="{slug}.html"' if slug in pages else 'href="#"'
    for slug in slugs:
        h = open(f"{OUT}/html/{slug}.html", encoding="utf-8").read()
        h = h.replace("../../assets/", "assets/")
        h = re.sub(r'href="' + re.escape(SITE) + r'/?([a-z0-9\-/]*)"', rewrite, h)
        name = "index.html" if slug == "inici" else f"{slug}.html"
        open(f"{docs}/{name}", "w", encoding="utf-8").write(h)
        if slug == "inici":
            open(f"{docs}/404.html", "w", encoding="utf-8").write(h)
    open(f"{docs}/.nojekyll", "w").close()


if __name__ == "__main__":
    main()
