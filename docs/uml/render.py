"""Render every .puml under docs/uml/ via the public PlantUML server.

Usage: python docs/uml/render.py [subdir]
Writes .png and .svg beside each source and reports any syntax error with
its line, so a broken diagram fails loudly instead of rendering an error image.
Note: this sends each diagram's text to plantuml.com.
"""
import glob, io, os, sys, urllib.error, urllib.request, zlib

ALPHA = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"

def enc64(d):
    o = []
    for i in range(0, len(d), 3):
        c = d[i:i+3]; b1 = c[0]; b2 = c[1] if len(c) > 1 else 0; b3 = c[2] if len(c) > 2 else 0
        o += [ALPHA[b1 >> 2], ALPHA[((b1 & 3) << 4) | (b2 >> 4)], ALPHA[((b2 & 15) << 2) | (b3 >> 6)], ALPHA[b3 & 63]]
    return "".join(o)

def url(text, fmt):
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    return f"https://www.plantuml.com/plantuml/{fmt}/{enc64(co.compress(text.encode()) + co.flush())}"

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), *(sys.argv[1:2]))
ok = True
for p in sorted(glob.glob(os.path.join(root, "*.puml"))):
    src = io.open(p, encoding="utf-8").read()
    name = os.path.basename(p)
    try:
        for fmt in ("png", "svg"):
            req = urllib.request.Request(url(src, fmt), headers={"User-Agent": "curl/8"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read(); err = r.headers.get("X-PlantUML-Diagram-Error")
            if err:
                raise RuntimeError(f"{err} (line {r.headers.get('X-PlantUML-Diagram-Error-Line')})")
            open(p[:-5] + "." + fmt, "wb").write(data)
        print(f"  OK    {name}")
    except urllib.error.HTTPError as e:
        ok = False
        body = e.read().decode("utf-8", "replace")
        line = [l.strip() for l in body.splitlines() if "line" in l.lower()][:1]
        print(f"  FAIL  {name}  HTTP {e.code}  {line}")
    except Exception as e:
        ok = False
        print(f"  FAIL  {name}  {e}")
sys.exit(0 if ok else 1)
