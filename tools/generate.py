#!/usr/bin/env python3
"""Build a Plymouth theme for every Nyx theme.

    tools/generate.py [--nyx-theme BIN] [--logo FILE] [--out DIR] [--only ID…]

Asks the Nyx theme engine (the `nyx-theme` command from nyx-design) for the built-in
themes, each one's resolved colours, and the logo drawn in them, and writes
DIR/<theme>/ with the script, its .plymouth file and the images, ready for
/usr/share/plymouth/themes. The splash shows the NYXOS wordmark exactly as the desktop
wallpaper does (nyx-wallpapers), so the boot ends on the desktop's picture. With
--logo it shows FILE instead, square (an SVG drawn in `currentColor` takes each theme's
logo colour; a PNG is used as it is). Needs rsvg-convert.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

# The wordmark as nyx-wallpapers draws it on a 3840 × 2160 wallpaper: 24 px a cell.
WORDMARK_CELL = 24

# Backgrounds that differ from the theme's surface, as in nyx-wallpapers' tools/wordmark.py.
BACKGROUND = {"catppuccin-mocha": "#181825"}


def rgb(hexcolor):
    h = hexcolor.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))


def script_color(hexcolor):
    return ", ".join(f"{c:.4f}" for c in rgb(hexcolor))


def render(svg, out, size):
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), "-o", str(out)], input=svg.encode(), check=True)


def render_wh(svg, out, w, h):
    subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h), "-o", str(out)], input=svg.encode(), check=True)


class Engine:
    """The nyx-theme command, kept away from the user's own themes and logo."""

    def __init__(self, program, logo):
        self.program = program
        self.logo = logo
        self.scratch = tempfile.TemporaryDirectory()
        self.env = dict(os.environ)
        for var in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME", "XDG_RUNTIME_DIR"):
            self.env[var] = self.scratch.name
        self.env["NYX_SYSTEM_LOGO_DIR"] = self.scratch.name
        self.env.pop("NYX_LOGO", None)

    def run(self, *args):
        return subprocess.run([self.program, *args], env=self.env, capture_output=True, text=True, check=True).stdout

    def themes(self):
        return json.loads(self.run("list", "--builtin", "--json"))

    def colors(self, tid):
        return json.loads(self.run("resolve", "--theme", tid, "--json"))["tokens"]["colors"]

    def logo_svg(self, tid, size):
        extra = ["--file", str(self.logo)] if self.logo else []
        return self.run("logo", "svg", "--theme", tid, "--size", str(size), *extra)


def build(engine, theme, out_root, install_root):
    tid = theme["id"]
    name = theme["name"]
    c = engine.colors(tid)
    bg = BACKGROUND.get(tid, c["surface.primary"])
    accent = c["accent.primary"]
    text = c["text.primary"]
    dim = c["text.secondary"]
    surface = c["surface.alternate"]
    border = c["border.default"]
    out = out_root / tid
    out.mkdir(parents=True, exist_ok=True)

    if engine.logo:
        render(engine.logo_svg(tid, 640), out / "mark.png", 640)
    else:
        mark = (HERE / "src/wordmark.svg").read_text().replace("currentColor", c.get("brand.logo", accent))
        w, h = (int(v) for v in mark.split('viewBox="0 0 ', 1)[1].split('"', 1)[0].split())
        render_wh(mark, out / "mark.png", w * WORDMARK_CELL, h * WORDMARK_CELL)

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
    script = script.replace("@WORDMARK@", "0" if engine.logo else "1")
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
ConsoleLogBackgroundColor=0x{bg.lstrip('#')[:6]}
"""
    )
    return tid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nyx-theme", default=os.environ.get("NYX_THEME", "nyx-theme"), help="the nyx-theme command")
    ap.add_argument("--logo", default=None, help="an SVG or PNG to use instead of the Nyx mark")
    ap.add_argument("--out", default=str(HERE / "build/themes"))
    ap.add_argument("--install-root", default="/usr/share/plymouth/themes", help="where the themes will be installed (written into .plymouth)")
    ap.add_argument("--only", nargs="*", default=[])
    a = ap.parse_args()
    engine = Engine(a.nyx_theme, Path(a.logo).resolve() if a.logo else None)
    themes = engine.themes()
    if not themes:
        sys.exit("the theme engine lists no themes")
    built = [build(engine, t, Path(a.out), a.install_root) for t in themes if not a.only or t["id"] in a.only]
    print(f"built {len(built)}: {' '.join(built)}")


if __name__ == "__main__":
    main()
