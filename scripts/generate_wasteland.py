#!/usr/bin/env python3
"""Generate the Wasteland Terminal watch face XML (wasteland/src/main/res/raw/watchface.xml).

Original retro-futuristic terminal design: phosphor CRT glow, scanlines with a rolling
scan band, VT323 clock with blinking colon, a command-line date with blinking cursor,
an analog pulse gauge driven by the heart-rate complication, a status panel (steps,
power, seconds), a segmented power bar, and a stepping seconds marker on the bezel.
Run from the repository root; the generated XML is committed.
"""
from pathlib import Path

from wfflib import (E, HOUR, SHEALTH, animate, arc, condition, draw, fill, group, lang, line, num,
                    rect, stroke, template, text, text_number, write)

OUT = Path(__file__).resolve().parent.parent / "wasteland/src/main/res/raw/watchface.xml"
FONT = "vt323"
CHAR = 0.4  # VT323 advance width, in em

PALETTES = [
    dict(id="0", name="palette_green", main="#41FF7A", bright="#C8FFD6", dim="#1F8A42", dark="#06240F",
         bg=["#0B3317", "#03140A", "#000000"]),
    dict(id="1", name="palette_amber", main="#FFB43C", bright="#FFE6B3", dim="#94621A", dark="#241604",
         bg=["#33200A", "#140C03", "#000000"]),
    dict(id="2", name="palette_ice", main="#7FE8FF", bright="#E0FAFF", dim="#2F7F93", dark="#05212A",
         bg=["#0B2C38", "#03121A", "#000000"]),
]

TIME_SIZE = 170
TIME_X = round(240 - 5 * CHAR * TIME_SIZE / 2)
DATE_SIZE = 26
DATE_CHARS = 18  # "> SAB 07.NOV.2026_"
DATE_X = round(240 - DATE_CHARS * CHAR * DATE_SIZE / 2)

LEFT = (62, 258, 170, 92)    # pulse panel x, y, w, h
RIGHT = (248, 258, 170, 92)  # status panel
GAUGE = (85, 80, 54)         # center x, y (relative to LEFT) and radius


def crt(p):
    glow = E("Ellipse", dict(x=0, y=0, width=480, height=480),
             fill(p["bg"][0], E("RadialGradient", dict(centerX=240, centerY=220, radius=260,
                                                       colors=" ".join(p["bg"]), positions="0 0.6 1"))))
    return draw(glow)


def bezel(p):
    import math
    ticks = []
    for i in range(60):
        a = math.radians(i * 6)
        major = i % 5 == 0
        r0, r1 = (214, 230) if major else (222, 230)
        ticks.append(line(240 + r0 * math.sin(a), 240 - r0 * math.cos(a),
                          240 + r1 * math.sin(a), 240 - r1 * math.cos(a),
                          p["main"] if major else p["dim"], 3 if major else 1.5))
    ring = E("Ellipse", dict(x=6, y=6, width=468, height=468), stroke(p["dim"], 2))
    spin = animate("angle", "[SECOND] * 6", duration=0.15, interpolation="LINEAR", angleDirection="CLOCKWISE")
    marker = group("sec_marker", spin, draw(rect(236, 8, 8, 18, fill(p["bright"]))),
                   draw(rect(232, 6, 16, 22, fill(p["main"])), alpha=60))
    return [draw(ring, *ticks), marker]


def header(p):
    title = text(60, 46, 360, 30, "W A S T E L A N D  //  T E R M", FONT, 22, p["main"], glow=(p["main"], 4))
    rule = draw(line(92, 84, 388, 84, p["main"], 1.5), line(92, 84, 92, 91, p["main"], 1.5),
                line(388, 84, 388, 91, p["main"], 1.5), rect(232, 81, 16, 6, fill(p["main"])))
    return [title, rule]


def clock(p):
    box = (TIME_X - 4, 86, 5 * CHAR * TIME_SIZE + 20, 136)
    digits = text(*box, [template("%02d %02d", HOUR, "[MINUTE]")], FONT, TIME_SIZE, p["bright"],
                  align="START", glow=(p["main"], 14))
    blink = animate("alpha", "[SECOND] % 2 == 0 ? 255 : 30", duration=0.12, interpolation="LINEAR")
    colon = text(*box, "  :  ", FONT, TIME_SIZE, p["bright"], align="START", glow=(p["main"], 14),
                 transforms=[blink])
    return [digits, colon]


