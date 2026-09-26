#!/usr/bin/env python3
"""Anime-style Arch landscape for LingmoOS, in the layered macOS look.

Cel-shaded sky and clouds (hard-edged, two-tone), a central peak shaped like
the Arch logo lit in Arch blue, stacked hills in front, sakura petals drifting
across. Two moods: sunset (light) and night (dark). Deterministic output.
"""
import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 3840, 2160
HORIZON = 0.62

MOODS = {
    "sunset": {
        "sky": [(0.0, (38, 64, 150)), (0.35, (98, 92, 190)), (0.55, (236, 128, 168)),
                (0.72, (255, 176, 138)), (1.0, (255, 214, 160))],
        "sun": ((255, 236, 200), 0.73, 0.50, 0.085), "sun_glow": (255, 190, 150),
        "cloud_lit": (255, 222, 222), "cloud_shade": (214, 150, 190), "cloud_alpha": 255,
        "peak": ((70, 150, 220), (23, 147, 209), (24, 64, 140)), "rim": (255, 220, 200),
        "hills": [((120, 96, 190), (86, 70, 160)), ((84, 70, 170), (60, 50, 140)),
                  ((56, 48, 132), (40, 34, 104)), ((34, 30, 88), (24, 20, 64))],
        "petal": (255, 184, 206), "stars": 60,
    },
    "night": {
        "sky": [(0.0, (6, 10, 30)), (0.4, (18, 28, 76)), (0.62, (60, 48, 128)),
                (0.8, (110, 70, 150)), (1.0, (150, 96, 170))],
        "sun": ((236, 240, 255), 0.76, 0.24, 0.05), "sun_glow": (150, 170, 255),
        "cloud_lit": (110, 118, 200), "cloud_shade": (64, 64, 140), "cloud_alpha": 255,
        "peak": ((40, 110, 190), (23, 110, 180), (12, 36, 90)), "rim": (170, 200, 255),
        "hills": [((52, 48, 120), (38, 36, 96)), ((36, 34, 96), (26, 26, 76)),
                  ((24, 22, 70), (18, 16, 54)), ((14, 12, 44), (10, 8, 32))],
        "petal": (236, 170, 210), "stars": 900,
    },
}


def multi_gradient(stops, n):
    t = np.linspace(0, 1, n)
    out = np.zeros((n, 3), np.float32)
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        m = (t >= t0) & (t <= t1)
        f = ((t[m] - t0) / (t1 - t0))[:, None]
        out[m] = np.array(c0) * (1 - f) + np.array(c1) * f
    return out


def sky(m):
    col = multi_gradient(m["sky"], H)
    img = np.repeat(col[:, None, :], W, axis=1)
    # Sun / moon glow
    (sc, sx, sy, sr) = m["sun"]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot((xx - W * sx) / W, (yy - H * sy) / W)
    glow = np.exp(-(d / (sr * 2.6)) ** 2)[..., None] * 0.55
    img = img * (1 - glow) + np.array(m["sun_glow"], np.float32) * glow
    return img, (xx, yy, d)


def draw_disc(img, m, grid):
    (sc, sx, sy, sr) = m["sun"]
    _, _, d = grid
    a = np.clip((sr - d) * W / 3.0, 0, 1)[..., None]  # anti-aliased hard edge
    return img * (1 - a) + np.array(sc, np.float32) * a


def stars(img, m, rng):
    n = m["stars"]
    xs = rng.integers(0, W, n)
    ys = (rng.random(n) ** 1.8 * H * 0.55).astype(int)
    b = rng.uniform(0.3, 1.0, n)
    for x, y, v in zip(xs, ys, b):
        r = 1 if v < 0.85 else 2
        img[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1] = \
            img[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1] * (1 - v) + 255 * v
    return img


