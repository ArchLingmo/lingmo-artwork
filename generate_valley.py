#!/usr/bin/env python3
"""Layered mountain-valley wallpapers for LingmoOS (macOS Monterey-like style).

Ridges come down from both sides into a V-shaped valley; distant layers are
lighter and hazier (atmospheric perspective), near ones dark; heavy film grain.
Anime/Arch touches: a hazy Arch-logo peak at the far end of the valley, a few
sakura petals, a thin moon at night. Deterministic output into wallpapers/.
"""
import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 3840, 2160
LAYERS = 9

PALETTES = {
    # sky top, sky horizon, far haze, near colour, deepest colour, petal
    "sunset": {
        "sky": ((236, 178, 140), (240, 196, 128)), "haze": (228, 150, 120),
        "mid": (140, 50, 110), "near": (40, 14, 60), "deep": (10, 6, 18),
        "peak": (226, 140, 130), "petal": (255, 196, 210), "moon": None,
    },
    "arch": {
        "sky": ((150, 214, 246), (206, 236, 250)), "haze": (120, 190, 232),
        "mid": (23, 120, 190), "near": (14, 44, 110), "deep": (6, 12, 34),
        "peak": (110, 180, 228), "petal": (255, 200, 222), "moon": None,
    },
    "night": {
        "sky": ((16, 20, 56), (70, 56, 120)), "haze": (80, 64, 140),
        "mid": (46, 36, 110), "near": (18, 14, 52), "deep": (5, 4, 14),
        "peak": (96, 86, 170), "petal": (220, 160, 210), "moon": (236, 236, 255),
    },
}


def lerp(a, b, t):
    return np.array(a, np.float32) * (1 - t) + np.array(b, np.float32) * t


def ridge_noise(x, rng, octaves=6):
    """Fractal sum of sines: jagged mountain ridge detail."""
    out = np.zeros_like(x)
    amp, freq = 1.0, rng.uniform(1.5, 2.5)
    for _ in range(octaves):
        out += amp * np.sin(freq * math.tau * x + rng.uniform(0, math.tau))
        amp *= 0.5
        freq *= rng.uniform(1.8, 2.3)
    return out


def layer_edge(i, rng):
    """Height of the ridge line for layer i (0 = farthest) across the width.

    Each layer is defined by its valley floor and how high it climbs at the
    left and right edges; near layers sit lower and lean to one side, so they
    frame the scene instead of closing it off.
    """
    x = np.linspace(0, 1, W, dtype=np.float32)
    depth = i / (LAYERS - 1)
    vx = 0.5 + rng.uniform(-0.08, 0.08)
    floor = 0.50 + depth * 0.46                        # valley bottom (fraction of H)
    rise = 0.20 + depth * 0.10                         # how far the sides climb above the floor
    lean = 0.35 if i % 2 else -0.35                    # alternate the high side
    left_top = floor - rise * (1 + lean) * rng.uniform(0.8, 1.2)
    right_top = floor - rise * (1 - lean) * rng.uniform(0.8, 1.2)
    side_top = np.where(x < vx, left_top, right_top)
    s = np.where(x < vx, (vx - x) / vx, (x - vx) / (1 - vx))
    shape = s ** 1.15 * (3 - 2 * s) / 2 + s * 0.5      # soft start, steady slope
    y = floor + (side_top - floor) * np.clip(shape, 0, 1)
    y += ridge_noise(x, rng) * (0.008 + 0.014 * depth)
    return y * H


