#!/usr/bin/env python3
"""Generate the Retrowave watch face XML (retrowave/src/main/res/raw/watchface.xml).

The face is a 480 x 480 synthwave scene: gradient sky with stars, striped half sun,
wireframe mountains, neon perspective grid, Monoton clock, and two complication
panels plus battery. Run from the repository root; the output is committed.
"""
import random
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "retrowave/src/main/res/raw/watchface.xml"
H = 292  # horizon line
SUN_R = 108

PALETTES = [
    dict(id="0", name="palette_sunset",
         sky=["#0B0120", "#2B0A4A", "#7A1B6B"], sun=["#FFE66D", "#FF9A3C", "#FF2E88"],
         pink="#FF2E88", cyan="#2DE2E6", grid="#FF2E88", gold="#FFD34E",
         mount_fill="#1A0533", mount_edge="#B026FF", ground="#1A0230"),
    dict(id="1", name="palette_miami",
         sky=["#06021A", "#1C0B4D", "#3B1C8C"], sun=["#FFF3B0", "#FF8ED4", "#C653FF"],
         pink="#FF5FD2", cyan="#5CF2FF", grid="#33E8FF", gold="#FFF3B0",
         mount_fill="#130838", mount_edge="#7B5CFF", ground="#0C0626"),
    dict(id="2", name="palette_outrun",
         sky=["#000000", "#14001F", "#4B0030"], sun=["#FFD319", "#FF6B1A", "#E8115B"],
         pink="#F222FF", cyan="#00D9FF", grid="#FF2079", gold="#FFD319",
         mount_fill="#12001C", mount_edge="#8C1EFF", ground="#100014"),
]

PT = 'subText([LANGUAGE_LOCALE_NAME], 0, 2) == "pt"'
HOUR = "[IS_24_HOUR_MODE] ? [HOUR_0_23] : [HOUR_1_12]"


def E(tag, attrib=None, *children, text=None):
    el = ET.Element(tag, {k: str(v) for k, v in (attrib or {}).items()})
    for c in children:
        el.append(c)
    if text is not None:
        el.text = text
    return el


def group(name, *children, **attrs):
    return E("Group", dict(name=name, x=0, y=0, width=480, height=480, **attrs), *children)


def draw(*shapes, alpha=None):
    a = dict(x=0, y=0, width=480, height=480)
    if alpha is not None:
        a["alpha"] = alpha
    return E("PartDraw", a, *shapes)


def stroke(color, t, **kw):
    return E("Stroke", dict(color=color, thickness=t, **kw))


def fill(color, gradient=None):
    f = E("Fill", dict(color=color))
    if gradient is not None:
        f.append(gradient)
    return f


def vgrad(y0, y1, colors, positions):
    return E("LinearGradient", dict(startX=0, startY=y0, endX=0, endY=y1,
                                    colors=" ".join(colors), positions=" ".join(map(str, positions))))


def line(x1, y1, x2, y2, color, t=1):
    f = lambda v: f"{v:.2f}" if isinstance(v, float) else v
    return E("Line", dict(startX=f(x1), startY=f(y1), endX=f(x2), endY=f(y2)), stroke(color, t))


def rect(x, y, w, h, the_fill):
    return E("Rectangle", dict(x=x, y=y, width=w, height=h), the_fill)


def template(fmt, *exprs):
    t = E("Template", text=fmt)
    for ex in exprs:
        t.append(E("Parameter", dict(expression=ex)))
    return t


def text(x, y, w, h, content, family, size, color, align="CENTER", glow=None):
    font = E("Font", dict(family=family, size=size, color=color))
    body = content if isinstance(content, list) else None
    if glow:
        holder = E("OutGlow", dict(color=glow[0], radius=glow[1]))
        font.append(holder)
    else:
        holder = font
    if body is None:
        holder.text = content
    else:
        for c in body:
            holder.append(c)
    return E("PartText", dict(x=x, y=y, width=w, height=h), E("Text", dict(align=align), font))


def lang(pt, en):
    return [template("%s", f'{PT} ? "{pt}" : "{en}"')]


