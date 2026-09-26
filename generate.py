#!/usr/bin/env python3
"""Generates the ArchLingmo wallpapers (light and dark) into source/ (brand.py adds the logo).

Soft blurred colour fields in the Lingmo blue palette, a few translucent
ribbons and one sweeping arc. Deterministic: same seed, same image.
"""
import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 3840, 2160
SEED = 2026

PALETTES = {
    "light": {
        "top": (174, 208, 252), "bottom": (86, 139, 235),
        "blobs": [(90, 140, 240), (120, 190, 255), (70, 110, 225), (165, 205, 255), (255, 255, 255)],
        "ribbon": (255, 255, 255), "ribbon_alpha": 70, "glow": (255, 255, 255), "glow_alpha": 110, "arc": (255, 255, 255), "arc_alpha": 150,
    },
    "dark": {
        "top": (22, 30, 58), "bottom": (10, 14, 30),
        "blobs": [(45, 85, 190), (30, 60, 150), (70, 120, 230), (25, 40, 95), (100, 150, 255)],
        "ribbon": (120, 170, 255), "ribbon_alpha": 45, "glow": (90, 140, 255), "glow_alpha": 70, "arc": (150, 190, 255), "arc_alpha": 120,
    },
}


def vertical_gradient(top, bottom):
    t = np.linspace(0.0, 1.0, H)[:, None, None]
    top, bottom = np.array(top, float), np.array(bottom, float)
    grad = top * (1 - t) + bottom * t
    return np.repeat(grad, W, axis=1)


def blob_layer(rng, colors):
    # Large soft colour fields, rendered small then blurred and upscaled
    sw, sh = W // 8, H // 8
    layer = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for i in range(14):
        c = colors[i % len(colors)]
        r = rng.uniform(0.10, 0.30) * sw
        aspect = rng.uniform(0.5, 1.1)
        x, y = rng.uniform(-0.05, 1.05) * sw, rng.uniform(0.0, 1.1) * sh
        draw.ellipse((x - r, y - r * aspect, x + r, y + r * aspect), fill=(*c, int(rng.uniform(80, 160))))
    layer = layer.filter(ImageFilter.GaussianBlur(sw * 0.06))
    return layer.resize((W, H), Image.LANCZOS)


def ribbon_layer(rng, color, alpha):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    # Two nearly parallel ribbons sharing one wave, like a single piece of silk
    amp, base = 0.11 * H, 0.62 * H
    freq, phase = 0.75, rng.uniform(0, math.tau)
    for k, (offset, thick, a) in enumerate(((0.0, 0.10, 1.0), (0.07, 0.05, 0.6))):
        pts_top, pts_bot = [], []
        for xi in range(0, W + 1, 16):
            t = xi / W
            y = base + offset * H + amp * math.sin(freq * math.tau * t + phase + k * 0.35)
            pts_top.append((xi, y))
            pts_bot.append((xi, y + thick * H * (0.55 + 0.45 * math.sin(math.tau * t + 1.3))))
        draw.polygon(pts_top + pts_bot[::-1], fill=(*color, int(alpha * a)))
    return layer.filter(ImageFilter.GaussianBlur(H * 0.012))


def arc_layer(color, alpha):
    # One thin sweeping arc across the frame, a quiet nod to the Arch logo curve
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for (cx, cy, r, start, end, scale) in ((W * 1.02, H * 1.18, H * 0.78, 185, 262, 1.0),
                                            (W * 1.02, H * 1.18, H * 0.86, 190, 250, 0.45)):
        for width, a in ((int(H * 0.014), alpha // 5), (int(H * 0.0035), alpha)):
            draw.arc((cx - r, cy - r, cx + r, cy + r), start, end,
                     fill=(*color, int(a * scale)), width=width)
    return layer.filter(ImageFilter.GaussianBlur(H * 0.0015))


def glow_layer(color, alpha):
    # Soft light falling from the top-left corner
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot((xx - W * 0.18) / W, (yy + H * 0.1) / H)
    a = np.clip(1.0 - d / 0.75, 0, 1) ** 2 * alpha
    layer = np.zeros((H, W, 4), np.uint8)
    layer[..., :3] = color
    layer[..., 3] = a.astype(np.uint8)
    return Image.fromarray(layer, "RGBA")


def grain(img, rng, strength=3.0):
    # Fine noise avoids banding in the smooth gradients
    arr = np.asarray(img).astype(np.float32)
    arr += rng.normal(0, strength, arr.shape[:2])[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def render(name, pal):
    rng = np.random.default_rng(SEED)
    base = Image.fromarray(vertical_gradient(pal["top"], pal["bottom"]).astype(np.uint8), "RGB").convert("RGBA")
    base = Image.alpha_composite(base, blob_layer(rng, pal["blobs"]))
    base = Image.alpha_composite(base, glow_layer(pal["glow"], pal["glow_alpha"]))
    base = Image.alpha_composite(base, ribbon_layer(rng, pal["ribbon"], pal["ribbon_alpha"]))
    base = Image.alpha_composite(base, arc_layer(pal["arc"], pal["arc_alpha"]))
    img = grain(base.convert("RGB"), rng)
    out = f"source/archlingmo-{name}.jpg"
    img.save(out, quality=92, optimize=True, progressive=True)
    print(out)


if __name__ == "__main__":
    for name in sys.argv[1:] or PALETTES:
        render(name, PALETTES[name])
