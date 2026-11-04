#!/usr/bin/env bash
# Screenshots of a theme, without root and without touching the screen: Plymouth draws
# into an invisible Xvfb display, inside a bubblewrap mount namespace where the built
# themes stand in for /usr/share/plymouth/themes.
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
Xvfb "$display" -screen 0 "${size}x24" -nolisten tcp &
xvfb=$!
trap 'kill $xvfb 2>/dev/null' EXIT
sleep 1

bwrap --dev-bind / / --bind "$here/build/themes" /usr/share/plymouth/themes --tmpfs /run \
  --unshare-net --die-with-parent --setenv DISPLAY "$display" -- bash -c '
  set -e
  shot() { sleep "$1"; import -display "$DISPLAY" -window root "'"$out"'/'"$theme"'-$2.png"; }
  plymouthd --no-daemon --tty=/dev/null --kernel-command-line="quiet splash plymouth.theme='"$theme"'" &
  sleep 1
  plymouth show-splash
  shot 0.3 fade
  shot 2 boot
  plymouth ask-for-password --prompt="Unlock disk" >/dev/null 2>&1 &
  shot 1 password
  plymouth display-message --text="Checking the disk…"
  shot 0.5 message
  plymouth quit
'
ls "$out"/"$theme"-*.png
