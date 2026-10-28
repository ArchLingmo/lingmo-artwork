#!/usr/bin/env python3
"""Generates the Axo wallpapers into source/ (brand.py adds the logo).

Axo, the ArchLingmo mascot (brand/axo), sits on the right third so desktop
icons and the dock stay clear. Backgrounds reuse the generate.py fields.
Deterministic: same seed, same image.
"""
import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from generate import H, W, blob_layer, glow_layer, grain, ribbon_layer, vertical_gradient

AXO = "brand/axo"

SCENES = {
    "noite": {
        "top": (14, 20, 48), "bottom": (6, 9, 24),
        "blobs": [(40, 80, 190), (25, 50, 140), (80, 60, 200), (20, 35, 90), (60, 130, 240)],
        "glow": (70, 120, 255), "glow_alpha": 60,
        "stars": 260, "halo": [(0, 190, 255), (170, 60, 255)],
        "axo": "03_3d/axo_3d_2048.png", "size": 0.50, "x": 0.76,
    },
    "dia": {
        "top": (196, 224, 255), "bottom": (120, 168, 245),
        "blobs": [(120, 175, 255), (160, 210, 255), (255, 255, 255), (110, 150, 240), (200, 225, 255)],
        "glow": (255, 255, 255), "glow_alpha": 120,
        "ribbon": (255, 255, 255), "ribbon_alpha": 60,
        "halo": [(255, 255, 255), (120, 200, 255)],
        "axo": "01_classic/axo_classic_2048.png", "size": 0.50, "x": 0.76,
    },
    "ia": {
        "top": (10, 16, 40), "bottom": (8, 6, 28),
        "blobs": [(30, 70, 180), (90, 40, 190), (20, 120, 220), (25, 30, 80), (60, 90, 230)],
        "glow": (60, 150, 255), "glow_alpha": 50,
        "grid": (80, 170, 255), "halo": [(0, 200, 255), (120, 80, 255)],
        "axo": "04_ai/axo_ai_2048.png", "size": 0.54, "x": 0.74,
    },
    "sonho": {
        "top": (30, 22, 70), "bottom": (12, 10, 34),
        "blobs": [(90, 60, 190), (60, 40, 150), (140, 80, 210), (30, 25, 80), (70, 100, 230)],
        "glow": (150, 110, 255), "glow_alpha": 50,
        "stars": 320, "moon": True, "hill": (18, 16, 48), "halo": [(120, 160, 255), (190, 100, 255)],
        "axo": "02_expressions/axo_dormindo_fonte.png", "size": 0.40, "x": 0.75, "ground": 0.86,
    },
}


def stars(rng, count):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for _ in range(count):
        x, y = rng.uniform(0, W), rng.uniform(0, H) * rng.uniform(0.3, 1.0)
        r = rng.choice([1.5, 2, 2.5, 3.5], p=[0.45, 0.3, 0.17, 0.08])
        a = int(rng.uniform(70, 230))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(235, 240, 255, a))
    soft = layer.filter(ImageFilter.GaussianBlur(3))
    return Image.alpha_composite(soft, layer)


def moon():
    cx, cy, r = W * 0.60, H * 0.24, H * 0.075
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    glow = np.zeros((H, W, 4), np.uint8)
    glow[..., :3] = (190, 180, 255)
    glow[..., 3] = (np.clip(1.0 - np.hypot(xx - cx, yy - cy) / (r * 4), 0, 1) ** 2.5 * 70).astype(np.uint8)
    layer = Image.fromarray(glow, "RGBA")
    disc = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(disc)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(250, 244, 225, 255))
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(250, 244, 225, 255))
    # crescent: cut with an offset disc
    draw.ellipse((cx - r * 0.55, cy - r * 1.15, cx + r * 1.45, cy + r * 0.85), fill=(0, 0, 0, 0))
    return Image.alpha_composite(layer, disc.filter(ImageFilter.GaussianBlur(1.2)))


def hill(color, top):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    pts = [(x, H * top + H * 0.05 * math.sin(x / W * math.pi * 1.4 + 0.6)) for x in range(0, W + 1, 16)]
    draw.polygon(pts + [(W, H), (0, H)], fill=(*color, 255))
    return layer.filter(ImageFilter.GaussianBlur(2))