# ------------------------------------------------------------------ scene pieces
def sky(p):
    return draw(rect(0, 0, 480, H, fill(p["sky"][0], vgrad(0, H, p["sky"], [0, 0.55, 1]))))


def stars():
    rnd = random.Random(7)
    dots = []
    for _ in range(34):
        x, y = rnd.randint(40, 440), rnd.randint(30, H - 70)
        if (x - 240) ** 2 + (y - 240) ** 2 > 225 ** 2:
            continue
        r = rnd.choice([1, 1, 1.5, 2])
        a = rnd.choice(["66", "99", "CC", "FF"])
        dots.append(E("Ellipse", dict(x=x, y=y, width=r * 2, height=r * 2), fill(f"#{a}FFFFFF")))
    return draw(*dots)


def sun(p):
    top = H - SUN_R
    glow = E("Ellipse", dict(x=240 - 175, y=H - 175, width=350, height=350),
             fill(p["pink"], E("RadialGradient", dict(
                 centerX=240, centerY=H, radius=175,
                 colors=f"#80{p['pink'][1:]} #40{p['pink'][1:]} #00{p['pink'][1:]}", positions="0.55 0.75 1"))))
    disc = E("Ellipse", dict(x=240 - SUN_R, y=top, width=SUN_R * 2, height=SUN_R * 2),
             fill(p["sun"][0], vgrad(top, H, p["sun"], [0, 0.5, 1])))
    # Stripes reuse the sky gradient, so they read as gaps in the sun.
    stripes = []
    for y, h in [(H - 15, 9), (H - 31, 7), (H - 45, 5), (H - 57, 4), (H - 68, 3), (H - 77, 2)]:
        # Clip each stripe to the sun's chord at its widest row so it never spills into the sky.
        half = (SUN_R ** 2 - (H - (y + h)) ** 2) ** 0.5 + 1
        stripes.append(rect(round(240 - half), y, round(half * 2), h,
                            fill(p["sky"][2], vgrad(0, H, p["sky"], [0, 0.55, 1]))))
    return [draw(glow), draw(disc, *stripes)]


def polygon_fill(pts, color):
    """Scanline-fill a simple polygon with 1px horizontal lines."""
    out = []
    ys = [y for _, y in pts]
    for y in range(int(min(ys)), int(max(ys))):
        yc = y + 0.5
        xs = []
        for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
            if (y1 <= yc < y2) or (y2 <= yc < y1):
                xs.append(x1 + (yc - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]):
            out.append(line(float(a), yc, float(b), yc, color))
    return out


def mountains(p):
    left = [(0, H), (0, 268), (34, 252), (60, 270), (96, 226), (128, 262), (150, 248), (200, H)]
    right = [(480 - x, y) for x, y in left]
    parts = []
    for pts in (left, right):
        parts += polygon_fill(pts, p["mount_fill"])
    edges = []
    for pts in (left, right):
        ridge = pts[1:]
        for (x1, y1), (x2, y2) in zip(ridge, ridge[1:]):
            edges.append(line(x1, y1, x2, y2, p["mount_edge"], 2))
    glow = [line(l.get("startX"), l.get("startY"), l.get("endX"), l.get("endY"), p["mount_edge"], 6) for l in edges]
    return [draw(*parts), draw(*glow, alpha=50), draw(*edges)]


def ground(p):
    return draw(rect(0, H, 480, 480 - H, fill(p["ground"], vgrad(H, 480, [p["ground"], "#000000"], [0, 1]))))


def grid(p):
    rows = [3, 8, 15, 25, 38, 55, 77, 105, 140, 185]
    lines = [line(0, H + d, 480, H + d, p["grid"], 1.5 if d > 30 else 1) for d in rows]
    for i in range(-12, 13):
        xb = 240 + i * 60
        xs = 240 + i * 60 * (2 / (480 - H))
        lines.append(line(xs, H + 2, xb, 480, p["grid"], 1.5))
    glow = [line(l.get("startX"), l.get("startY"), l.get("endX"), l.get("endY"), p["grid"], 4) for l in lines]
    horizon = [line(0, H, 480, H, p["pink"], 6)]
    return [draw(*glow, alpha=45), draw(*lines, alpha=200), draw(*horizon, alpha=90),
            draw(line(0, H, 480, H, p["sun"][0], 2))]


