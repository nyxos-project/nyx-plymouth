#!/usr/bin/env bash
# Screenshots of a theme, without root and without touching the screen: Plymouth draws
# into an invisible Xvfb display, inside a bubblewrap sandbox where it runs as root of
# its own user namespace and the built themes stand in for /usr/share/plymouth/themes.
#
#   tools/preview.sh [THEME] [WIDTHxHEIGHT]      → build/preview/THEME-*.png
set -euo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
theme=${1:-nyx-dark}
size=${2:-1920x1080}
out="$here/build/preview"
mkdir -p "$out"
[[ -d $here/build/themes/$theme ]] || "$here/tools/generate.py" --only "$theme"
command -v Xvfb >/dev/null || { echo "Xvfb is needed: sudo pacman -S xorg-server-xvfb" >&2; exit 1; }

display=:$((90 + RANDOM % 9))
Xvfb "$display" -screen 0 "${size}x24" -nolisten tcp >/dev/null 2>&1 &
xvfb=$!
trap 'kill $xvfb 2>/dev/null' EXIT
sleep 1

# plymouthd wants a real terminal (`script` gives it one) and finds its theme in
# /run/plymouth/plymouthd.defaults (a private /run here).
inner='
  ulimit -c 0
  mkdir -p /run/plymouth
  printf "[Daemon]\nTheme=%s\n" "$THEME" > /run/plymouth/plymouthd.defaults
  shot() { sleep "$1"; import -display "$DISPLAY" -window root "$OUT/$THEME-$2.png"; }
  plymouthd --no-daemon --tty="$(tty)" --kernel-command-line="quiet splash" &
  sleep 1.5
  plymouth show-splash
  shot 0.3 fade
  shot 3 boot
  plymouth ask-for-password --prompt="Please enter passphrase for disk NyxOS (cryptroot):" >/dev/null 2>&1 &
  shot 1 password
  plymouth display-message --text="Checking the disk…"
  shot 0.5 message
  plymouth quit
'
bwrap --dev-bind / / --bind "$here/build/themes" /usr/share/plymouth/themes --tmpfs /run \
  --unshare-user --uid 0 --gid 0 --unshare-net --die-with-parent \
  --setenv DISPLAY "$display" --setenv THEME "$theme" --setenv OUT "$out" \
  -- script -qec "$inner" /dev/null >/dev/null
ls "$out"/"$theme"-*.png