def date_line(p):
    box = (DATE_X - 2, 220, DATE_CHARS * CHAR * DATE_SIZE + 24, 34)
    body = [E("Upper", None, template("> %s %02d.%s.%d", 'subText(icuText("EEE"), 0, 3)', "[DAY]",
                                       'subText(icuText("MMM"), 0, 3)', "[YEAR]"))]
    date = text(*box, body, FONT, DATE_SIZE, p["main"], align="START", glow=(p["main"], 5))
    blink = animate("alpha", "[SECOND] % 2 == 0 ? 255 : 0", duration=0.1, interpolation="LINEAR")
    cursor = text(*box, " " * (DATE_CHARS - 1) + "_", FONT, DATE_SIZE, p["bright"], align="START",
                  transforms=[blink])
    return [date, cursor]


def bracket_frame(x, y, w, h, color, c=12):
    pts = []
    for (cx, cy, dx, dy) in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        pts += [line(cx, cy, cx + dx * c, cy, color, 2), line(cx, cy, cx, cy + dy * c, color, 2)]
    pts.append(E("Rectangle", dict(x=x, y=y, width=w, height=h), stroke(color, 1)))
    return pts


def tag(x, y, label, p):
    """Inverted label block: filled rectangle with dark text."""
    w = len(label[0]) * CHAR * 18 + 12
    return [draw(rect(x, y, w, 18, fill(p["main"]))),
            text(x, y - 2, max(w, 70), 22, lang(*label), FONT, 18, p["dark"], align="START")]


def panels(p):
    out = [draw(*bracket_frame(*LEFT, p["main"]), *bracket_frame(*RIGHT, p["main"]), alpha=200)]
    out += tag(LEFT[0] + 6, LEFT[1] + 6, ("PULSO", "PULSE"), p)
    out += tag(RIGHT[0] + 6, RIGHT[1] + 6, ("STATUS", "STATUS"), p)

    # Pulse gauge scale (40-200 bpm across -75..75 degrees).
    import math
    gx, gy, r = LEFT[0] + GAUGE[0], LEFT[1] + GAUGE[1], GAUGE[2]
    scale = [arc(gx, gy, r, -75, 75, p["dim"], 2)]
    for i in range(11):
        a = math.radians(-75 + i * 15)
        major = i % 5 == 0
        r0 = r - (12 if major else 7)
        scale.append(line(gx + r0 * math.sin(a), gy - r0 * math.cos(a), gx + r * math.sin(a), gy - r * math.cos(a),
                          p["main"] if major else p["dim"], 2 if major else 1.5))
    scale.append(arc(gx, gy, r, 45, 75, "#FF5A3C", 3))  # high zone
    out.append(draw(*scale))
    out.append(text(gx - r - 18, gy - 10, 30, 18, "40", FONT, 16, p["dim"]))
    out.append(text(gx + r - 10, gy - 10, 30, 18, "200", FONT, 16, p["dim"]))

    # Status rows.
    rx, ry = RIGHT[0] + 8, RIGHT[1] + 28
    rows = [("STP", None), ("PWR", template("%d%%", "[BATTERY_PERCENT]")), ("SEC", template("%02d", "[SECOND]"))]
    for i, (label, value) in enumerate(rows):
        y = ry + i * 21
        out.append(text(rx, y, 60, 22, label, FONT, 22, p["dim"], align="START"))
        if value is not None:
            out.append(text(rx + 40, y, RIGHT[2] - 56, 22, [value], FONT, 24, p["bright"], align="END"))
    return out


def power_bar(p):
    out = [text(66, 356, 50, 22, "PWR", FONT, 20, p["dim"], align="START"),
           draw(line(104, 358, 104, 376, p["main"], 2), line(104, 358, 109, 358, p["main"], 2),
                line(104, 376, 109, 376, p["main"], 2), line(376, 358, 376, 376, p["main"], 2),
                line(371, 358, 376, 358, p["main"], 2), line(371, 376, 376, 376, p["main"], 2))]
    for k in range(20):
        lit = E("Transform", dict(target="alpha", value=f"[BATTERY_PERCENT] &gt;= {5 * (k + 1)} ? 255 : 45"))
        out.append(draw(rect(110 + k * 13, 361, 10, 13, fill(p["main"])), transforms=[lit]))
    out.append(text(40, 386, 400, 24, lang("> SISTEMA OPERACIONAL", "> SYSTEM ONLINE"), FONT, 20, p["dim"]))
    return out


