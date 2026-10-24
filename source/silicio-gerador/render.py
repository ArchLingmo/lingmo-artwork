"""Renders the Silício wallpapers from wall.html: render.py <ids> <width> <height> <outdir>
(needs python-playwright with a Chromium; CHROMIUM=/path/to/chrome to pick one)."""
import os, sys, base64, pathlib
from playwright.sync_api import sync_playwright
ids=sys.argv[1].split(','); w,h=int(sys.argv[2]),int(sys.argv[3]); out=sys.argv[4]
base=pathlib.Path(__file__).with_name("wall.html").resolve().as_uri()
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None,args=["--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist"])
    for i in ids:
        pg=b.new_page(); msgs=[]; pg.on("console",lambda m: msgs.append(m.text)); pg.on("pageerror",lambda e: msgs.append(str(e)))
        pg.goto(f"{base}?id={i}&w={w}&h={h}"); pg.wait_for_function("document.title=='done'",timeout=900000)
        data=pg.evaluate("document.getElementById('c').toDataURL('image/png')")
        open(f"{out}/{i}_{w}.png","wb").write(base64.b64decode(data.split(',')[1]))
        print(i, msgs[:3]); pg.close()
    b.close()
