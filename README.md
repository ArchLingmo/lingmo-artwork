# lingmo-artwork

ArchLingmo wallpapers (3840×2160, light and dark), installed into
`/usr/share/backgrounds/lingmoos/` so they show up in Settings → Background.
`silicio-light.jpg` is the default for new desktops; `silicio-dark.jpg` is the
login (SDDM) background for the Silicon release. Existing desktop choices are preserved.

| File | Style |
|---|---|
| `silicio-{light,dark}.jpg` | refractive glass ribbons in ice blue and midnight sapphire, Silicon release |
| `lingmo-arch-monterey-4k.png` | layered sunset hills, sakura petals, anime silhouette (default) |
| `archlingmo-{light,dark}.jpg` | soft blue fields, silk ribbon and arcs |
| `archmac-{light,dark}.jpg` | macOS-inspired stacked waves in Arch blue, sunrise sky |
| `axo-{dia,noite,ia,sonho}.jpg` | Axo, the mascot: thumbs-up by day, headphones under the stars, holographic AI screens, asleep under the moon |

Every wallpaper carries the ArchLingmo logo (top left, below the status bar) to
promote the desktop. Unbranded originals live in `source/`; `brand.py` writes
the branded ones to `wallpapers/`, which is what gets installed:

```sh
python3 generate.py          # archlingmo-*  -> source/   (needs Pillow and numpy)
python3 generate_archmac.py  # archmac-*     -> source/
python3 generate_axo.py      # axo-*         -> source/   (art from brand/axo)
python3 brand.py             # source/* + brand/archlingmo-logo*.png -> wallpapers/
```

`brand/archlingmo-logo.svg` and `brand/archlingmo-logo-white.svg` are the
ArchLingmo symbol (`brand/axo/05_logo`) with the "ArchLingmo" wordmark in Inter
Bold; the white variant is used on dark or vivid backgrounds. The older
`brand/lingmo-logo*` files are the upstream Lingmo OS logo, no longer used.

`source/lingmo-arch-monterey-4k.png` had a "LINGMO · ARCH" caption baked in at
the bottom right; it was inpainted out so only the top-left logo remains.

The Silicon pair is exported at 3840×2160 from matching 1672×941 originals.
The light edition uses clear glass and ice blue; the dark edition uses sapphire
edge lighting against midnight blue. Keep the unbranded masters in `source/`;
`python3 brand.py silicio-light.jpg silicio-dark.jpg` reapplies the project logo.
