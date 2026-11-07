#!/usr/bin/env python3
"""Generate the Cyberpunk HUD watch face XML (watchface/src/main/res/raw/watchface.xml).

The face started as a hand-made XML (commit 90222fe). This script loads that version
from git and applies every later change on top of it, so the output is reproducible:
edit this script and re-run it instead of editing the XML by hand.
Set DEBUG=1 (or DEBUG2=1) to add on-device diagnostic text.
"""
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = str(Path(__file__).resolve().parent.parent)
PATH = "watchface/src/main/res/raw/watchface.xml"
BASE = "90222fe"
DEBUG = os.environ.get("DEBUG") == "1"

src = subprocess.run(["git", "-C", REPO, "show", f"{BASE}:{PATH}"],
                     capture_output=True, text=True, check=True).stdout
root = ET.fromstring(src)
scene = root.find("Scene")
face = scene.find("Group[@name='active_face']")

HR, STEPS, STRESS = "[CONFIGURATION.theme.2]", "[CONFIGURATION.theme.4]", "[CONFIGURATION.accent.0]"
CYAN, YELLOW, GREEN, DIM = "[CONFIGURATION.theme.0]", "[CONFIGURATION.accent.1]", "[CONFIGURATION.theme.3]", "[CONFIGURATION.accent.2]"
COLS = [(135, HR), (240, STEPS), (345, STRESS)]
CY = 332  # complication ring center


def E(tag, attrib=None, *children, text=None):
    el = ET.Element(tag, {k: str(v) for k, v in (attrib or {}).items()})
    for c in children:
        el.append(c)
    if text is not None:
        el.text = text
    return el


def stroke(color, t, **kw):
    return E("Stroke", dict(color=color, thickness=t, **kw))


def fill(color):
    return E("Fill", dict(color=color))


def draw(x, y, w, h, *shapes, alpha=None):
    a = dict(x=x, y=y, width=w, height=h)
    if alpha is not None:
        a["alpha"] = alpha
    return E("PartDraw", a, *shapes)


def line(x1, y1, x2, y2, color, t=1, **kw):
    return E("Line", dict(startX=x1, startY=y1, endX=x2, endY=y2), stroke(color, t, **kw))


def rect(x, y, w, h, color, *extra):
    return E("Rectangle", dict(x=x, y=y, width=w, height=h), fill(color), *extra)


def arc(cx, cy, d, a0, a1, color, t, *extra, **kw):
    return E("Arc", dict(centerX=cx, centerY=cy, width=d, height=d, startAngle=a0, endAngle=a1),
             stroke(color, t, **kw), *extra)


def template(fmt, *exprs):
    t = E("Template", text=fmt)
    for ex in exprs:
        t.append(E("Parameter", dict(expression=ex)))
    return t


def text(x, y, w, h, content, family="sharetechmono", size=14, color="#FFFFFF", align="CENTER",
         weight=None, spacing=None, alpha=None, wrap=None):
    """content is a plain string or a list of Template/Upper/decoration elements."""
    fa = dict(family=family, size=size, color=color)
    if weight:
        fa["weight"] = weight
    if spacing is not None:
        fa["letterSpacing"] = spacing
    font = E("Font", fa)
    if isinstance(content, str):
        font.text = content
    else:
        for c in content:
            font.append(c)
    pa = dict(x=x, y=y, width=w, height=h)
    if alpha is not None:
        pa["alpha"] = alpha
    return E("PartText", pa, E("Text", dict(align=align), font))


def condition(*cases, default=None):
    """cases: (name, expression, [children]). Returns a Condition element."""
    exprs = E("Expressions")
    for name, ex, _ in cases:
        exprs.append(E("Expression", dict(name=name), text=ex))
    cond = E("Condition", None, exprs)
    for name, _, kids in cases:
        cond.append(E("Compare", dict(expression=name), *kids))
    if default:
        cond.append(E("Default", None, *default))
    return cond


