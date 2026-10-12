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
SANS, SERIF, SCRIPT, IGFONT = "Jost", "Playfair Display", "Over the Rainbow", "Grand Hotel"

MENU = [("Inici", "/"), ("Projectes", "/projectes/"), ("Cuines", "/cuines/"), ("Banys", "/banys/"),
        ("Interiorisme", "/interiorisme/"), ("Parquets", "/parquets/"), ("Nosaltres", "/nosaltres/"),
        ("Contacte", "/contacte/")]
MENU_SLUG = "menu-principal"

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
def heading(text, tag="h2", font=SANS, size=16, weight=400, color="#000000", lh=1.2, ls=None, tf=None,
            style=None, align=None, href=None, cls="", hide=None, margin=None):
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
    s = {"text": text, "link": link(url), "button_text_color": color,
         "background_color": bg or "#FFFFFF00", "text_padding": box(pad),
         "border_radius": box(radius), "size": "sm"}
    rules = []
    typo(s, rules, sel, "", font, size, weight, 1, ls, tf)
    rules += [("", sel, f"color:{color}"), ("", sel, f"background-color:{bg or 'transparent'}"),
              ("", sel, f"padding:{boxcss(pad)}"), ("", sel, f"border-radius:{boxcss(radius)}")]
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
    href = url if url.startswith(("#", "http")) else SITE + url
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


def image(key, h=None, w=100, alt="", fit="cover", align=None, wunit="%", cls="", hide=None, radius=None):
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
    el = {"id": i, "elType": "widget", "settings": s, "elements": [], "widgetType": "image"}
    html = (f'<div class="elementor-element e{i} elementor-widget elementor-widget-image {cls}">'
            f'<div class="elementor-widget-container"><img src="../../assets/{key}" alt="{escape(alt)}"></div></div>')
    return Node(el, html, rules)


def icon_list(items, icon_color="#000", icon_size=14, color="#000", font=SANS, size=15, weight=400, ls=None,
              tf=None, indent=8, cls=""):
    """items: [(text, icon, url|None)]"""
    i = nid()
    s = {"icon_list": [], "view": "traditional", "icon_color": icon_color, "icon_size": sz(icon_size),
         "text_color": color, "text_indent": sz(indent), "space_between": sz(0)}
    rules = []
    sel = f".e{i} .elementor-icon-list-text"
    typo(s, rules, sel, "icon_", font, size, weight, 1.3, ls, tf)
    rules += [("", sel, f"color:{color}"), ("", f".e{i} .elementor-icon-list-icon", f"color:{icon_color}"),
              ("", f".e{i} .elementor-icon-list-icon", f"font-size:{icon_size}px"),
              ("", sel, f"padding-left:{indent}px")]
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


def divider(w=100, weight=1, color=C_LINE, grow=False, hide=None):
    i = nid()
    s = {"style": "solid", "weight": sz(weight), "color": color, "width": sz(w, "%"), "gap": sz(0)}
    rules = [("", f".e{i} .elementor-divider", "padding:0"),
             ("", f".e{i} .elementor-divider-separator", f"border-top:{weight}px solid {color}"),
             ("", f".e{i} .elementor-divider-separator", f"width:{w}%")]
    if grow:
        s["_flex_size"] = "grow"
        rules.append(("", f".e{i}", "flex:1 1 auto"))
    _hide(s, rules, f".e{i}", hide)
    el = {"id": i, "elType": "widget", "settings": s, "elements": [], "widgetType": "divider"}
    html = (f'<div class="elementor-element e{i} elementor-widget elementor-widget-divider">'
            f'<div class="elementor-widget-container"><div class="elementor-divider">'
            f'<span class="elementor-divider-separator"></span></div></div></div>')
    return Node(el, html, rules)


