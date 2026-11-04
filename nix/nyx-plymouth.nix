# Nyx Plymouth for nyx-packages (copy to pkgs/nyx-plymouth.nix). Inputs: this repo as
# `src`, nyx-design as `design` (for the theme colours and the mark).
{
  stdenvNoCC,
  src,
  design,
  python3,
  librsvg,
}:
stdenvNoCC.mkDerivation {
  pname = "nyx-plymouth";
  version = "0.1.0";
  inherit src;
  nativeBuildInputs = [
    python3
    librsvg
  ];
  buildPhase = ''
    python3 tools/generate.py --design ${design} --out build/themes \
      --install-root $out/share/plymouth/themes
  '';
  installPhase = ''
    mkdir -p $out/share/plymouth/themes
    cp -r build/themes/* $out/share/plymouth/themes/
  '';
  meta.description = "The NyxOS boot splash, one Plymouth theme per Nyx theme";
}