def cel_clouds(m, rng):
    """Flat two-tone clouds: a lit body with a shaded underside, hard edges."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for cx, cy, scale in ((0.18, 0.30, 1.0), (0.55, 0.20, 0.8), (0.86, 0.36, 1.1), (0.38, 0.44, 0.7)):
        body = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(body)
        base_w = W * 0.16 * scale
        for i in range(9):
            r = base_w * rng.uniform(0.18, 0.34)
            x = W * cx + rng.uniform(-0.5, 0.5) * base_w
            y = H * cy + rng.uniform(-0.12, 0.1) * base_w - (r * 0.3 if i % 2 else 0)
            dr.ellipse((x - r, y - r * 0.8, x + r, y + r * 0.8), fill=255)
        # Flat bottom, as in anime cumulus
        dr.rectangle((0, H * cy + base_w * 0.12, W, H), fill=0)
        shade = Image.new("L", (W, H), 0)
        ImageDraw.Draw(shade).rectangle((0, H * cy - base_w * 0.02, W, H), fill=255)
        shade = Image.composite(body, Image.new("L", (W, H), 0), shade)
        a = m["cloud_alpha"]
        layer.paste(Image.new("RGBA", (W, H), (*m["cloud_lit"], a)), mask=body)
        layer.paste(Image.new("RGBA", (W, H), (*m["cloud_shade"], a)), mask=shade)
    return layer.filter(ImageFilter.GaussianBlur(1.2))


def arch_peak(m):
    """Fuji-like mountain in Arch blue whose snow cap is the Arch logo:
    a sharp triangle with concave sides and the arch cut into its base."""
    cx, top, base = W * 0.5, H * 0.17, H * HORIZON + H * 0.12
    half = W * 0.36

    def flank(sign, summit, depth, width, k=1.6, p=0.72):
        pts = []
        for i in range(0, 121):
            t = i / 120
            pts.append((cx + sign * width * t ** k, summit + depth * t ** p))
        return pts

    # Mountain body
    mask = Image.new("L", (W, H), 0)
    left, right = flank(-1, top, base - top, half), flank(1, top, base - top, half)
    ImageDraw.Draw(mask).polygon(left + right[::-1], fill=255)
    top_c, mid_c, bot_c = (np.array(c, np.float32) for c in m["peak"])
    t = np.clip((np.arange(H) - top) / (base - top), 0, 1)[:, None, None]
    grad = np.where(t < 0.5, top_c * (1 - t * 2) + mid_c * t * 2, mid_c * (2 - t * 2) + bot_c * (t * 2 - 1))
    face = np.repeat(grad, W, axis=1)
    # Cel shading: lit left face, shaded right face, split along a ridge line
    ys = np.arange(H)[:, None, None]
    xs = np.arange(W)[None, :, None]
    ridge = cx + (ys - top) * 0.10
    face = np.where(xs < ridge, face * 1.10 + 8, face * 0.80)
    body = Image.fromarray(np.dstack([np.clip(face, 0, 255).astype(np.uint8), np.array(mask)]), "RGBA")

    # Snow cap = Arch logo
    cap_h = (base - top) * 0.36
    cap_w = half * (cap_h / (base - top)) ** (0.72 / 1.6) * 1.02
    cap = Image.new("L", (W, H), 0)
    dc = ImageDraw.Draw(cap)
    cl = flank(-1, top, cap_h, cap_w, k=1.6, p=0.72)
    cr = flank(1, top, cap_h, cap_w, k=1.6, p=0.72)
    dc.polygon(cl + cr[::-1], fill=255)
    nw, nh = cap_w * 0.42, cap_h * 0.34
    dc.ellipse((cx - nw, top + cap_h - nh, cx + nw, top + cap_h + nh), fill=0)
    cap = Image.composite(cap, Image.new("L", (W, H), 0), mask)
    snow = np.zeros((H, W, 4), np.uint8)
    snow[..., :3] = np.where(xs[..., 0][..., None] < ridge, 250, 212).astype(np.uint8) * np.array([1, 1, 1], np.uint8)
    snow[..., 2] = np.where(xs[..., 0] < ridge[..., 0], 255, 236)
    snow[..., 3] = np.array(cap)
    body = Image.alpha_composite(body, Image.fromarray(snow, "RGBA"))

    # Rim light along the lit flank
    rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(rim).line(left, fill=(*m["rim"], 210), width=int(H * 0.004))
    rim = rim.filter(ImageFilter.GaussianBlur(H * 0.002))
    return Image.alpha_composite(body, rim)


def torii_and_trees(m, rng):
    """Silhouettes on the nearest hill: a torii gate and a few cherry trees."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    sil = (*m["hills"][-1][1], 255)
    gx, gy, s = W * 0.80, H * 0.855, H * 0.12
    # pillars
    for dx in (-0.36, 0.36):
        d.polygon([(gx + dx * s - s * 0.035, gy), (gx + dx * s + s * 0.035, gy),
                   (gx + dx * s * 0.92 + s * 0.03, gy - s), (gx + dx * s * 0.92 - s * 0.03, gy - s)], fill=sil)
    # kasagi (curved top beam) and nuki (lower beam)
    top = [(gx - s * 0.62 + i * s * 1.24 / 40, gy - s * 1.05 - s * 0.06 * (1 - ((i - 20) / 20) ** 2)) for i in range(41)]
    d.polygon(top + [(gx + s * 0.55, gy - s * 0.93), (gx - s * 0.55, gy - s * 0.93)], fill=sil)
    d.rectangle((gx - s * 0.46, gy - s * 0.78, gx + s * 0.46, gy - s * 0.72), fill=sil)
    # cherry trees: trunk + clustered round canopy, in petal pink over the silhouette
    for tx, scale in ((0.10, 1.0), (0.18, 0.7), (0.93, 0.8)):
        x, y, r = W * tx, H * 0.86, H * 0.075 * scale
        d.line([(x, y), (x + r * 0.1, y - r * 1.6)], fill=sil, width=int(r * 0.18))
        for _ in range(9):
            ox, oy = rng.uniform(-1.1, 1.1) * r, rng.uniform(-2.4, -1.4) * r
            rr = r * rng.uniform(0.45, 0.7)
            d.ellipse((x + ox - rr, y + oy - rr, x + ox + rr, y + oy + rr), fill=(*m["petal"], 255))
        for _ in range(5):
            ox, oy = rng.uniform(-0.9, 0.9) * r, rng.uniform(-1.9, -1.4) * r
            rr = r * rng.uniform(0.35, 0.5)
            shade = tuple(int(c * 0.8) for c in m["petal"])
            d.ellipse((x + ox - rr, y + oy - rr, x + ox + rr, y + oy + rr), fill=(*shade, 255))
    return layer