def nav_menu(active="Inici", size=15, weight=300, color="#fff", space=22, vpad=5, hpad=9):
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
            f'<button class="elementor-menu-toggle" aria-label="Menú" onclick="this.parentNode.classList.toggle(\'open\')">'
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
        s["grid_rows_grid"] = sz(rows, "fr")
        put(s, "grid_gaps", gap, gapv)
        rules.append(("", lay, "display:grid"))
        rule(rules, lay, "grid-template-columns", cols, lambda v: f"repeat({v},1fr)")
        rules.append(("", lay, f"grid-template-rows:repeat({rows},1fr)"))
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
        put(s, "width", width, lambda v: sz(v, "%"))
        rule(rules, outer, "--w", width, lambda v: f"{v}%")
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
    btn = button("Demana pressupost", "/contacte/", bg=C_BROWN, color="#fff", size=16, weight=400,
                 pad=(15, 30, 15, 30), border="#8C7358", radius=2, hide=["mobile"])
    return container([logo, nav, btn], dir="row", justify="space-between", align="center",
                     gap=24, pad=R((16, 19, 16, 96), (16, 24, 16, 24), (14, 16, 14, 16)),
                     pos={"type": "absolute", "x": 0, "y": 0}, z=100, cls="cl-header")


def ftr():
    eyebrow = heading("COMENCEM?", "p", SANS, 13, 400, "#FFFFFFCC", 1.2, 2.5)
    h = heading("Parlem del teu projecte", "h2", SERIF, R(48, 40, 34), 400, "#FFFFFF", 1.15)
    p = heading("Explica'ns la teva idea i t'assessorem sense compromís.", "p", SANS, 18, 300,
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
    contact = container(cells, grid=(R(3, 3, 1), 2), gap=R(14, 14, 10), inner=True, pad=0)
    right = container([cta, contact], gap=28, inner=True, width=R(50, 100), pad=0,
                      align=R("flex-start", "flex-start", "flex-start"))
    top = container([left, right], dir=R("row", "column", "column"), justify="space-between", align="center",
                    gap=R(60, 36, 32), inner=True, pad=0)
    copy = heading("Copyright CREEM LLAR", "p", SANS, 14, 300, "#FFFFFFB3", 1.2)
    wa = icon("fab fa-whatsapp", 32, "#fff", pos=(24, 24), link_url="https://wa.me/34972684896",
              view="stacked", bgc="#25D366", pad=15, shape="circle")
    return container([top, copy, wa], gap=32, boxed=1320,
                     pad=R((70, 60, 40, 60), (60, 40, 32, 40), (48, 24, 28, 24)),
                     cls="cl-footer")


def ftr_wrap():
    """El footer porta fons a tot l'ample: contenidor exterior ple + contingut boxed."""
    inner = ftr()
    return container([inner], gap=0, pad=0,
                     grad={"a": "#4B3F36", "b": "#2A2420", "angle": 125, "ap": 0, "bp": 100}, cls="cl-footer-wrap")


def hero(img, ph, p_text, btn_text, btn_url, eyebrow=None, minh=572, py=(110, 40), arrow=True):
    kids = []
    if eyebrow:
        kids.append(heading(eyebrow, "p", SANS, 16, 300, "#FFFFFFE6", 1.2, 3))
    kids.append(heading("Espais<br>fets a mida", "h1", SANS, R(74, 60, 44), 300, "#FFFFFF", 1.05))
    kids.append(heading(p_text, "p", SANS, R(24, 22, 19), 300, "#FFFFFFF2", 1.4))
    kids.append(button(btn_text, btn_url, bg=C_TAN, color="#2B2118", size=15, weight=500, ls=1.2,
                       pad=(20, 34, 20, 34), radius=1, tf="uppercase" if arrow else None,
                       icon="fas fa-long-arrow-alt-right"))
    return container(kids, gap=R(22, 20, 18), justify="center", align="flex-start",
                     pad=R((py[0], 60, py[1], 133), (110, 48, 40, 48), (110, 24, 40, 24)),
                     minh=R(minh, 520, 520), bgimg=img, bgpos="right center", cls="cl-hero",
                     overlay={"a": "#1A120CCC", "b": "#1A120C00", "angle": 90, "ap": 0, "bp": 62})


def tile(img, title, text):
    return container([image(img, h=R(229, 220, 200), alt=title),
                      heading(title, "h3", SANS, 27, 500, "#141413", 1.2),
                      heading(text, "p", SANS, 16, 300, C_TEXT, 1.45)],
                     gap=10, inner=True, pad=0, align="stretch")


def categories():
    tiles = [tile("cat-cuines.jpg", "Cuines", "Dissenys funcionals i elegants per al teu dia a dia."),
             tile("cat-banys.jpg", "Banys", "Espais moderns, còmodes i plens de benestar."),
             tile("cat-interiorisme.jpg", "Interiorisme", "Solucions a mida per a cada estil de vida."),
             tile("cat-reformes.jpg", "Reformes", "Transformem els teus espais amb garantia i experiència.")]
    grid = container(tiles, grid=(R(4, 2, 1), 1), gap=R(37, 28, 28), inner=True, pad=0)
    return container([grid], boxed=1310, bg=C_BG2, pad=R((46, 65, 40, 65), (40, 40, 36, 40), (32, 24, 32, 24)),
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
                                heading(t, "h3", SANS, 22, 400, "#141413", 1.2, align="center"),
                                heading(d, "p", SANS, 15, 300, C_TEXT, 1.4, align="center")],
                               gap=10, inner=True, align="center",
                               pad=R((36, 20, 36, 20), (30, 20, 30, 20), (24, 12, 24, 12)),
                               border=C_LINE,
                               bw=R((0, 0 if last else 1, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0))))
    grid = container(cells, grid=(R(4, 2, 1), 1), gap=0, inner=True, pad=0)
    return container([grid], boxed=1310, bg=C_BG3, pad=R((0, 65, 0, 65), (0, 40, 0, 40), (0, 24, 0, 24)),
                     gap=0, cls="cl-props")