def replace(parent, old, new_list):
    i = list(parent).index(old)
    parent.remove(old)
    for k, n in enumerate(new_list):
        parent.insert(i + k, n)


def parallelogram_rows(x0, y0, w, h, skew, color):
    """Filled parallelogram leaning right, drawn with 1px horizontal lines."""
    out = []
    for r in range(h):
        off = skew * (1 - r / max(h - 1, 1))
        y = y0 + r + 0.5
        out.append(line(f"{x0 + off:.2f}", f"{y:.2f}", f"{x0 + off + w:.2f}", f"{y:.2f}", color))
    return out


# ---------------------------------------------------------------- corner arcs
ticks = face.find("BooleanConfiguration[@id='ticksRing']")
tick_draw = ticks.find("BooleanOption/PartDraw")
for a in tick_draw.findall("Arc"):
    tick_draw.remove(a)
tick_draw.set("alpha", "120")
# Tick ring turns clockwise, one full turn per minute, around the canvas center.


def spin():
    # Step once per second and let Animation tween the step at 60 fps, always clockwise.
    return E("Transform", dict(target="angle", value="[SECOND] * 6"),
             E("Animation", dict(duration=1, fps=60, interpolation="LINEAR", angleDirection="CLOCKWISE")))


# Seconds marker riding on the rotating ring: at angle 0 of the ring it points at the
# current second, with a fading trail behind it.
SEC = "[CONFIGURATION.theme.1]"
trail = []
for k, a in enumerate((140, 90, 50, 25)):
    trail.append(E("PartDraw", dict(x=0, y=0, width=480, height=480, alpha=a),
                   arc(240, 240, 460, -6 * (k + 1), -6 * k, SEC, 3)))
marker = E("PartDraw", dict(x=0, y=0, width=480, height=480),
           line(240, 3, 240, 19, SEC, 3),
           line(234, 3, 240, 9, SEC, 2), line(246, 3, 240, 9, SEC, 2))
tick_opt = ticks.find("BooleanOption")
tick_opt.remove(tick_draw)
tick_opt.append(E("Group", dict(name="tick_ring", x=0, y=0, width=480, height=480),
                  spin(), tick_draw, *trail, marker))
corner = [(301, 329, CYAN), (31, 59, "[CONFIGURATION.theme.2]"),
          (121, 149, CYAN), (211, 239, "[CONFIGURATION.theme.2]")]
glow = draw(0, 0, 480, 480, *[arc(240, 240, 444, a0, a1, c, 9) for a0, a1, c in corner], alpha=45)
arcs = draw(0, 0, 480, 480, *[arc(240, 240, 444, a0, a1, c, 4) for a0, a1, c in corner])
idx = list(face).index(ticks)
face.insert(idx + 1, glow)
face.insert(idx + 2, arcs)

# ---------------------------------------------------------------- battery header
batt_texts = [p for p in face.findall("PartText") if p.get("y") in ("55", "54")]
replace(face, batt_texts[0], [text(146, 60, 90, 22, "B A T T", size=15, color=GREEN, align="START",
                                   weight="BOLD")])
pct = text(235, 54, 100, 30, [template("%d%%", "[BATTERY_PERCENT]")], family="orbitron", size=22,
           color=GREEN, align="END", weight="BOLD")
replace(face, batt_texts[1], [pct])

# ---------------------------------------------------------------- date
date_cfg = face.find("BooleanConfiguration[@id='showDate']")
opt = date_cfg.find("BooleanOption")
for c in list(opt):
    opt.remove(c)
upper = E("Upper", None, template(
    "%s // %02d.%s.%02d",
    'subText(icuText("EEE"), 0, 3)', "[DAY]", 'subText(icuText("MMM"), 0, 3)', "[YEAR] % 100"))
opt.append(text(140, 106, 200, 26, [upper], size=17, color=CYAN, spacing=0.14))

