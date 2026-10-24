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

Every wallpaper carries the Lingmo OS logo (top left, below the status bar) to
promote the desktop. Unbranded originals live in `source/`; `brand.py` writes
the branded ones to `wallpapers/`, which is what gets installed:

```sh
python3 generate.py          # archlingmo-*  -> source/   (needs Pillow and numpy)
python3 generate_archmac.py  # archmac-*     -> source/
python3 brand.py             # source/* + brand/lingmo-logo*.png -> wallpapers/
```

`brand/lingmo-logo.svg` and `brand/lingmo-logo-white.svg` are the upstream Lingmo
OS logo (lingmo-settings `logo-2.svg`) without its edition badge; the white
variant is used on light or vivid backgrounds.

The Silicon pair is exported at 3840×2160 from matching 1672×941 originals.
The light edition uses clear glass and ice blue; the dark edition uses sapphire
edge lighting against midnight blue. Keep the unbranded masters in `source/`;
`python3 brand.py silicio-light.jpg silicio-dark.jpg` reapplies the project logo.