def feat_card(img, title, city, arrow_url="/projectes/"):
    text = container([heading(title, "h3", SANS, 22, 400, "#141413", 1.2),
                      heading(city.upper(), "p", SANS, 13, 400, C_TEXT, 1.2, 2)],
                     gap=6, inner=True, pad=0, width=80)
    row = container([text, icon("fas fa-long-arrow-alt-right", 22, "#141413", align="right")],
                    dir="row", justify="space-between", align="center", gap=10, inner=True, pad=0)
    return container([image(img, h=R(262, 240, 220), alt=title), row], gap=14, inner=True, pad=0)


def featured():
    head_l = container([heading("PROJECTES DESTACATS", "p", SANS, 13, 400, C_TEXT, 1.2, 2.5),
                        heading("Espais que inspiren", "h2", SERIF, R(52, 44, 36), 400, "#111111", 1.1)],
                       gap=8, inner=True, pad=0, width=60)
    head_r = button("Veure tots els projectes", "/projectes/", None, C_DARK, 15, 400, 0, (4, 0, 4, 0),
                    border=C_DARK, bw=(0, 0, 1, 0), radius=0, icon="fas fa-long-arrow-alt-right")
    head = container([head_l, head_r], dir="row", justify="space-between", align="flex-end", gap=20,
                     inner=True, pad=0)
    cards = [feat_card("home-proj-1.jpg", "Cuina contemporània", "Figueres"),
             feat_card("home-proj-2.jpg", "Bany amb caràcter", "Banyoles"),
             feat_card("home-proj-3.jpg", "Reforma integral", "Figueres")]
    grid = container(cards, grid=(R(3, 2, 1), 1), gap=R(18, 18, 28), inner=True, pad=0)
    return container([head, grid], gap=26, boxed=1320, bg=C_BG,
                     pad=R((64, 60, 56, 60), (56, 40, 48, 40), (44, 24, 40, 24)), cls="cl-featured")