def seconds_rim(p):
    # Rotates clockwise one step per second, tweened at 60 fps (same approach as the HUD face).
    spin = E("Transform", dict(target="angle", value="[SECOND] * 6"),
             E("Animation", dict(duration=1, fps=60, interpolation="LINEAR", angleDirection="CLOCKWISE")))
    trail = []
    for k, a in enumerate((150, 95, 55, 25)):
        trail.append(draw(E("Arc", dict(centerX=240, centerY=240, width=460, height=460,
                                        startAngle=-6 * (k + 1), endAngle=-6 * k),
                            stroke(p["sun"][0], 3)), alpha=a))
    dot = draw(E("Ellipse", dict(x=235, y=5, width=10, height=10), fill(p["sun"][0])))
    rim = draw(E("Ellipse", dict(x=10, y=10, width=460, height=460), stroke(p["pink"], 1)), alpha=70)
    return [rim, group("seconds_marker", spin, *trail, dot)]


def clock_texts(p):
    date = text(60, 54, 360, 28, [E("Upper", None, template(
        "%s   %02d   %s", 'subText(icuText("EEE"), 0, 3)', "[DAY]", 'subText(icuText("MMM"), 0, 3)'))],
        "audiowide", 18, p["cyan"], glow=(p["cyan"], 6))
    time = text(10, 88, 460, 108, [template("%02d:%02d", HOUR, "[MINUTE]")],
                "monoton", 88, p["pink"], glow=(p["pink"], 10))
    return [date, time]


PANELS = [(120, "hr"), (240, "batt"), (360, "steps")]
PANEL_W, PANEL_H, PANEL_Y = 100, 62, 334


def panels(p):
    colors = {"hr": p["pink"], "batt": p["cyan"], "steps": p["gold"]}
    shapes, glows, labels = [], [], []
    for cx, key in PANELS:
        x = cx - PANEL_W // 2
        shapes.append(E("RoundRectangle", dict(x=x, y=PANEL_Y, width=PANEL_W, height=PANEL_H,
                                               cornerRadiusX=10, cornerRadiusY=10),
                        fill("#D9080014"), stroke(colors[key], 1.5)))
        glows.append(E("RoundRectangle", dict(x=x, y=PANEL_Y, width=PANEL_W, height=PANEL_H,
                                              cornerRadiusX=10, cornerRadiusY=10), stroke(colors[key], 5)))
    names = {"hr": ("BPM", "BPM"), "batt": ("BATERIA", "BATTERY"), "steps": ("PASSOS", "STEPS")}
    for cx, key in PANELS:
        labels.append(text(cx - PANEL_W // 2, PANEL_Y + 38, PANEL_W, 20, lang(*names[key]),
                           "sharetechmono", 13, colors[key]))
    battery = text(240 - PANEL_W // 2, PANEL_Y + 4, PANEL_W, 34, [template("%d%%", "[BATTERY_PERCENT]")],
                   "audiowide", 24, "#FFFFFF", glow=(p["cyan"], 6))
    return [draw(*glows, alpha=60), draw(*shapes), battery, *labels]


def palette_scene(p):
    return group(f"scene_{p['id']}", sky(p), stars(), *sun(p), *mountains(p), ground(p), *grid(p),
                 *seconds_rim(p), *clock_texts(p), *panels(p))