# Date rule: shorter lines with square end caps, as in the reference.
for pd in face.findall("PartDraw"):
    lines = pd.findall("Line")
    if any(l.get("startY") == "116" and l.get("startX") == "94" for l in lines):
        for l in lines:
            if l.get("startY") == "116":
                if l.get("startX") == "94":
                    l.set("startX", "94"); l.set("endX", "146")
                else:
                    l.set("startX", "334"); l.set("endX", "386")
                l.set("startY", "119"); l.set("endY", "119")
                l.find("Stroke").set("thickness", "1.5")
        pd.append(rect(89, 116, 6, 6, CYAN))
        pd.append(rect(385, 116, 6, 6, CYAN))

# ---------------------------------------------------------------- complication tracks (layout)
layout = face.find("ListConfiguration[@id='layout']")
ring_group = layout.find("ListOption[@id='0']/Group")
for c in list(ring_group):
    ring_group.remove(c)
ring_group.append(draw(0, 0, 480, 480, *[
    E("Ellipse", dict(x=cx - 46, y=CY - 46, width=92, height=92),
      stroke(col, 1.5, dashIntervals="3 4")) for cx, col in COLS], alpha=150))
ring_group.append(draw(0, 0, 480, 480, *[arc(cx, CY, 80, 0, 360, col, 6) for cx, col in COLS], alpha=60))

bars_group = layout.find("ListOption[@id='1']/Group")
for c in list(bars_group):
    bars_group.remove(c)
bars_group.append(draw(0, 0, 480, 480, *[rect(cx - 34, 368, 68, 4, col) for cx, col in COLS], alpha=60))

# ---------------------------------------------------------------- notification alert banner
ALERT = "[CONFIGURATION.theme.2]"


def alert_banner():
    blink = E("Transform", dict(target="alpha", value="[SECOND] % 2 == 0 ? 255 : 90"),
              E("Animation", dict(duration=0.15, fps=60, interpolation="LINEAR")))
    x0, y0, w, h = 186, 421, 108, 20
    frame = draw(0, 0, 480, 480,
                 E("Rectangle", dict(x=x0, y=y0, width=w, height=h), fill("#33000000")),
                 E("Rectangle", dict(x=x0, y=y0, width=w, height=h), stroke(ALERT, 1.5)),
                 # Warning triangle with exclamation mark.
                 line(x0 + 15, y0 + 3, x0 + 7, y0 + 17, ALERT, 1.8), line(x0 + 15, y0 + 3, x0 + 23, y0 + 17, ALERT, 1.8),
                 line(x0 + 6.5, y0 + 17, x0 + 23.5, y0 + 17, ALERT, 1.8),
                 rect(x0 + 14, y0 + 7, 2, 5, ALERT), rect(x0 + 14, y0 + 13.5, 2, 2, ALERT),
                 # Corner notches for the HUD look.
                 line(x0 - 6, y0 + h / 2, x0 - 1, y0 + h / 2, ALERT, 1.5),
                 line(x0 + w + 1, y0 + h / 2, x0 + w + 6, y0 + h / 2, ALERT, 1.5))
    frame.insert(0, blink)
    glow = draw(0, 0, 480, 480, E("Rectangle", dict(x=x0, y=y0, width=w, height=h), stroke(ALERT, 6)))
    glow.set("alpha", "60")
    count = text(x0 + 26, y0 - 1, w - 30, h + 2, [template("%02d MSG", "[UNREAD_NOTIFICATION_COUNT]")],
                 size=16, color=ALERT, weight="BOLD")
    count.insert(0, E("Transform", dict(target="alpha", value="[SECOND] % 2 == 0 ? 255 : 90"),
                      E("Animation", dict(duration=0.15, fps=60, interpolation="LINEAR"))))
    return [glow, frame, count]


# ---------------------------------------------------------------- icons, labels, sub-labels, hazard
for p in list(face.findall("PartText")):
    y = p.get("y")
    if y in ("298", "378", "402"):
        face.remove(p)