def metode():
    left = container([heading("EL NOSTRE MÈTODE", "p", SANS, 12, 400, C_TEXT, 1.2, 2.5),
                      heading("Un procés senzill,<br>amb grans resultats", "h2", SERIF, R(40, 36, 32), 400, C_NAVY, 1.2)],
                     gap=14, inner=True, width=R(30, 100), pad=0)
    steps = []
    data = [("01", "far fa-comment", "Escoltem", "Analitzem les teves necessitats i et proposem idees a mida."),
            ("02", "far fa-file-alt", "Dissenyem", "Planifiquem cada detall amb rigor i transparència."),
            ("03", "fas fa-wrench", "Fem realitat", "Ens ocupem de tot perquè només gaudeixis del resultat.")]
    for num, ic, t, d in data:
        top = container([heading(num, "p", SERIF, 34, 400, "#5A5550", 1, style="italic"),
                         icon(ic, 30, "#2B2B2B"), divider(100, 1, "#8F877D", grow=True)],
                        dir="row", align="center", gap=14, inner=True, pad=0)
        steps.append(container([top, heading(t, "h3", SANS, 20, 500, "#141413", 1.2),
                                heading(d, "p", SANS, 15, 300, C_TEXT, 1.45)],
                               gap=10, inner=True, pad=0))
    steps_grid = container(steps, grid=(R(3, 1, 1), 1), gap=R(34, 28, 28), inner=True,
                           pad=R((0, 0, 0, 44), (0, 0, 0, 0), (0, 0, 0, 0)), border=C_LINE,
                           bw=R((0, 0, 0, 1), (0, 0, 0, 0), (0, 0, 0, 0)), width=R(70, 100))
    row = container([left, steps_grid], dir=R("row", "column", "column"), align="center",
                    gap=R(44, 32, 28), inner=True, pad=0)
    return container([row], boxed=1310, bg=C_METODE, gap=0,
                     pad=R((44, 65, 44, 65), (44, 40, 44, 40), (36, 24, 36, 24)), cls="cl-metode")


def quote(text, size=32):
    return container([heading(text, "p", SCRIPT, size, 400, "#3A3A3A", 1.45),
                      divider(40, 1, "#3A3A3A")], gap=10, inner=True, pad=0, width=R(30, 100),
                     align="flex-start", hide=None)


def interiorisme(titulo="Dissenyem espais<br>per cada estil de vida"):
    img = container([], inner=True, width=R(45.5, 100), bgimg="interiorisme.jpg", minh=R(434, 300),
                    pad=0)
    kids = [heading("INTERIORISME A FIGUERES | BANYOLES", "p", SANS, 12, 400, "#4A443F", 1.2, 2.5),
            heading(titulo, "h2", SERIF, R(46, 40, 34), 400, "#141413", 1.15),
            heading("Creem cuines, banys i espais que combinen estètica, funcionalitat i benestar, sempre "
                    "adaptats al teu estil de vida i a l'entorn on vius.", "p", SANS, 17, 300, "#2E2A27", 1.5),
            button("Parlem del teu projecte", "/contacte/", bg=C_DARK, color="#fff", size=16, weight=400,
                   pad=(18, 34, 18, 34), radius=1, icon="fas fa-long-arrow-alt-right")]
    text = container(kids, gap=18, inner=True, pad=0, width=R(70, 100), align="flex-start")
    q = quote("“ La teva llar,<br>el nostre<br>compromís ”", 30)
    right = container([text, q], dir=R("row", "column", "column"), align=R("center", "flex-start", "flex-start"),
                      gap=R(30, 28, 24), inner=True, width=R(54.5, 100), bg=C_BEIGE,
                      pad=R((60, 60, 60, 70), (48, 40, 48, 40), (40, 24, 40, 24)), justify="center")
    return container([img, right], dir=R("row", "column", "column"), gap=0, align="stretch", pad=0,
                     cls="cl-split")


