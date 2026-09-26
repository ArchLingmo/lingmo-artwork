#!/usr/bin/env python3
"""Puts the Lingmo OS logo on the wallpapers: source/<name> -> wallpapers/<name>.

The logo sits at the top left, just below the status bar, like on the upstream
Lingmo wallpapers. Dark backgrounds get the brand-colour logo; light or vivid
ones get the white variant with a soft shadow.
"""
import sys

from PIL import Image, ImageFilter

# name -> logo variant
WALLPAPERS = {
    "archlingmo-light.jpg": "white",
    "archlingmo-dark.jpg": "white",
    "archmac-light.jpg": "color",
    "archmac-dark.jpg": "color",
    "lingmo-arch-monterey-4k.png": "white",
}

LOGO_HEIGHT = 0.055   # fraction of the wallpaper height
MARGIN_X = 0.03       # fraction of the width
MARGIN_Y = 0.065      # fraction of the height, clears the status bar


def brand(name, variant):
    wp = Image.open(f"source/{name}").convert("RGBA")
    W, H = wp.size
    logo = Image.open("brand/lingmo-logo-white.png" if variant == "white" else "brand/lingmo-logo.png")
    h = round(H * LOGO_HEIGHT)
    logo = logo.resize((round(logo.width * h / logo.height), h), Image.LANCZOS)
    pos = (round(W * MARGIN_X), round(H * MARGIN_Y))

    if variant == "white":
        # soft shadow so the white logo reads on bright areas too
        shadow = Image.new("RGBA", logo.size, (0, 0, 0, 0))
        shadow.putalpha(logo.getchannel("A").point(lambda a: a * 0.35))
        shadow = shadow.filter(ImageFilter.GaussianBlur(h * 0.06))
        wp.alpha_composite(shadow, (pos[0], pos[1] + round(h * 0.03)))
    wp.alpha_composite(logo, pos)

    out = f"wallpapers/{name}"
    if name.endswith(".jpg"):
        wp.convert("RGB").save(out, quality=93, optimize=True, progressive=True)
    else:
        wp.save(out, optimize=True)
    print(out)


if __name__ == "__main__":
    for name in sys.argv[1:] or WALLPAPERS:
        brand(name, WALLPAPERS[name])
