# Nyx Plymouth for nyx-packages (copy to pkgs/nyx-plymouth.nix). Inputs: this repo as
# `src`, the `nyx-theme` package (the theme engine's command), and the system logo as
# `logo` when one is set (the Nyx mark otherwise).
{
  lib,
  stdenvNoCC,
  src,
  nyx-theme,
  python3,
  librsvg,
  logo ? null,
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
    python3 tools/generate.py --nyx-theme ${lib.getExe nyx-theme} \
      ${lib.optionalString (logo != null) "--logo ${logo}"} \
      --out build/themes --install-root $out/share/plymouth/themes
  '';
  installPhase = ''
    mkdir -p $out/share/plymouth/themes
    cp -r build/themes/* $out/share/plymouth/themes/
  '';
  meta.description = "The NyxOS boot splash, one Plymouth theme per Nyx theme";
}