def grid(color):
    # Faint perspective grid on the floor plus a few circuit traces
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    horizon, vx = H * 0.62, W * 0.74
    for i in range(-24, 25):
        draw.line((vx, horizon, vx + i * W * 0.09, H), fill=(*color, 34), width=3)
    y, step = horizon, H * 0.012
    while y < H:
        draw.line((0, y, W, y), fill=(*color, int(18 + 30 * (y - horizon) / (H - horizon))), width=3)
        step *= 1.32
        y += step
    fade = Image.linear_gradient("L").resize((W, H))
    layer.putalpha(Image.fromarray((np.asarray(layer.getchannel("A")) * np.clip((np.asarray(fade) / 255.0 - 0.55) * 3, 0, 1)).astype(np.uint8)))
    return layer.filter(ImageFilter.GaussianBlur(1.5))


def halo(cx, cy, r, colors):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot(xx - cx, yy - cy) / r
    a = np.clip(1.0 - d, 0, 1) ** 2.2
    t = np.clip((xx - (cx - r)) / (2 * r), 0, 1)[..., None]
    rgb = np.array(colors[0], np.float32) * (1 - t) + np.array(colors[1], np.float32) * t
    layer = np.zeros((H, W, 4), np.uint8)
    layer[..., :3] = rgb.astype(np.uint8)
    layer[..., 3] = (a * 120).astype(np.uint8)
    return Image.fromarray(layer, "RGBA")


def mascot(path, height):
    img = Image.open(f"{AXO}/{path}").convert("RGBA")
    img = img.crop(img.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox())
    img = img.resize((round(img.width * height / img.height), height), Image.LANCZOS)
    # the art is upscaled from a small sheet: a light unsharp mask restores the edges
    rgb = img.convert("RGB").filter(ImageFilter.UnsharpMask(radius=2.2, percent=60, threshold=2))
    rgb.putalpha(img.getchannel("A"))
    return rgb


def shadow(axo, pos):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    cx, by = pos[0] + axo.width / 2, pos[1] + axo.height
    w, h = axo.width * 0.42, axo.height * 0.045
    draw.ellipse((cx - w, by - h, cx + w, by + h), fill=(0, 0, 20, 110))
    return layer.filter(ImageFilter.GaussianBlur(h * 0.9))


def render(name, sc):
    rng = np.random.default_rng(2026)
    base = Image.fromarray(vertical_gradient(sc["top"], sc["bottom"]).astype(np.uint8), "RGB").convert("RGBA")
    base = Image.alpha_composite(base, blob_layer(rng, sc["blobs"]))
    base = Image.alpha_composite(base, glow_layer(sc["glow"], sc["glow_alpha"]))
    if "stars" in sc:
        base = Image.alpha_composite(base, stars(rng, sc["stars"]))
    if sc.get("moon"):
        base = Image.alpha_composite(base, moon())
    if "ribbon" in sc:
        base = Image.alpha_composite(base, ribbon_layer(rng, sc["ribbon"], sc["ribbon_alpha"]))
    if "grid" in sc:
        base = Image.alpha_composite(base, grid(sc["grid"]))

    axo = mascot(sc["axo"], round(H * sc["size"]))
    ground = sc.get("ground", 0.84)
    pos = (round(W * sc["x"] - axo.width / 2), round(H * ground - axo.height))
    base = Image.alpha_composite(base, halo(pos[0] + axo.width / 2, pos[1] + axo.height * 0.48,
                                            axo.height * 0.85, sc["halo"]))
    if "hill" in sc:
        base = Image.alpha_composite(base, hill(sc["hill"], ground - 0.035))
    base = Image.alpha_composite(base, shadow(axo, pos))
    base.alpha_composite(axo, pos)

    img = grain(base.convert("RGB"), rng, 2.5)
    out = f"source/axo-{name}.jpg"
    img.save(out, quality=93, optimize=True, progressive=True)
    print(out)


if __name__ == "__main__":
    for name in sys.argv[1:] or SCENES:
        render(name, SCENES[name])
