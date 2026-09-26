#!/usr/bin/env python3
"""Arch Linux wallpapers in the spirit of recent macOS ones (light and dark).

Stacked flowing layers, each with its own vertical gradient and a soft
shadow on the layer beneath, over a smooth sky. Palette built around the
Arch blue (#1793D1). Deterministic output into source/ (brand.py adds the logo).
"""
import math
import sys

import numpy as np
from PIL import Image, ImageFilter

W, H = 3840, 2160

# Each layer: (baseline 0..1, amplitude 0..1, frequency, phase, top colour, bottom colour)
PALETTES = {
    "light": {
        "sky": ((150, 196, 250), (255, 214, 214)),
        "glow": ((255, 190, 170), 0.55),
        "layers": [
            (0.30, 0.10, 0.55, 0.4, (160, 205, 250), (120, 180, 245)),
            (0.42, 0.11, 0.70, 2.1, (110, 175, 240), (60, 150, 225)),
            (0.54, 0.10, 0.60, 4.0, (60, 160, 225), (23, 147, 209)),
            (0.66, 0.09, 0.80, 1.2, (40, 120, 215), (35, 90, 200)),
            (0.78, 0.08, 0.65, 3.3, (80, 85, 210), (60, 60, 180)),
            (0.90, 0.07, 0.75, 5.1, (110, 70, 200), (70, 45, 160)),
        ],
        "shadow": 0.22,
    },
    "dark": {
        "sky": ((8, 12, 30), (30, 40, 96)),
        "glow": ((90, 120, 255), 0.35),
        "layers": [
            (0.30, 0.10, 0.55, 0.4, (28, 52, 110), (22, 42, 95)),
            (0.42, 0.11, 0.70, 2.1, (20, 70, 140), (18, 58, 125)),
            (0.54, 0.10, 0.60, 4.0, (16, 110, 170), (12, 85, 150)),
            (0.66, 0.09, 0.80, 1.2, (24, 70, 150), (18, 50, 120)),
            (0.78, 0.08, 0.65, 3.3, (45, 45, 125), (32, 30, 100)),
            (0.90, 0.07, 0.75, 5.1, (62, 34, 115), (40, 22, 85)),
        ],
        "shadow": 0.45,
    },
}


def lerp(a, b, t):
    return np.array(a, np.float32) * (1 - t) + np.array(b, np.float32) * t


def curve(base, amp, freq, phase):
    x = np.linspace(0, 1, W, dtype=np.float32)
    # Two harmonics give the relaxed, asymmetric swell of a dune
    y = (base + amp * np.sin(freq * math.tau * x + phase)
         + amp * 0.35 * np.sin(freq * 2.3 * math.tau * x + phase * 1.7))
    return y * H


def render(name, pal):
    ys = np.arange(H, dtype=np.float32)[:, None]
    t_sky = ys / H
    img = lerp(pal["sky"][0], pal["sky"][1], (t_sky[..., None] / 0.45).clip(0, 1) ** 1.3) * np.ones((1, W, 1), np.float32)
    # Sunrise-like glow over the horizon, off-centre to the right
    xs = np.arange(W, dtype=np.float32)[None, :]
    g = np.exp(-(((xs - W * 0.66) / (W * 0.35)) ** 2 + ((ys - H * 0.36) / (H * 0.22)) ** 2))
    glow_color, glow_strength = pal["glow"]
    img = img * (1 - g[..., None] * glow_strength) + np.array(glow_color, np.float32) * g[..., None] * glow_strength

    for i, (base, amp, freq, phase, top, bottom) in enumerate(pal["layers"]):
        edge = curve(base, amp, freq, phase)[None, :]
        # Soft shadow cast on everything already drawn, just above this layer's edge
        dist = edge - ys
        shadow = np.clip(1 - np.abs(dist - H * 0.012) / (H * 0.05), 0, 1) ** 2
        shadow = np.where(dist > 0, shadow, 0) * pal["shadow"] * (0.35 if i == 0 else 1.0)
        img *= (1 - shadow[..., None])
        # Layer fill with its own gradient from its edge down to the bottom
        inside = ys >= edge
        t = np.clip((ys - edge) / (H - edge + 1), 0, 1)
        fill = lerp(top, bottom, t[..., None] ** 0.8)
        # Thin highlight along the crest
        crest = np.clip(1 - np.abs(ys - edge) / (H * 0.004), 0, 1)[..., None] * 18
        # Anti-aliased edge
        a = np.clip(ys - edge + 0.5, 0, 1)[..., None]
        img = img * (1 - a) + (fill + crest * inside[..., None]) * a

    rng = np.random.default_rng(7)
    img += rng.normal(0, 2.0, (H, W, 1))  # fine grain against banding
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")
    out = out.filter(ImageFilter.GaussianBlur(0.6))
    path = f"source/archmac-{name}.jpg"
    out.save(path, quality=92, optimize=True, progressive=True)
    print(path)


if __name__ == "__main__":
    for name in sys.argv[1:] or PALETTES:
        render(name, PALETTES[name])