for pd in list(face.findall("PartDraw")):
    if any(s.get("thickness") == "5" and s.get("color") == YELLOW for s in pd.iter("Stroke")):
        hazard = [l for i in range(13) for l in parallelogram_rows(189 + i * 8, 428, 4, 6, 4, YELLOW)]
        # With unread notifications the hazard stripe turns into a blinking alert banner.
        replace(face, pd, [condition(("unread", "[UNREAD_NOTIFICATION_COUNT] &gt; 0", alert_banner()),
                                     default=[draw(0, 0, 480, 480, *hazard)])])

icons = [
    text(115, 298, 40, 26, "♥", size=20, color=HR),
    draw(0, 0, 480, 480,
         *[line(229 + i * 7, 305, 234 + i * 7, 310.5, STEPS, 2) for i in range(3)],
         *[line(234 + i * 7, 310.5, 229 + i * 7, 316, STEPS, 2) for i in range(3)]),
    draw(0, 0, 480, 480,
         line(345, 302, 336, 318, STRESS, 2), line(345, 302, 354, 318, STRESS, 2),
         line(335.5, 318, 354.5, 318, STRESS, 2),
         rect(344, 307, 2, 6, STRESS), rect(344, 314.5, 2, 2, STRESS)),
]
labels = [text(cx - 55, 380, 110, 22, name, size=15, color=col, weight="BOLD")
          for (cx, col), name in zip(COLS, ["B P M", "P A S S O S", "S T R E S S"])]
rest = text(85, 400, 100, 20, [template("%s", 'subText([LANGUAGE_LOCALE_NAME], 0, 2) == "pt" ? "REPOUSO" : "RESTING"')],
            size=13, color=DIM, spacing=0.08)
if DEBUG:
    face.append(text(140, 440, 200, 20, [template("%s|%s", "[LANGUAGE_CODE]", "[LANGUAGE_LOCALE_NAME]")], size=13))
for el in icons + labels + [rest]:
    face.append(el)

# ---------------------------------------------------------------- scanlines on by default
for b in root.iter("BooleanConfiguration"):
    if b.get("id") == "scanlines" and b.get("defaultValue"):
        b.set("defaultValue", "TRUE")

# ---------------------------------------------------------------- complication slots
SLOT = 92
RING = dict(cx=46, cy=46, d=80)


def value_text(content, size):
    return text(0, 32, SLOT, 34, content, family="orbitron", size=size, weight="BOLD")


def sub_text(content):
    # Rendered below the label row, outside the tap area.
    return text(-4, 114, SLOT + 8, 20, content, size=13, color=DIM, spacing=0.08)


def progress(fraction_expr, color):
    """Continuous ring (rings layout) or bar (bars layout) for a 0..1 fraction."""
    ring = draw(0, 0, SLOT, SLOT, arc(RING["cx"], RING["cy"], RING["d"], 0, 0, color, 6,
                                      E("Transform", dict(target="endAngle",
                                                          value=f"clamp({fraction_expr}, 0, 1) * 360"))))
    bar = draw(0, 0, SLOT, 100, rect(12, 82, 0, 4, color,
                                     E("Transform", dict(target="width",
                                                         value=f"clamp({fraction_expr}, 0, 1) * 68"))))
    return condition(("layout_rings", '[CONFIGURATION.layout] == "0"', [ring]),
                     ("layout_bars", '[CONFIGURATION.layout] == "1"', [bar]))


def text_number():
    """[COMPLICATION.TEXT] is not coerced to a number on device, so parse up to 3 digits."""
    def digit(i):
        ch = f"subText([COMPLICATION.TEXT], {i}, {i + 1})"
        expr = "0"
        for d in range(9, 0, -1):
            expr = f'({ch} == "{d}" ? {d} : {expr})'
        return expr
    n = "textLength([COMPLICATION.TEXT])"
    return (f"({n} == 3 ? {digit(0)} * 100 + {digit(1)} * 10 + {digit(2)} : "
            f"({n} == 2 ? {digit(0)} * 10 + {digit(1)} : {digit(0)}))")


def numeric_text(max_value):
    return f"{text_number()} / {max_value}"