def scanlines(p):
    lines = [line(0, y + 0.5, 480, y + 0.5, "#000000", 1) for y in range(0, 480, 3)]
    band_fill = fill(p["main"], E("LinearGradient", dict(startX=0, startY=0, endX=0, endY=60,
                                                         colors=f"#00{p['main'][1:]} #26{p['main'][1:]} #00{p['main'][1:]}",
                                                         positions="0 0.5 1")))
    band = draw(rect(0, 0, 480, 60, band_fill), box=(0, -60, 480, 60),
                transforms=[animate("y", "([SECOND] % 8) * 70 - 60", duration=1, interpolation="LINEAR"),
                            animate("alpha", "[SECOND] % 8 == 0 ? 0 : 255", duration=0.2, interpolation="LINEAR")])
    return [draw(*lines, alpha=80), band]


def palette_scene(p):
    flicker = animate("alpha", "[SECOND] % 13 == 0 ? 185 : 255", duration=0.12, interpolation="LINEAR")
    content = group(f"content_{p['id']}", flicker, *header(p), *clock(p), *date_line(p), *panels(p),
                    *power_bar(p))
    return group(f"scene_{p['id']}", crt(p), *bezel(p), content, *scanlines(p))


def pulse_slot(p_main="#FFFFFF"):
    """Heart-rate complication: needle and value. Colours follow the palette through a
    per-palette ListConfiguration inside the slot."""
    x, y, w, h = LEFT
    gx, gy, r = GAUGE

    def needle(angle_expr, color, bright):
        box = (gx - r, gy - r, 2 * r, 2 * r)
        hand = draw(line(r, r, r, 8, bright, 2.5, cap="ROUND"), line(r, r, r, r - 12, color, 4, cap="ROUND"),
                    E("Ellipse", dict(x=r - 5, y=r - 5, width=10, height=10), fill(color)),
                    box=box, transforms=[animate("angle", angle_expr, duration=0.8, interpolation="OVERSHOOT")])
        return hand

    def parts(pal, number):
        angle = f"-75 + clamp(({number} - 40) / 160, 0, 1) * 150" if number else "-75"
        return [needle(angle, pal["main"], pal["bright"])]

    def by_palette(builder, tag_name):
        # ListConfiguration is not a valid Complication child, so wrap it in a Group.
        return group(f"pulse_{tag_name}", E("ListConfiguration", dict(id="palette"),
                     *[E("ListOption", dict(id=pal["id"]), group(f"pulse_{tag_name}_{pal['id']}", *builder(pal)))
                       for pal in PALETTES]))

    value_box = (0, gy - 46, w, 30)
    numeric = 'textLength([COMPLICATION.TEXT]) &gt; 0 &amp;&amp; textLength([COMPLICATION.TEXT]) &lt;= 3 &amp;&amp; [COMPLICATION.TEXT] != "--"'
    n = text_number()

    def numeric_view(pal):
        return parts(pal, n) + [text(*value_box, [template("%s", "[COMPLICATION.TEXT]")], FONT, 34, pal["bright"],
                                     glow=(pal["main"], 6))]

    def idle_view(pal):
        return parts(pal, None) + [text(*value_box, "---", FONT, 34, pal["dim"])]

    slot = E("ComplicationSlot", dict(x=x, y=y, width=w, height=h, slotId="0", displayName="comp_hr",
                                      supportedTypes="SHORT_TEXT EMPTY"),
             E("DefaultProviderPolicy", dict(defaultSystemProvider="HEART_RATE", defaultSystemProviderType="SHORT_TEXT",
                                             primaryProvider=f"{SHEALTH}.heartrate.HeartrateComplicationProviderService",
                                             primaryProviderType="SHORT_TEXT")),
             E("BoundingBox", dict(x=0, y=0, width=w, height=h)),
             E("Variant", dict(mode="AMBIENT", target="alpha", value=0)))
    slot.append(E("Complication", dict(type="SHORT_TEXT"),
                  condition(("hr_numeric", numeric, [by_palette(numeric_view, "live")]), default=[by_palette(idle_view, "idle")])))
    slot.append(E("Complication", dict(type="EMPTY"), by_palette(idle_view, "empty")))
    return slot