def render(name, pal):
    rng = np.random.default_rng(1792)  # Arch blue #1793D1, loosely
    ys = np.arange(H, dtype=np.float32)[:, None]

    # Sky
    t = (ys / (H * 0.6)).clip(0, 1)[..., None]
    img = lerp(pal["sky"][0], pal["sky"][1], t) * np.ones((1, W, 1), np.float32)
    # soft glow down the valley
    xs = np.arange(W, dtype=np.float32)[None, :]
    g = np.exp(-(((xs - W * 0.54) / (W * 0.22)) ** 2 + ((ys - H * 0.45) / (H * 0.35)) ** 2))
    img = img * (1 - g[..., None] * 0.35) + np.array(pal["haze"], np.float32) * g[..., None] * 0.35

    if pal["moon"]:
        # thin crescent up on the right
        mx, my, mr = W * 0.74, H * 0.16, H * 0.045
        d1 = np.hypot(xs - mx, ys - my)
        d2 = np.hypot(xs - mx - mr * 0.35, ys - my + mr * 0.15)
        a = (np.clip(mr - d1, 0, 1) * np.clip(d2 - mr * 0.92, 0, 1))[..., None]
        img = img * (1 - a) + np.array(pal["moon"], np.float32) * a
        star_rng = np.random.default_rng(5)
        for _ in range(500):
            sx, sy = star_rng.integers(0, W), int(star_rng.random() ** 2 * H * 0.5)
            img[sy, sx] = img[sy, sx] * 0.3 + 255 * 0.7

    # Far peak shaped like the Arch logo, sitting in the haze at the valley end
    peak = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(peak)
    cx, top, base, half = W * 0.52, H * 0.14, H * 0.60, W * 0.20
    left = [(cx - half * (i / 100) ** 1.15, top + (base - top) * (i / 100) ** 0.92) for i in range(101)]
    right = [(cx + half * (i / 100) ** 1.15, top + (base - top) * (i / 100) ** 0.92) for i in range(101)]
    dr.polygon(left + right[::-1], fill=255)
    nw, nh = half * 0.36, (base - top) * 0.22
    dr.ellipse((cx - nw, base - nh, cx + nw, base + nh), fill=0)
    peak = np.asarray(peak.filter(ImageFilter.GaussianBlur(3)), np.float32)[..., None] / 255 * 0.7
    ptone = lerp(pal["peak"], pal["sky"][1], (ys / H)[..., None] * 0.6)
    img = img * (1 - peak) + ptone * peak

    # Ridge layers, far to near
    for i in range(LAYERS):
        depth = i / (LAYERS - 1)
        edge = layer_edge(i, rng)[None, :]
        # colour by depth: haze -> mid -> near -> deep
        if depth < 0.5:
            base_c = lerp(pal["haze"], pal["mid"], depth / 0.5)
        elif depth < 0.9:
            base_c = lerp(pal["mid"], pal["near"], (depth - 0.5) / 0.4)
        else:
            base_c = lerp(pal["near"], pal["deep"], (depth - 0.9) / 0.1)
        below = np.clip((ys - edge) / (H * (0.25 + depth * 0.3)), 0, 1)[..., None]
        # lighter along the ridge, darker lower down, plus fog pooling at the bottom
        fill = base_c * (1.08 - 0.35 * below)
        fog = np.exp(-((ys - (edge + H * 0.18)) / (H * 0.12)) ** 2)[..., None] * (1 - depth) * 0.25
        fill = fill * (1 - fog) + np.array(pal["haze"], np.float32) * fog
        a = np.clip(ys - edge + 1.0, 0, 1)[..., None]
        img = img * (1 - a) + fill * a

    # Sakura petals (few, soft)
    base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    prng = np.random.default_rng(39)
    for k in range(28):
        s = prng.uniform(14, 30)
        p = Image.new("RGBA", (int(s * 2), int(s * 2)), (0, 0, 0, 0))
        ImageDraw.Draw(p).ellipse((s * 0.4, s * 0.72, s * 1.6, s * 1.28),
                                  fill=(*pal["petal"], int(prng.uniform(140, 210))))
        p = p.rotate(prng.uniform(0, 360), resample=Image.BICUBIC, expand=True)
        base.alpha_composite(p, (int(prng.uniform(0.05, 0.95) * W), int(prng.uniform(0.15, 0.85) * H)))

    # Heavy film grain, the signature of the style
    arr = np.asarray(base.convert("RGB")).astype(np.float32)
    grng = np.random.default_rng(11)
    arr += grng.normal(0, 7.0, (H, W, 1)) + grng.normal(0, 2.5, (H, W, 3))
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    path = f"wallpapers/lingmo-valley-{name}.jpg"
    out.save(path, quality=93, optimize=True, progressive=True)
    print(path)


if __name__ == "__main__":
    for name in sys.argv[1:] or PALETTES:
        render(name, PALETTES[name])
