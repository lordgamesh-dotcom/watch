#!/usr/bin/env python3
"""Render static Galaxy Fit3 wallpapers (256 x 402) in the style of each watch face.

The Fit3 does not run Wear OS and accepts no third-party watch faces, so these are
backgrounds for its built-in photo watch face. The band draws its own clock on top,
so the upper/centre area of every image is kept calm. No live data is drawn.
Output: fit3/<name>.png. Requires Pillow.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "fit3"
W, H = 256, 402
S = 3  # supersampling factor
FONTS = {
    "audiowide": ROOT / "retrowave/src/main/res/font/audiowide.ttf",
    "vt323": ROOT / "wasteland/src/main/res/font/vt323.ttf",
    "sharetech": ROOT / "watchface/src/main/res/font/sharetechmono.ttf",
}


def rgb(h, a=255):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (a,)


def mix(c1, c2, t):
    a, b = rgb(c1), rgb(c2)
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


def canvas():
    return Image.new("RGBA", (W * S, H * S), (0, 0, 0, 255))


def layer():
    return Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))


def glow_onto(base, lay, radius, strength=1):
    blurred = lay.filter(ImageFilter.GaussianBlur(radius * S))
    for _ in range(strength):
        base.alpha_composite(blurred)
    base.alpha_composite(lay)


def vgradient(img, y0, y1, stops):
    d = ImageDraw.Draw(img)
    for y in range(int(y0 * S), int(y1 * S)):
        t = (y / S - y0) / max(y1 - y0, 1)
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if p0 <= t <= p1:
                d.line([(0, y), (W * S, y)], fill=mix(c0, c1, (t - p0) / max(p1 - p0, 1e-6)))
                break


def font(name, size):
    return ImageFont.truetype(str(FONTS[name]), int(size * S))


def finish(img, name):
    out = img.resize((W, H), Image.LANCZOS).convert("RGB")
    OUT.mkdir(exist_ok=True)
    out.save(OUT / f"{name}.png", optimize=True)
    print("wrote", OUT / f"{name}.png")


def P(*pts):
    return [(x * S, y * S) for x, y in pts]


# ------------------------------------------------------------------ Retrowave
def retrowave():
    img = canvas()
    hz, r, cx = 300, 104, W / 2
    vgradient(img, 0, hz, [(0, "#000000"), (0.55, "#05030F"), (1, "#140A2E")])
    d = ImageDraw.Draw(img)
    rnd = random.Random(11)
    for _ in range(45):
        x, y = rnd.uniform(6, W - 6), rnd.uniform(6, hz - r - 12)
        s = rnd.choice([0.6, 0.8, 1, 1.3])
        d.ellipse([(x - s) * S, (y - s) * S, (x + s) * S, (y + s) * S], fill=(255, 255, 255, rnd.choice([90, 140, 220])))

    def sun_col(y):
        t = (y - (hz - r)) / r
        return mix("#5AD7FF", "#A98CFF", t * 2) if t < 0.5 else mix("#A98CFF", "#FF6EC7", (t - 0.5) * 2)

    glow = layer()
    gd = ImageDraw.Draw(glow)
    gd.ellipse([(cx - r * 1.5) * S, (hz - r * 1.5) * S, (cx + r * 1.5) * S, (hz + r * 1.5) * S], fill=rgb("#FF4FB0", 60))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(30 * S)))

    sun = layer()
    sd = ImageDraw.Draw(sun)
    y = hz - r + 2
    while y < hz - 2:
        half = math.sqrt(max(r * r - (hz - y - 2) ** 2, 0))
        sd.line(P((cx - half, y + 2), (cx + half, y + 2)), fill=sun_col(y), width=5 * S)
        y += 8.5
    img.alpha_composite(sun)

    neon = layer()
    nd = ImageDraw.Draw(neon)
    big = [(cx - 112, hz - 112), (cx + 112, hz - 112), (cx, hz - 2)]
    small = [(cx, hz - 92), (cx + 46, hz - 6), (cx - 46, hz - 6)]
    for (a, b), col in zip(((big[0], big[1]), (big[1], big[2]), (big[2], big[0])), ("#4D6BFF", "#FF7AD1", "#FF7AD1")):
        nd.line(P(a, b), fill=rgb(col), width=3 * S)
    for a, b in ((small[0], small[1]), (small[1], small[2]), (small[2], small[0])):
        nd.line(P(a, b), fill=rgb("#FFC2EC"), width=int(2.5 * S))
    glow_onto(img, neon, 4, 2)
    hot = layer()
    hd = ImageDraw.Draw(hot)
    for tri in (big, small):
        for a, b in zip(tri, tri[1:] + tri[:1]):
            hd.line(P(a, b), fill=(255, 255, 255, 150), width=S)
    img.alpha_composite(hot)

    sil = layer()
    sd = ImageDraw.Draw(sil)
    dark = rgb("#05020A")
    sd.ellipse([(cx - 52) * S, (hz - 9) * S, (cx + 52) * S, (hz + 11) * S], fill=dark)
    sd.ellipse([(cx - 22) * S, (hz - 15) * S, (cx + 24) * S, (hz + 7) * S], fill=dark)

    def quad(p0, c, p1, n=12):
        return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
                 (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]) for t in (i / n for i in range(n + 1))]

    for bx, h, lean in ((cx - 14, 62, -16), (cx + 8, 80, 8), (cx + 26, 48, 20)):
        base = (bx, hz - 6)
        crown = (bx + lean, hz - 6 - h)
        pts = quad(base, (bx + lean * 0.1, hz - 6 - h * 0.6), crown)
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            sd.line(P(a, b), fill=dark, width=int((5 - i * 0.2) * S))
        for dx, dy, droop in ((-30, 4, 10), (-24, -12, 8), (-8, -22, 6), (10, -22, 6), (25, -12, 8),
                              (31, 4, 10), (-18, 14, 4), (18, 14, 4)):
            end = (crown[0] + dx, crown[1] + dy + droop)
            fp = quad(crown, (crown[0] + dx * 0.5, crown[1] + dy - droop * 0.6), end, 8)
            for i, (a, b) in enumerate(zip(fp, fp[1:])):
                sd.line(P(a, b), fill=dark, width=max(int((3.4 - i * 0.35) * S), S))
                if 1 <= i <= 6:
                    ln = 6 - i * 0.6
                    sgn = 1 if dx > 0 else -1
                    sd.line(P(b, (b[0] + sgn * ln * 0.6, b[1] + ln)), fill=dark, width=int(1.2 * S))
    img.alpha_composite(sil)

    vgradient(img, hz, H, [(0, "#120A2A"), (1, "#000000")])
    d = ImageDraw.Draw(img)
    refl = layer()
    rd = ImageDraw.Draw(refl)
    for k in range(10):
        yy = hz + 5 + k * 7
        src = hz - 4 - k * 8.5
        half = math.sqrt(max(r * r - (hz - src) ** 2, 0)) * (0.95 - k * 0.05)
        off = (k % 2) * 6 - 3
        col = sun_col(src)
        rd.line(P((cx - half + off, yy), (cx + half + off, yy)), fill=col[:3] + (max(40, 200 - k * 16),), width=int(2.5 * S))
    rd.line(P((cx, hz + 2), (cx - 112, hz + 112)), fill=rgb("#FF7AD1", 60), width=2 * S)
    rd.line(P((cx, hz + 2), (cx + 112, hz + 112)), fill=rgb("#FF7AD1", 60), width=2 * S)
    rnd = random.Random(5)
    for _ in range(40):
        yy = rnd.uniform(hz + 6, H - 10)
        x = rnd.uniform(10, W - 30)
        rd.line(P((x, yy), (x + rnd.uniform(6, 22), yy)), fill=rgb(rnd.choice(["#FF6EC7", "#5AD7FF", "#4D6BFF"]), 80), width=S)
    glow_onto(img, refl, 2)
    d.line(P((0, hz), (W, hz)), fill=rgb("#FF6EC7", 160), width=int(1.5 * S))
    finish(img, "retrowave")


# ------------------------------------------------------------------ Cyberpunk HUD
def cyberpunk():
    img = canvas()
    cyan, red, yellow, dim = "#19E6FF", "#FF2D4A", "#F5EB0A", "#0E4E5A"
    vgradient(img, 0, H, [(0, "#00060A"), (0.5, "#000000"), (1, "#00060A")])
    d = ImageDraw.Draw(img)
    for y in range(0, H, 3):
        d.line(P((0, y), (W, y)), fill=rgb("#19E6FF", 10), width=S)

    neon = layer()
    nd = ImageDraw.Draw(neon)
    m = 8
    # Rounded outer frame and inner hairline.
    nd.rounded_rectangle([m * S, m * S, (W - m) * S, (H - m) * S], radius=34 * S, outline=rgb(cyan, 120), width=S)
    nd.rounded_rectangle([(m + 7) * S, (m + 7) * S, (W - m - 7) * S, (H - m - 7) * S], radius=28 * S, outline=rgb(dim), width=S)
    # Corner arcs: cyan top-left / bottom-right, red top-right / bottom-left.
    for (x0, y0, a0, col) in ((m, m, 180, cyan), (W - m - 68, m, 270, red), (m, H - m - 68, 90, red), (W - m - 68, H - m - 68, 0, cyan)):
        nd.arc([x0 * S, y0 * S, (x0 + 68) * S, (y0 + 68) * S], a0, a0 + 90, fill=rgb(col), width=4 * S)
    # Edge ticks.
    for y in range(60, H - 60, 8):
        major = (y - 60) % 40 == 0
        ln = 8 if major else 4
        for x0, sgn in ((m + 1, 1), (W - m - 1, -1)):
            nd.line(P((x0, y), (x0 + sgn * ln, y)), fill=rgb(cyan if major else dim), width=S)
    # Divider with notch, crosshairs and dashes (lower third).
    yd = 272
    nd.line(P((22, yd), (98, yd), (104, yd + 6), (152, yd + 6), (158, yd), (234, yd)), fill=rgb(cyan), width=2 * S)
    for cx in (16, W - 16):
        nd.line(P((cx, yd - 6), (cx, yd + 6)), fill=rgb(cyan), width=2 * S)
        nd.line(P((cx - 6, yd), (cx + 6, yd)), fill=rgb(cyan), width=2 * S)
    x = 56
    for w in (12, 4, 24, 6, 18, 8, 22, 5, 14):
        nd.rectangle([x * S, (yd + 14) * S, (x + w) * S, (yd + 17) * S], fill=rgb(yellow))
        x += w + 8
    # Top bracket bar.
    nd.line(P((40, 40), (W - 40, 40)), fill=rgb(cyan), width=S + 1)
    nd.rectangle([(W / 2 - 8) * S, 37 * S, (W / 2 + 8) * S, 43 * S], fill=rgb(cyan))
    for x0 in (40, W - 40):
        nd.line(P((x0, 40), (x0, 47)), fill=rgb(cyan), width=S + 1)
    # Hazard stripe.
    for i in range(14):
        x0 = 72 + i * 8
        nd.polygon(P((x0 + 4, 350), (x0 + 8, 350), (x0 + 4, 357), (x0, 357)), fill=rgb(yellow))
    glow_onto(img, neon, 3, 2)

    d = ImageDraw.Draw(img)
    f = font("sharetech", 11)
    d.text((W / 2 * S, 28 * S), "S Y S : / / H U D", font=f, fill=rgb(cyan, 200), anchor="mm")
    d.text((W / 2 * S, 330 * S), "N E T   L I N K   O K", font=f, fill=rgb("#8FA3AB"), anchor="mm")
    finish(img, "cyberpunk_hud")


# ------------------------------------------------------------------ Wasteland Terminal
def wasteland():
    img = canvas()
    green, bright, dim = "#41FF7A", "#C8FFD6", "#1F8A42"
    glow = layer()
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-60 * S, 40 * S, (W + 60) * S, (H - 40) * S], fill=rgb("#0B3317"))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(40 * S)))

    neon = layer()
    nd = ImageDraw.Draw(neon)
    m = 10
    nd.rounded_rectangle([m * S, m * S, (W - m) * S, (H - m) * S], radius=30 * S, outline=rgb(dim), width=2 * S)
    # Header and rule.
    nd.line(P((30, 58), (W - 30, 58)), fill=rgb(green), width=int(1.5 * S))
    for x0 in (30, W - 30):
        nd.line(P((x0, 58), (x0, 64)), fill=rgb(green), width=int(1.5 * S))
    nd.rectangle([(W / 2 - 8) * S, 55 * S, (W / 2 + 8) * S, 61 * S], fill=rgb(green))
    # Corner brackets of the main display area.
    x0, y0, x1, y1, c = 22, 76, W - 22, 286, 14
    for (cx, cy, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        nd.line(P((cx, cy), (cx + dx * c, cy)), fill=rgb(green), width=2 * S)
        nd.line(P((cx, cy), (cx, cy + dy * c)), fill=rgb(green), width=2 * S)
    # Side rulers.
    for y in range(92, 276, 8):
        major = (y - 92) % 32 == 0
        for xx, sgn in ((x0 + 4, 1), (x1 - 4, -1)):
            nd.line(P((xx, y), (xx + sgn * (7 if major else 3), y)), fill=rgb(green if major else dim), width=S)
    # Decorative segmented bar (no live data).
    nd.line(P((30, 312), (30, 326)), fill=rgb(green), width=2 * S)
    nd.line(P((W - 30, 312), (W - 30, 326)), fill=rgb(green), width=2 * S)
    for k in range(16):
        xs = 36 + k * 11.5
        nd.rectangle([xs * S, 315 * S, (xs + 8) * S, 323 * S], fill=rgb(green, 255 if k < 12 else 60))
    glow_onto(img, neon, 3, 2)

    d = ImageDraw.Draw(img)
    d.text((W / 2 * S, 40 * S), "W A S T E L A N D", font=font("vt323", 20), fill=rgb(green), anchor="mm")
    d.text((W / 2 * S, 300 * S), "// T E R M I N A L //", font=font("vt323", 15), fill=rgb(dim), anchor="mm")
    d.text((26 * S, 346 * S), "> SISTEMA OPERACIONAL_", font=font("vt323", 17), fill=rgb(bright), anchor="lm")
    d.text((26 * S, 364 * S), "> AGUARDANDO SINAL...", font=font("vt323", 15), fill=rgb(dim), anchor="lm")

    for y in range(0, H * S, 3 * S):
        d.line([(0, y), (W * S, y)], fill=(0, 0, 0, 90), width=S)
    finish(img, "wasteland_terminal")


if __name__ == "__main__":
    retrowave()
    cyberpunk()
    wasteland()