def is_number():
    return "textLength([COMPLICATION.TEXT]) &gt; 0 &amp;&amp; textLength([COMPLICATION.TEXT]) &lt;= 3 &amp;&amp; [COMPLICATION.TEXT] != \"--\""


def stress_level():
    v = text_number()
    pt = 'subText([LANGUAGE_LOCALE_NAME], 0, 2) == "pt"'
    return (f'{v} &lt;= 25 ? ({pt} ? "BAIXO" : "LOW") : ({v} &lt;= 50 ? "NORMAL" : '
            f'({v} &lt;= 75 ? ({pt} ? "MÉDIO" : "MEDIUM") : ({pt} ? "ALTO" : "HIGH")))')


DASH = value_text("--", 26)

SAMSUNG = "com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.complications"
slots_spec = {
    "0": dict(color=HR, max=180, size=28, primary=(f"{SAMSUNG}.heartrate.HeartrateComplicationProviderService", "SHORT_TEXT"),
              system=("HEART_RATE", "SHORT_TEXT"), types="SHORT_TEXT RANGED_VALUE EMPTY"),
    "1": dict(color=STEPS, max=10000, size=22, primary=(f"{SAMSUNG}.steps.StepsComplicationProviderService", "GOAL_PROGRESS"),
              system=("STEP_COUNT", "SHORT_TEXT"), types="GOAL_PROGRESS RANGED_VALUE SHORT_TEXT EMPTY"),
    "2": dict(color=STRESS, max=100, size=28, primary=(f"{SAMSUNG}.stress.StressComplicationProviderService", "SHORT_TEXT"),
              system=("EMPTY", "EMPTY"), types="SHORT_TEXT RANGED_VALUE EMPTY"),
}