def hills(m, rng):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ys = np.arange(H, dtype=np.float32)[:, None]
    for i, (top_c, bot_c) in enumerate(m["hills"]):
        base = H * (HORIZON + 0.06 + i * 0.09)
        amp = H * (0.05 - i * 0.006)
        freq, phase = rng.uniform(0.6, 1.1), rng.uniform(0, math.tau)
        x = np.linspace(0, 1, W, dtype=np.float32)
        edge = (base + amp * np.sin(freq * math.tau * x + phase)
                + amp * 0.4 * np.sin(freq * 2.7 * math.tau * x + phase * 1.3))[None, :]
        t = np.clip((ys - edge) / (H - edge + 1), 0, 1)[..., None]
        col = np.array(top_c, np.float32) * (1 - t) + np.array(bot_c, np.float32) * t
        a = np.clip(ys - edge + 0.5, 0, 1) * 255
        # soft shadow the hill casts on what's behind it
        sh = np.clip(1 - (edge - ys) / (H * 0.03), 0, 1) * (ys < edge) * 70
        hill = np.dstack([np.clip(col, 0, 255).astype(np.uint8), a.astype(np.uint8)])
        shadow = np.zeros((H, W, 4), np.uint8)
        shadow[..., 3] = sh.astype(np.uint8)
        layer = Image.alpha_composite(layer, Image.fromarray(shadow, "RGBA"))
        layer = Image.alpha_composite(layer, Image.fromarray(hill, "RGBA"))
    return layer


def petals(m, rng):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i in range(55):
        size = rng.uniform(12, 30) * (2.4 if i < 8 else 1)  # a few close-up, bigger petals
        p = Image.new("RGBA", (int(size * 2), int(size * 2)), (0, 0, 0, 0))
        d = ImageDraw.Draw(p)
        d.ellipse((size * 0.4, size * 0.7, size * 1.6, size * 1.3), fill=(*m["petal"], int(rng.uniform(150, 235))))
        d.ellipse((size * 0.9, size * 0.85, size * 1.2, size * 1.15), fill=(255, 235, 240, 120))
        p = p.rotate(rng.uniform(0, 360), resample=Image.BICUBIC, expand=True)
        if i < 8:
            p = p.filter(ImageFilter.GaussianBlur(size * 0.12))  # depth of field
        x = int(rng.uniform(-0.02, 1.0) * W)
        y = int(rng.uniform(0.25, 0.95) * H)
        layer.alpha_composite(p, (max(0, x), max(0, y)))
    return layer


def render(name):
    m = MOODS[name]
    rng = np.random.default_rng(2026)
    img, grid = sky(m)
    img = stars(img, m, rng)
    img = draw_disc(img, m, grid)
    base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    base = Image.alpha_composite(base, cel_clouds(m, rng))
    base = Image.alpha_composite(base, arch_peak(m))
    base = Image.alpha_composite(base, hills(m, rng))
    base = Image.alpha_composite(base, torii_and_trees(m, rng))
    base = Image.alpha_composite(base, petals(m, rng))
    arr = np.asarray(base.convert("RGB")).astype(np.float32)
    arr += rng.normal(0, 1.8, (H, W, 1))
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    path = f"wallpapers/lingmo-anime-{name}.jpg"
    out.save(path, quality=92, optimize=True, progressive=True)
    print(path)


if __name__ == "__main__":
    for name in sys.argv[1:] or MOODS:
        render(name)