def equip():
    img = container([image("equip.jpg", h=R(255, 240, 220), alt="L'equip de Creem Llar")],
                    inner=True, width=R(36, 100), pad=0)
    text = container([heading("PERSONES QUE FAN POSSIBLE CREEM LLAR", "p", SANS, 12, 400, "#4A443F", 1.2, 2.5),
                      heading("Un equip al teu costat", "h2", SERIF, R(36, 32, 30), 400, "#141413", 1.15),
                      heading("Som un estudi d'interiorisme amb arrels a Figueres, apassionats pel disseny i la "
                              "qualitat. Treballem amb proximitat, escolta i compromís per crear espais únics, "
                              "pensats per a tu.", "p", SANS, 16, 300, "#2E2A27", 1.55),
                      button("Coneix l'equip", "/nosaltres/", None, C_DARK, 15, 400, 0, (4, 0, 4, 0),
                             border=C_DARK, bw=(0, 0, 1, 0), radius=0, icon="fas fa-long-arrow-alt-right")],
                     gap=14, inner=True, pad=0, width=R(44, 100), align="flex-start")
    q = quote("“ Llar<br>és molt més<br>que un lloc ”", 30)
    return container([img, text, q], dir=R("row", "column", "column"), align=R("center", "flex-start", "flex-start"),
                     gap=R(48, 28, 24), boxed=1440, bg="#FFFFFF",
                     pad=R((40, 74, 40, 74), (40, 40, 40, 40), (36, 24, 36, 24)), cls="cl-team")


def insta_head():
    ico = icon("fab fa-instagram", 34, "#E1306C")
    name = heading("Instagram", "p", IGFONT, 30, 400, "#262626", 1)
    txt = heading("SEGUEIX-NOS A INSTAGRAM I ESTIGUES ACTUALITZAT DE LES TENDÈNCIES", "p", SANS,
                  R(17, 15, 13), 400, "#141413", 1.3, 0.6)
    return container([container([ico, name], dir="row", align="center", gap=8, inner=True, pad=0,
                                 width=R(17, 100)), txt],
                     dir=R("row", "row", "column"), align=R("center", "center", "flex-start"), gap=R(36, 24, 12),
                     bg="#FFFFFF", pad=R((16, 38, 14, 38), (16, 40, 14, 40), (16, 24, 14, 24)),
                     cls="cl-ig-head")


def insta_feed():
    feed = image("instagram-feed.jpg", h=None, w=100, alt="Feed d'Instagram de Creem Llar")
    more = button("Veure més", "https://www.instagram.com/", None, "#FFFFFF", 14, 400, 0, (6, 0, 6, 0),
                  radius=0, align="right")
    return container([feed, more], gap=0, bg="#0A0D12", pad=R((0, 38, 12, 38), (0, 20, 12, 20), (0, 16, 12, 16)),
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
                     pad=R((20, 22, 18, 22), (20, 22, 18, 22), (20, 18, 16, 18)),
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
                     align=R("flex-end", "flex-start", "flex-start"), gap=R(40, 24, 20), boxed=1380,
                     pad=R((60, 30, 28, 30), (52, 40, 24, 40), (40, 24, 20, 24)), bg=C_BG, cls="cl-pintro")


def proj_filters():
    labels = [("Tots", "tots"), ("Cuina", "cuina"), ("Banys", "banys"), ("Interiorisme", "interiorisme"),
              ("Reformes", "reformes"), ("Parquets", "parquets")]
    btns = []
    for lab, key in labels:
        btns.append(button(lab, f"#{key}", bg="#FFFFFF00", color="#1E1B19", size=17, weight=400,
                           pad=(15, 28, 15, 28), border="#CFC8BF", radius=1,
                           cls="cl-filter is-active" if key == "tots" else "cl-filter",
                           hover_bg="#FFFFFF00"))
    return container(btns, dir="row", justify="center", align="center", wrap=True, gap=12, boxed=1380,
                     pad=R((14, 30, 30, 30), (10, 40, 24, 40), (8, 24, 20, 24)), bg=C_BG, cls="cl-filters")


