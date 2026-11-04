# Nyx Plymouth

The NyxOS boot splash: the theme's background, the Nyx eclipse fading in at the
centre, a thin progress line under it, and a quiet password field when the disk needs
unlocking. No other text, no elaborate animation.

There's one Plymouth theme per Nyx theme, built from nyx-design: its colours from
`crates/nyx-theme/themes/*.toml`, the mark from `brand/`. Dark themes use the silver
mark, light themes the mark in their accent.

```sh
tools/generate.py --design ../nyx-design          # → build/themes/<theme>/
tools/preview.sh nyx-dark 1920x1080              # → build/preview/nyx-dark-*.png
```

`preview.sh` needs Xvfb and bubblewrap and runs without root: Plymouth draws into an
invisible display, with the built themes mounted over `/usr/share/plymouth/themes`
for that run only.

## NyxOS

The package runs `tools/generate.py --install-root $out/share/plymouth/themes` and
installs `build/themes/*`; the system sets
`boot.plymouth = { enable = true; themePackages = [ nyx-plymouth ]; theme = "nyx-dark"; }`.
The boot theme is a system setting and can differ from the desktop theme.

## Files

- `src/nyx.script`: the Plymouth script, with `@BG@` and `@DIM@` filled in per theme.
- `tools/generate.py`: builds the themes.
- `tools/preview.sh`: screenshots the fade-in, the boot, the password prompt and a
  message.
