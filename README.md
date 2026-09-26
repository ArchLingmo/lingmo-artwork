# lingmo-artwork

ArchLingmo wallpapers (3840×2160, light and dark), installed into
`/usr/share/backgrounds/lingmoos/` so they show up in Settings → Background.
`lingmo-arch-monterey-4k.png` is the default desktop and login (SDDM) wallpaper.

| File | Style |
|---|---|
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