def proj_grid():
    cards = [proj_card(n + 1, t, c, k) for n, (t, c, k) in enumerate(PROJECTS)]
    grid = container(cards, grid=(R(3, 2, 1), 5), gap=R(24, 20, 18), inner=True, pad=0)
    return container([grid, html_widget(FILTER_JS)], boxed=1380, bg=C_BG, gap=0,
                     pad=R((0, 30, 70, 30), (0, 40, 56, 40), (0, 24, 44, 24)), cls="cl-pgrid")


# ================================================================ PÀGINES
def page_inici():
    return [hero("hero-inici.jpg", None, "Cuines, banys i interiorisme<br>per crear llars úniques",
                 "Veure projectes", "/projectes/", eyebrow="FIGUERES  |  BANYOLES"),
            categories(), props(), featured(), metode(), interiorisme(), equip(), insta_head(), insta_feed()]


def page_projectes():
    return [hero("hero-projectes.jpg", None, "Cuines, banys, interiorisme, reformes<br>i parquets per crear llars "
                 "úniques", "Contactar amb nosaltres", "/contacte/", minh=505, py=(120, 40), arrow=False),
            proj_intro(), proj_filters(), proj_grid(),
            interiorisme("Dissenyem espais<br>per a persones reals"), equip()]


# ================================================================ SORTIDA
BASE_CSS = """
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:#F8F5F0;font-family:'Jost',sans-serif;-webkit-font-smoothing:antialiased;position:relative;overflow-x:hidden}
img{max-width:100%;height:auto;vertical-align:middle;display:inline-block;border:0}
a{text-decoration:none;color:inherit}
.e-con{display:flex;flex-direction:column;position:relative;width:100%;min-width:0;--w:100%}
.e-con>.e-con-inner{display:flex;flex-direction:column;width:100%;margin:0 auto;min-width:0}
.e-con.e-child{width:var(--w);flex:0 1 auto}
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
.elementor-menu-toggle{display:none;background:none;border:0;color:#fff;font-size:24px;cursor:pointer}
.elementor-divider{display:block}
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


GFONTS = ("https://fonts.googleapis.com/css2?family=Jost:ital,wght@0,300;0,400;0,500;0,600&"
          "family=Playfair+Display:ital,wght@0,400;0,500;1,400&family=Over+the+Rainbow&family=Grand+Hotel&display=swap")


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
    pages = [("inici", "Inici", "Inici", page_inici), ("projectes", "Projectes", "Projectes", page_projectes)]
    for slug, title, active, fn in pages:
        nodes = fn()
        write_json(slug, f"Creem Llar - {title}", "page", nodes, ps)
        write_html(slug, title, [hdr(active)] + nodes + [footer])

    with open(f"{OUT}/html/index.html", "w", encoding="utf-8") as f:
        f.write("<!doctype html><meta charset=utf-8><title>Creem Llar</title>"
                "<body style='font-family:sans-serif;padding:40px'><h1>Previsualitzacions</h1><ul>"
                + "".join(f"<li><a href='{s}.html'>{t}</a></li>" for s, t, _, _ in pages) + "</ul>")
    standalone()
    print("OK ->", OUT)


def standalone():
    """HTML autocontingut (imatges en base64) per descarregar i obrir directament."""
    import base64, re
    os.makedirs(f"{OUT}/descarregar", exist_ok=True)
    for slug in ("inici", "projectes"):
        h = open(f"{OUT}/html/{slug}.html", encoding="utf-8").read()

        def rep(m):
            fn = m.group(1)
            b = base64.b64encode(open(f"{ROOT}/assets/{fn}", "rb").read()).decode()
            return f"data:image/jpeg;base64,{b}"
        h = re.sub(r"\.\./\.\./assets/([\w\-\.]+\.jpg)", rep, h)
        open(f"{OUT}/descarregar/{slug}.html", "w", encoding="utf-8").write(h)


if __name__ == "__main__":
    main()
