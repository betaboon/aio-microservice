{ pkgs ? import <nixpkgs> { } }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    pdm
    ruff
    # required for taplo-pre-commit
    cargo
  ];

  shellHook = ''
    # dirty hack to get ruff-pre-commit working
    ruff_bin=$(find ~/.cache/pre-commit -type f -name ruff)
    [ -f "$ruff_bin" ] && ln -sf ${pkgs.ruff}/bin/ruff $ruff_bin
  '';
}