def complication_slot(slot_id, cx, name, primary, system, types, glow):
    value = lambda content: text(0, 4, PANEL_W, 34, content, "audiowide", 24, "#FFFFFF", glow=(glow, 6))
    has_text = 'textLength([COMPLICATION.TEXT]) > 0 && [COMPLICATION.TEXT] != "--"'
    txt = [template("%s", "[COMPLICATION.TEXT]")]

    def cond(expr, yes, no):
        return E("Condition", None, E("Expressions", None, E("Expression", dict(name="has_text"), text=expr)),
                 E("Compare", dict(expression="has_text"), yes), E("Default", None, no))

    slot = E("ComplicationSlot", dict(x=cx - PANEL_W // 2, y=PANEL_Y, width=PANEL_W, height=PANEL_H,
                                      slotId=slot_id, displayName=name, supportedTypes=types),
             E("DefaultProviderPolicy", dict(defaultSystemProvider=system[0], defaultSystemProviderType=system[1],
                                             primaryProvider=primary[0], primaryProviderType=primary[1])),
             E("BoundingBox", dict(x=0, y=0, width=PANEL_W, height=PANEL_H)),
             E("Variant", dict(mode="AMBIENT", target="alpha", value=0)))
    slot.append(E("Complication", dict(type="SHORT_TEXT"), cond(has_text, value(txt), value("--"))))
    slot.append(E("Complication", dict(type="RANGED_VALUE"),
                  cond(has_text, value(txt), value([template("%d", "round([COMPLICATION.RANGED_VALUE_VALUE])")]))))
    if "GOAL_PROGRESS" in types:
        slot.append(E("Complication", dict(type="GOAL_PROGRESS"),
                      value([template("%d", "round([COMPLICATION.GOAL_PROGRESS_VALUE])")])))
    slot.append(E("Complication", dict(type="EMPTY"), value("--")))
    return slot


def aod(p):
    # Galaxy Watch AOD offload only rendered plain PartText in testing; Monoton is a line font,
    # so a plain dim copy already reads as an outlined neon clock.
    return group(f"aod_{p['id']}",
                 text(10, 186, 460, 108, [template("%02d:%02d", HOUR, "[MINUTE]")], "monoton", 88, p["pink"]),
                 alpha=0)


def build():
    root = E("WatchFace", dict(width=480, height=480))
    root.append(E("Metadata", dict(key="CLOCK_TYPE", value="DIGITAL")))
    root.append(E("Metadata", dict(key="PREVIEW_TIME", value="10:09:00")))
    root.append(E("UserConfigurations", None,
                  E("ListConfiguration", dict(id="palette", defaultValue="0", displayName="palette_label",
                                              screenReaderText="palette_label"),
                    *[E("ListOption", dict(id=p["id"], displayName=p["name"])) for p in PALETTES])))
    scene = E("Scene", dict(backgroundColor="#000000"))
    root.append(scene)

    active = E("ListConfiguration", dict(id="palette"),
               *[E("ListOption", dict(id=p["id"]), palette_scene(p)) for p in PALETTES])
    scene.append(group("active_face", E("Variant", dict(mode="AMBIENT", target="alpha", value=0)), active))

    aod_groups = []
    for p in PALETTES:
        g = aod(p)
        g.insert(0, E("Variant", dict(mode="AMBIENT", target="alpha", value=255)))
        aod_groups.append(E("ListOption", dict(id=p["id"]), g))
    scene.append(E("ListConfiguration", dict(id="palette"), *aod_groups))

    shealth = "com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.complications"
    scene.append(complication_slot("0", 120, "comp_hr",
                                   (f"{shealth}.heartrate.HeartrateComplicationProviderService", "SHORT_TEXT"),
                                   ("HEART_RATE", "SHORT_TEXT"), "SHORT_TEXT RANGED_VALUE EMPTY", "#FF2E88"))
    scene.append(complication_slot("1", 360, "comp_steps",
                                   (f"{shealth}.steps.StepsComplicationProviderService", "GOAL_PROGRESS"),
                                   ("STEP_COUNT", "SHORT_TEXT"), "GOAL_PROGRESS RANGED_VALUE SHORT_TEXT EMPTY",
                                   "#FFD34E"))
    return root


if __name__ == "__main__":
    xml = ET.tostring(build(), encoding="unicode")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('<?xml version="1.0" encoding="utf-8"?>\n' + xml, encoding="utf-8")
    print(f"wrote {OUT} ({len(xml)} bytes)")
