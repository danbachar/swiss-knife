{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/bc59ba1>
}:
pkgs.mkShell {
  nativeBuildInputs = [
    pkgs.cmake
    pkgs.llvmPackages_12.llvm
    pkgs.llvmPackages_12.clang
    pkgs.ninja
  ];
}