for slot in scene.findall("ComplicationSlot"):
    sid = slot.get("slotId")
    spec = slots_spec[sid]
    cx = COLS[int(sid)][0]
    for c in list(slot):
        slot.remove(c)
    slot.set("x", cx - SLOT // 2); slot.set("y", CY - SLOT // 2)
    slot.set("width", SLOT); slot.set("height", 136)
    slot.set("supportedTypes", spec["types"])
    for k in ("x", "y", "width", "height"):
        slot.set(k, str(slot.get(k)))
    pol = dict(defaultSystemProvider=spec["system"][0], defaultSystemProviderType=spec["system"][1],
               primaryProvider=spec["primary"][0], primaryProviderType=spec["primary"][1])
    slot.append(E("DefaultProviderPolicy", pol))
    slot.append(E("BoundingBox", dict(x=0, y=0, width=SLOT, height=136)))
    slot.append(E("Variant", dict(mode="AMBIENT", target="alpha", value=0)))

    txt = [template("%s", "[COMPLICATION.TEXT]")]
    short_kids = []
    if sid == "1":
        short_kids.append(value_text(txt, spec["size"]))
    else:
        numeric_kids = [progress(numeric_text(spec["max"]), spec["color"]), value_text(txt, spec["size"])]
        if sid == "2":
            numeric_kids.append(sub_text([template("%s", stress_level())]))
        short_kids.append(condition(("is_number", is_number(), numeric_kids), default=[DASH]))
    if os.environ.get("DEBUG2") == "1" and sid == "0":
        short_kids.append(text(-20, 64, SLOT + 40, 16, [template("%s|%s|%s", "[COMPLICATION.TEXT] / 180", "[COMPLICATION.TEXT] * 1", "clamp([COMPLICATION.TEXT] / 180, 0, 1) * 360")], size=11))
    if DEBUG:
        short_kids = [text(0, 60, SLOT, 20, [template("[%s|%s]", "[COMPLICATION.TEXT]", "textLength([COMPLICATION.TEXT])")], size=13)]
    slot.append(E("Complication", dict(type="SHORT_TEXT"), *short_kids))

    rv = "([COMPLICATION.RANGED_VALUE_VALUE] - [COMPLICATION.RANGED_VALUE_MIN]) / ([COMPLICATION.RANGED_VALUE_MAX] - [COMPLICATION.RANGED_VALUE_MIN])"
    has_text = "textLength([COMPLICATION.TEXT]) &gt; 0 &amp;&amp; [COMPLICATION.TEXT] != \"--\""
    ranged = E("Complication", dict(type="RANGED_VALUE"),
               progress(rv, spec["color"]),
               condition(("has_text", has_text, [value_text(txt, spec["size"])]),
                         default=[value_text([template("%d", "round([COMPLICATION.RANGED_VALUE_VALUE])")],
                                             spec["size"])]))
    if sid == "1":
        ranged.append(condition(
            ("goal_scale", "[COMPLICATION.RANGED_VALUE_MAX] &gt; 100",
             [sub_text([template("/%d", "round([COMPLICATION.RANGED_VALUE_MAX])")])]),
            default=[sub_text([template("%d%%", "round(" + rv + " * 100)")])]))
    if DEBUG:
        ranged.append(text(-20, 62, SLOT + 40, 16, [template("%s/%s/%s", "[COMPLICATION.TEXT]", "[COMPLICATION.TITLE]", "[COMPLICATION.RANGED_VALUE_VALUE]")], size=12))
    slot.append(ranged)

    if sid == "1":
        gp = "[COMPLICATION.GOAL_PROGRESS_VALUE] / [COMPLICATION.GOAL_PROGRESS_TARGET_VALUE]"
        slot.append(E("Complication", dict(type="GOAL_PROGRESS"),
                      progress(gp, spec["color"]),
                      value_text([template("%d", "round([COMPLICATION.GOAL_PROGRESS_VALUE])")], spec["size"]),
                      sub_text([template("/%d", "round([COMPLICATION.GOAL_PROGRESS_TARGET_VALUE])")]),
                      *([text(0, 62, SLOT, 16, "GP", size=12)] if DEBUG else [])))
    slot.append(E("Complication", dict(type="EMPTY"), value_text("..", 26) if DEBUG else DASH))

# ---------------------------------------------------------------- AOD: outlined digits
HOUR = {"0": "[IS_24_HOUR_MODE] ? [HOUR_0_23] : [HOUR_1_12]", "1": "[HOUR_0_23]", "2": "[HOUR_1_12]"}
aod = scene.find("ListConfiguration[@id='aodStyle']")
for grp in aod.iter("Group"):
    if not grp.get("name", "").startswith("aod_clock_"):
        continue
    fmt_id = grp.get("name")[-1]
    clock = grp.find("DigitalClock")
    y, h = int(clock.get("y")), int(clock.get("height"))
    size = clock.find("TimeText/Font").get("size")
    # Galaxy Watch AOD offload draws neither Outline nor DigitalClock, so the outline is
    # simulated: cyan copies shifted by 2px, then a black copy on top.
    def copy(dx, dy, color):
        return text(30 + dx, y + dy, 420, h, [template("%02d:%02d", HOUR[fmt_id], "[MINUTE]")],
                    family="orbitron", size=size, color=color, weight="BOLD")
    offsets = [(2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    replace(grp, clock, [copy(dx, dy, CYAN) for dx, dy in offsets] + [copy(0, 0, "#000000")])
# Show AOD content through a Variant on each top-level group (verified on device);
# drop the per-part alpha/Variant pairs.
for opt in aod.findall("ListOption"):
    grp = opt.find("Group")
    grp.set("alpha", "0")
    grp.insert(0, E("Variant", dict(mode="AMBIENT", target="alpha", value=255)))
for p in aod.iter("PartText"):
    v = p.find("Variant")
    if v is not None:
        p.remove(v)
        p.attrib.pop("alpha", None)

out = ET.tostring(root, encoding="unicode")
# ElementTree escapes &, <, > in text; the helpers above wrote them pre-escaped for readability.
out = out.replace("&amp;gt;", "&gt;").replace("&amp;lt;", "&lt;").replace("&amp;amp;", "&amp;")
with open(f"{REPO}/{PATH}", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="utf-8"?>\n' + out)
print("written", len(out))
