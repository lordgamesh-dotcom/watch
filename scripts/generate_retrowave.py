#!/usr/bin/env python3
"""Generate the Retrowave watch face XML (retrowave/src/main/res/raw/watchface.xml).

480 x 480 neon-island scene in a vaporwave / Vice City style: dark sky, a half sun
made of horizontal gradient stripes, two neon triangles, a palm island, and dark
water with a shimmering reflection. On top: Monoton clock, date, a seconds marker
on the rim, and heart-rate, battery and steps panels.

Animations (all driven by [SECOND] plus Animation tweening, which renders smoothly
on the Galaxy Watch runtime): palms sway, the reflection shimmers, stars twinkle,
the neon triangles flicker now and then, and the seconds marker rotates.

Run from the repository root; the generated XML is committed.
"""
import random
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "retrowave/src/main/res/raw/watchface.xml"
H = 300        # horizon
SUN_R = 118
SUN_TOP = H - SUN_R

PALETTES = [
    dict(id="0", name="palette_island",
         sky=["#000000", "#05030F", "#0D0820"], sun=["#5AD7FF", "#A98CFF", "#FF6EC7"],
         tri_top="#4D6BFF", tri_leg="#FF7AD1", tri_small="#FFC2EC",
         water=["#120A2A", "#000000"], shadow="#05020A",
         time="#FFD1EE", glow="#FF4FB0", date="#7FE3FF",
         pink="#FF6EC7", cyan="#5AD7FF", lilac="#B9A6FF"),
    dict(id="1", name="palette_vice",
         sky=["#05010F", "#1A0730", "#4A0F45"], sun=["#FFE07A", "#FF8A5C", "#FF3C8E"],
         tri_top="#2EE6D6", tri_leg="#FF4FA0", tri_small="#FFD0E4",
         water=["#1E0B33", "#000000"], shadow="#0A0310",
         time="#FFE3F1", glow="#FF3C8E", date="#3EF0E0",
         pink="#FF4FA0", cyan="#3EF0E0", lilac="#FFD27A"),
    dict(id="2", name="palette_vapor",
         sky=["#0B0726", "#251A55", "#5A3A8A"], sun=["#A6FFF2", "#C9A7FF", "#FFA6E1"],
         tri_top="#8EF6FF", tri_leg="#FF9EDB", tri_small="#E9D5FF",
         water=["#1A1240", "#05030F"], shadow="#0B0820",
         time="#FFE6F7", glow="#FF8BD6", date="#A6FFF2",
         pink="#FF9EDB", cyan="#8EF6FF", lilac="#E9D5FF"),
]

PT = 'subText([LANGUAGE_LOCALE_NAME], 0, 2) == "pt"'
HOUR = "[IS_24_HOUR_MODE] ? [HOUR_0_23] : [HOUR_1_12]"


# ------------------------------------------------------------------ XML helpers
def E(tag, attrib=None, *children, text=None):
    el = ET.Element(tag, {k: str(v) for k, v in (attrib or {}).items()})
    for c in children:
        el.append(c)
    if text is not None:
        el.text = text
    return el


def num(v):
    return f"{v:.2f}" if isinstance(v, float) else v


def group(name, *children, **attrs):
    return E("Group", dict(name=name, x=0, y=0, width=480, height=480, **attrs), *children)


def draw(*shapes, alpha=None, transforms=()):
    a = dict(x=0, y=0, width=480, height=480)
    if alpha is not None:
        a["alpha"] = alpha
    return E("PartDraw", a, *transforms, *shapes)


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


def line(x1, y1, x2, y2, color, t=1, cap=None):
    s = stroke(color, t, **({"cap": cap} if cap else {}))
    return E("Line", dict(startX=num(x1), startY=num(y1), endX=num(x2), endY=num(y2)), s)


def rect(x, y, w, h, the_fill, *extra):
    return E("Rectangle", dict(x=num(x), y=num(y), width=num(w), height=num(h)), the_fill, *extra)


def animate(target, value, duration=1, interpolation="EASE_IN_OUT", **kw):
    return E("Transform", dict(target=target, value=value),
             E("Animation", dict(duration=duration, fps=60, interpolation=interpolation, **kw)))


