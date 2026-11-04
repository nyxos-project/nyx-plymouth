#!/usr/bin/env python3
"""Build a Plymouth theme for every Nyx theme.

    tools/generate.py [--design PATH] [--out DIR] [--only ID…]

Reads the theme colours from nyx-design (crates/nyx-theme/themes/*.toml) and the
eclipse mark from nyx-design's brand/, and writes DIR/<theme>/ with the script, its
.plymouth file and the images, ready for /usr/share/plymouth/themes. Dark themes get
the silver mark; light themes the mark in their accent. Needs rsvg-convert.
"""

import argparse
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def rgb(hexcolor):
    h = hexcolor.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))


def script_color(hexcolor):
    return ", ".join(f"{c:.3f}" for c in rgb(hexcolor))


def render(svg, out, size):
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), "-o", str(out)], input=svg.encode(), check=True)


def render_wh(svg, out, w, h):
    subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h), "-o", str(out)], input=svg.encode(), check=True)


def build(theme_file, brand, out_root, install_root):
    t = tomllib.load(open(theme_file, "rb"))
    tid = theme_file.stem
    name = t.get("name", tid)
    light = bool(t.get("light", False))
    bg = t.get("bg", "#09090a")
    accent = t.get("accent", "#5b9cff")
    text = t.get("text", "#e8e8ea")
    dim = t.get("dim_text", "#9a9aa1")
    surface = t.get("surface", t.get("card", bg))
    border = t.get("border", dim)
    out = out_root / tid
    out.mkdir(parents=True, exist_ok=True)

    if light:
        mark = (brand / "nyx-mark.svg").read_text()
        mark = re.sub(r'color="#[0-9a-fA-F]{6}"', f'color="{accent}"', mark, count=1)
    else:
        mark = (brand / "nyx-mark-silver.svg").read_text()
    render(mark, out / "mark.png", 640)

    render_wh(f'<svg xmlns="http://www.w3.org/2000/svg" width="8" height="2"><rect width="8" height="2" rx="1" fill="{text}" fill-opacity="0.12"/></svg>', out / "track.png", 8, 2)
    render_wh(f'<svg xmlns="http://www.w3.org/2000/svg" width="8" height="2"><rect width="8" height="2" rx="1" fill="{accent}"/></svg>', out / "bar.png", 8, 2)
    render_wh(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="280" height="40"><rect x="0.5" y="0.5" width="279" height="39" rx="11" fill="{surface}" stroke="{border}"/></svg>',
        out / "field.png",
        280,
        40,
    )
    render_wh(f'<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"><circle cx="4" cy="4" r="3.5" fill="{text}"/></svg>', out / "dot.png", 8, 8)

    script = (HERE / "src/nyx.script").read_text()
    script = script.replace("@BG@", script_color(bg)).replace("@DIM@", script_color(dim))
    (out / f"{tid}.script").write_text(script)
    image_dir = f"{install_root}/{tid}"
    (out / f"{tid}.plymouth").write_text(
        f"""[Plymouth Theme]
Name=Nyx ({name})
Description=The Nyx boot splash in {name}'s colours.
ModuleName=script

[script]
ImageDir={image_dir}
ScriptFile={image_dir}/{tid}.script
ConsoleLogBackgroundColor=0x{bg.lstrip('#')}
"""
    )
    return tid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", default=os.environ.get("NYX_DESIGN", str(HERE.parent / "nyx-design")))
    ap.add_argument("--out", default=str(HERE / "build/themes"))
    ap.add_argument("--install-root", default="/usr/share/plymouth/themes", help="where the themes will be installed (written into .plymouth)")
    ap.add_argument("--only", nargs="*", default=[])
    a = ap.parse_args()
    design = Path(a.design)
    themes = sorted((design / "crates/nyx-theme/themes").glob("*.toml"))
    if not themes:
        sys.exit(f"no themes in {design}/crates/nyx-theme/themes")
    built = [build(f, design / "brand", Path(a.out), a.install_root) for f in themes if not a.only or f.stem in a.only]
    print(f"built {len(built)}: {' '.join(built)}")


if __name__ == "__main__":
    main()
