"""Small helpers shared by the watch face generators (Watch Face Format XML via ElementTree)."""
import xml.etree.ElementTree as ET
from pathlib import Path

PT = 'subText([LANGUAGE_LOCALE_NAME], 0, 2) == "pt"'
HOUR = "[IS_24_HOUR_MODE] ? [HOUR_0_23] : [HOUR_1_12]"
SHEALTH = "com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.complications"


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


def draw(*shapes, alpha=None, transforms=(), box=(0, 0, 480, 480)):
    a = dict(x=round(box[0]), y=round(box[1]), width=round(box[2]), height=round(box[3]))
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


def line(x1, y1, x2, y2, color, t=1, cap=None):
    s = stroke(color, t, **({"cap": cap} if cap else {}))
    return E("Line", dict(startX=num(x1), startY=num(y1), endX=num(x2), endY=num(y2)), s)


def rect(x, y, w, h, the_fill, *extra):
    return E("Rectangle", dict(x=num(x), y=num(y), width=num(w), height=num(h)), the_fill, *extra)


def arc(cx, cy, r, a0, a1, color, t, **kw):
    return E("Arc", dict(centerX=num(cx), centerY=num(cy), width=num(2 * r), height=num(2 * r),
                         startAngle=num(a0), endAngle=num(a1)), stroke(color, t, **kw))


def animate(target, value, duration=1, interpolation="EASE_IN_OUT", fps=60, **kw):
    return E("Transform", dict(target=target, value=value),
             E("Animation", dict(duration=duration, fps=fps, interpolation=interpolation, **kw)))


def template(fmt, *exprs):
    t = E("Template", text=fmt)
    for ex in exprs:
        t.append(E("Parameter", dict(expression=ex)))
    return t


def text(x, y, w, h, content, family, size, color, align="CENTER", glow=None, alpha=None, transforms=()):
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
    # Part geometry must be integers in the WFF schema.
    a = dict(x=round(x), y=round(y), width=round(w), height=round(h))
    if alpha is not None:
        a["alpha"] = alpha
    return E("PartText", a, *transforms, E("Text", dict(align=align), font))


def lang(pt, en):
    return [template("%s", f'{PT} ? "{pt}" : "{en}"')]


def condition(*cases, default=None):
    """cases: (name, expression, [children])."""
    exprs = E("Expressions")
    for name, ex, _ in cases:
        exprs.append(E("Expression", dict(name=name), text=ex))
    cond = E("Condition", None, exprs)
    for name, _, kids in cases:
        cond.append(E("Compare", dict(expression=name), *kids))
    if default:
        cond.append(E("Default", None, *default))
    return cond


def text_number(source="[COMPLICATION.TEXT]"):
    """Numeric value of a 1-3 digit text source. The Galaxy Watch runtime does not coerce
    complication text to a number, so digits are matched one by one."""
    def digit(i):
        ch = f"subText({source}, {i}, {i + 1})"
        expr = "0"
        for d in range(9, 0, -1):
            expr = f'({ch} == "{d}" ? {d} : {expr})'
        return expr
    n = f"textLength({source})"
    return (f"({n} == 3 ? {digit(0)} * 100 + {digit(1)} * 10 + {digit(2)} : "
            f"({n} == 2 ? {digit(0)} * 10 + {digit(1)} : {digit(0)}))")


def write(root, out: Path):
    xml = ET.tostring(root, encoding="unicode")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('<?xml version="1.0" encoding="utf-8"?>\n' + xml, encoding="utf-8")
    print(f"wrote {out} ({len(xml)} bytes)")