def template(fmt, *exprs):
    t = E("Template", text=fmt)
    for ex in exprs:
        t.append(E("Parameter", dict(expression=ex)))
    return t


def text(x, y, w, h, content, family, size, color, align="CENTER", glow=None):
    font = E("Font", dict(family=family, size=size, color=color))
    holder = font
    if glow:
        holder = E("OutGlow", dict(color=glow[0], radius=glow[1]))
        font.append(holder)
    if isinstance(content, list):
        for c in content:
            holder.append(c)
    else:
        holder.text = content
    return E("PartText", dict(x=x, y=y, width=w, height=h), E("Text", dict(align=align), font))


def lang(pt, en):
    return [template("%s", f'{PT} ? "{pt}" : "{en}"')]


def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a[i] + (b[i] - a[i]) * t):02X}" for i in range(3))


def sun_color(p, y):
    """Sun gradient: top color at SUN_TOP, middle at half height, bottom at the horizon."""
    t = min(max((y - SUN_TOP) / SUN_R, 0), 1)
    top, mid, bot = p["sun"]
    return mix(top, mid, t * 2) if t < 0.5 else mix(mid, bot, (t - 0.5) * 2)


def chord(y, r=SUN_R):
    d = H - y
    return (r * r - d * d) ** 0.5 if abs(d) < r else 0


# ------------------------------------------------------------------ scene
def sky(p):
    return draw(rect(0, 0, 480, H, fill(p["sky"][0], vgrad(0, H, p["sky"], [0, 0.6, 1]))))


def stars():
    rnd = random.Random(11)
    buckets = [[], [], []]
    for _ in range(40):
        x, y = rnd.randint(30, 450), rnd.randint(24, SUN_TOP - 10)
        if (x - 240) ** 2 + (y - 240) ** 2 > 222 ** 2:
            continue
        r = rnd.choice([0.8, 1, 1, 1.4])
        buckets[rnd.randrange(3)].append(
            E("Ellipse", dict(x=num(x - r), y=num(y - r), width=num(2 * r), height=num(2 * r)), fill("#FFFFFF")))
    # Each bucket brightens on its own second of a 3-second cycle.
    return [draw(*b, alpha=110, transforms=[animate("alpha", f"[SECOND] % 3 == {k} ? 230 : 70")])
            for k, b in enumerate(buckets) if b]


def sun(p):
    glow = E("Ellipse", dict(x=240 - 190, y=H - 190, width=380, height=380),
             fill(p["glow"], E("RadialGradient", dict(
                 centerX=240, centerY=H, radius=190,
                 colors=f"#55{p['glow'][1:]} #22{p['glow'][1:]} #00{p['glow'][1:]}", positions="0.5 0.75 1"))))
    stripes = []
    y = SUN_TOP + 2
    while y < H - 2:
        half = chord(y + 2)
        stripes.append(line(240 - half, y + 2, 240 + half, y + 2, sun_color(p, y), 5))
        y += 9
    return [draw(glow), draw(*stripes)]


def triangle_lines(pts, colors, t):
    (a, b, c), out = pts, []
    for (p1, p2), col in zip(((a, b), (b, c), (c, a)), colors):
        out.append(line(*p1, *p2, col, t, cap="ROUND"))
    return out


def triangles(p):
    big = [(118, 184), (362, 184), (240, H - 2)]
    small = [(240, 204), (290, H - 6), (190, H - 6)]
    big_cols = [p["tri_top"], p["tri_leg"], p["tri_leg"]]
    small_cols = [p["tri_small"]] * 3
    glow = draw(*triangle_lines(big, big_cols, 10), *triangle_lines(small, small_cols, 9), alpha=55)
    core = draw(*triangle_lines(big, big_cols, 3), *triangle_lines(small, small_cols, 2.5))
    hot = draw(*triangle_lines(big, ["#FFFFFF"] * 3, 1), *triangle_lines(small, ["#FFFFFF"] * 3, 1), alpha=150)
    # Neon flicker: a short dip every 7 seconds.
    flicker = animate("alpha", "[SECOND] % 7 == 3 ? 120 : 255", duration=0.25, interpolation="LINEAR")
    return group("neon_triangles", flicker, glow, core, hot)