def steps_slot():
    x, y = RIGHT[0] + 48, RIGHT[1] + 28
    w, h = RIGHT[2] - 64, 22

    def value(content):
        return group("steps_value", E("ListConfiguration", dict(id="palette"),
                     *[E("ListOption", dict(id=pal["id"]),
                         text(0, 0, w, h, content, FONT, 24, pal["bright"], align="END")) for pal in PALETTES]))

    has_text = 'textLength([COMPLICATION.TEXT]) &gt; 0 &amp;&amp; [COMPLICATION.TEXT] != "--"'
    txt = [template("%s", "[COMPLICATION.TEXT]")]
    slot = E("ComplicationSlot", dict(x=x, y=y, width=w, height=h, slotId="1", displayName="comp_steps",
                                      supportedTypes="GOAL_PROGRESS RANGED_VALUE SHORT_TEXT EMPTY"),
             E("DefaultProviderPolicy", dict(defaultSystemProvider="STEP_COUNT", defaultSystemProviderType="SHORT_TEXT",
                                             primaryProvider=f"{SHEALTH}.steps.StepsComplicationProviderService",
                                             primaryProviderType="GOAL_PROGRESS")),
             E("BoundingBox", dict(x=0, y=0, width=w, height=h)),
             E("Variant", dict(mode="AMBIENT", target="alpha", value=0)))
    slot.append(E("Complication", dict(type="GOAL_PROGRESS"),
                  value([template("%d", "round([COMPLICATION.GOAL_PROGRESS_VALUE])")])))
    slot.append(E("Complication", dict(type="RANGED_VALUE"),
                  condition(("has_text", has_text, [value(txt)]),
                            default=[value([template("%d", "round([COMPLICATION.RANGED_VALUE_VALUE])")])])))
    slot.append(E("Complication", dict(type="SHORT_TEXT"),
                  condition(("has_text", has_text, [value(txt)]), default=[value("--")])))
    slot.append(E("Complication", dict(type="EMPTY"), value("--")))
    return slot


def aod(p):
    # Galaxy Watch AOD offload rendered only plain PartText in testing.
    box = (TIME_X - 4, 172, 5 * CHAR * TIME_SIZE + 20, 136)
    return group(f"aod_{p['id']}",
                 text(*box, [template("%02d:%02d", HOUR, "[MINUTE]")], FONT, TIME_SIZE, p["dim"], align="START"),
                 alpha=0)


def build():
    root = E("WatchFace", dict(width=480, height=480))
    root.append(E("Metadata", dict(key="CLOCK_TYPE", value="DIGITAL")))
    root.append(E("Metadata", dict(key="PREVIEW_TIME", value="10:08:32")))
    root.append(E("UserConfigurations", None,
                  E("ListConfiguration", dict(id="palette", defaultValue="0", displayName="palette_label",
                                              screenReaderText="palette_label"),
                    *[E("ListOption", dict(id=p["id"], displayName=p["name"])) for p in PALETTES])))
    scene = E("Scene", dict(backgroundColor="#000000"))
    root.append(scene)
    scene.append(group("active_face", E("Variant", dict(mode="AMBIENT", target="alpha", value=0)),
                       E("ListConfiguration", dict(id="palette"),
                         *[E("ListOption", dict(id=p["id"]), palette_scene(p)) for p in PALETTES])))
    aods = []
    for p in PALETTES:
        g = aod(p)
        g.insert(0, E("Variant", dict(mode="AMBIENT", target="alpha", value=255)))
        aods.append(E("ListOption", dict(id=p["id"]), g))
    scene.append(E("ListConfiguration", dict(id="palette"), *aods))
    scene.append(pulse_slot())
    scene.append(steps_slot())
    return root


if __name__ == "__main__":
    import xml.etree.ElementTree as ET
    root = build()
    xml = ET.tostring(root, encoding="unicode")
    # Expressions above were written pre-escaped for readability; undo ElementTree's double escaping.
    xml = xml.replace("&amp;gt;", "&gt;").replace("&amp;lt;", "&lt;").replace("&amp;amp;", "&amp;")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('<?xml version="1.0" encoding="utf-8"?>\n' + xml, encoding="utf-8")
    print(f"wrote {OUT} ({len(xml)} bytes)")