def quad(p0, c, p1, n):
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]))
    return pts


def palm(name, base, height, lean, color, phase):
    bx, by = base
    crown = (bx + lean, by - height)
    trunk_pts = quad(base, (bx + lean * 0.1, by - height * 0.6), crown, 10)
    shapes = []
    for i, (q0, q1) in enumerate(zip(trunk_pts, trunk_pts[1:])):
        shapes.append(line(*q0, *q1, color, 5 - i * 0.25, cap="ROUND"))
    # Fronds: (direction dx, dy, droop); drawn as tapered quadratic curves with leaflets.
    fronds = [(-30, 4, 10), (-24, -12, 8), (-8, -22, 6), (10, -22, 6), (25, -12, 8), (31, 4, 10),
              (-18, 14, 4), (18, 14, 4)]
    for dx, dy, droop in fronds:
        end = (crown[0] + dx, crown[1] + dy + droop)
        ctrl = (crown[0] + dx * 0.5, crown[1] + dy - droop * 0.6)
        pts = quad(crown, ctrl, end, 6)
        for i, (q0, q1) in enumerate(zip(pts, pts[1:])):
            shapes.append(line(*q0, *q1, color, 3.4 - i * 0.45, cap="ROUND"))
            if 1 <= i <= 4:
                ln = 6 - i * 0.8
                shapes.append(line(*q1, q1[0] + (dx > 0) * ln - (dx <= 0) * ln * 0.3, q1[1] + ln, color, 1.2))
                shapes.append(line(*q1, q1[0] - (dx > 0) * ln * 0.3 + (dx <= 0) * ln * -1, q1[1] + ln * 0.8, color, 1.2))
    sway = animate("angle", f"([SECOND] + {phase}) % 4 < 2 ? 1.6 : -1.6", duration=2)
    return E("Group", dict(name=name, x=0, y=0, width=480, height=480,
                           pivotX=num(bx / 480), pivotY=num(by / 480)), sway, draw(*shapes))


def island(p):
    mound = draw(E("Ellipse", dict(x=184, y=H - 9, width=112, height=20), fill(p["shadow"])),
                 E("Ellipse", dict(x=214, y=H - 15, width=46, height=22), fill(p["shadow"])))
    palms = [palm("palm_a", (226, H - 6), 64, -16, p["shadow"], 0),
             palm("palm_b", (248, H - 8), 82, 8, p["shadow"], 1),
             palm("palm_c", (266, H - 5), 50, 20, p["shadow"], 3)]
    return [mound, *palms]


def water(p):
    sea = draw(rect(0, H, 480, 480 - H, fill(p["water"][0], vgrad(H, 480, p["water"], [0, 1]))))
    horizon = draw(line(0, H, 480, H, p["pink"], 1.5), alpha=140)
    # Mirror of the big triangle's legs.
    mirror = draw(line(240, H + 2, 118, 2 * H - 184, p["tri_leg"], 2),
                  line(240, H + 2, 362, 2 * H - 184, p["tri_leg"], 2), alpha=45)
    # Sun reflection: stripes mirrored under the horizon, each one widening and narrowing
    # out of phase with its neighbours so the water appears to shimmer.
    bars = []
    for k in range(9):
        y = H + 4 + k * 7
        src = H - 4 - k * 9
        w = 2 * chord(src) * (0.95 - k * 0.05)
        narrow = w * 0.72
        cx = 240 + (k % 2) * 4 - 2
        alpha = max(40, 190 - k * 18)
        bars.append(draw(rect(cx - w / 2, y, w, 2.5, fill(sun_color(p, src)),
                              animate("width", f"([SECOND] + {k}) % 2 == 0 ? {w:.1f} : {narrow:.1f}"),
                              animate("x", f"([SECOND] + {k}) % 2 == 0 ? {cx - w / 2:.1f} : {cx - narrow / 2:.1f}")),
                         alpha=alpha))
    # Loose ripple dashes in the neon colours.
    rnd = random.Random(5)
    ripples = []
    for _ in range(26):
        y = rnd.randint(H + 6, 330)
        x = rnd.randint(60, 420)
        ln = rnd.randint(8, 26)
        ripples.append(line(x, y, x + ln, y, rnd.choice([p["pink"], p["cyan"], p["tri_top"]]), 1))
    return [sea, horizon, mirror, *bars, draw(*ripples, alpha=70)]


def seconds_rim(p):
    spin = animate("angle", "[SECOND] * 6", interpolation="LINEAR", angleDirection="CLOCKWISE")
    trail = []
    for k, a in enumerate((150, 95, 55, 25)):
        trail.append(draw(E("Arc", dict(centerX=240, centerY=240, width=460, height=460,
                                        startAngle=-6 * (k + 1), endAngle=-6 * k),
                            stroke(p["pink"], 3)), alpha=a))
    dot = draw(E("Ellipse", dict(x=235, y=5, width=10, height=10), fill(p["pink"])))
    rim = draw(E("Ellipse", dict(x=10, y=10, width=460, height=460), stroke(p["lilac"], 1)), alpha=60)
    return [rim, group("seconds_marker", spin, *trail, dot)]


def clock_texts(p):
    date = text(60, 44, 360, 28, [E("Upper", None, template(
        "%s   %02d   %s", 'subText(icuText("EEE"), 0, 3)', "[DAY]", 'subText(icuText("MMM"), 0, 3)'))],
        "audiowide", 18, p["date"], glow=(p["date"], 6))
    time = text(10, 72, 460, 104, [template("%02d:%02d", HOUR, "[MINUTE]")],
                "monoton", 84, p["time"], glow=(p["glow"], 12))
    return [date, time]


PANELS = [(120, "hr"), (240, "batt"), (360, "steps")]
PANEL_W, PANEL_H, PANEL_Y = 100, 62, 338


def panels(p):
    colors = {"hr": p["pink"], "batt": p["cyan"], "steps": p["lilac"]}
    shapes, glows, labels = [], [], []
    for cx, key in PANELS:
        box = dict(x=cx - PANEL_W // 2, y=PANEL_Y, width=PANEL_W, height=PANEL_H, cornerRadiusX=10, cornerRadiusY=10)
        shapes.append(E("RoundRectangle", box, fill("#D9050210"), stroke(colors[key], 1.5)))
        glows.append(E("RoundRectangle", box, stroke(colors[key], 5)))
    names = {"hr": ("BPM", "BPM"), "batt": ("BATERIA", "BATTERY"), "steps": ("PASSOS", "STEPS")}
    for cx, key in PANELS:
        labels.append(text(cx - PANEL_W // 2, PANEL_Y + 38, PANEL_W, 20, lang(*names[key]),
                           "sharetechmono", 13, colors[key]))
    battery = text(240 - PANEL_W // 2, PANEL_Y + 4, PANEL_W, 34, [template("%d%%", "[BATTERY_PERCENT]")],
                   "audiowide", 24, "#FFFFFF", glow=(p["cyan"], 6))
    return [draw(*glows, alpha=60), draw(*shapes), battery, *labels]


def palette_scene(p):
    return group(f"scene_{p['id']}", sky(p), *stars(), *sun(p), triangles(p), *island(p), *water(p),
                 *seconds_rim(p), *clock_texts(p), *panels(p))


# ------------------------------------------------------------------ complications, AOD, root
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
    # so a plain copy already reads as an outlined neon clock.
    return group(f"aod_{p['id']}",
                 text(10, 186, 460, 108, [template("%02d:%02d", HOUR, "[MINUTE]")], "monoton", 88, p["glow"]),
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
                                   ("HEART_RATE", "SHORT_TEXT"), "SHORT_TEXT RANGED_VALUE EMPTY", "#FF4FB0"))
    scene.append(complication_slot("1", 360, "comp_steps",
                                   (f"{shealth}.steps.StepsComplicationProviderService", "GOAL_PROGRESS"),
                                   ("STEP_COUNT", "SHORT_TEXT"), "GOAL_PROGRESS RANGED_VALUE SHORT_TEXT EMPTY",
                                   "#B9A6FF"))
    return root


if __name__ == "__main__":
    xml = ET.tostring(build(), encoding="unicode")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('<?xml version="1.0" encoding="utf-8"?>\n' + xml, encoding="utf-8")
    print(f"wrote {OUT} ({len(xml)} bytes)")
