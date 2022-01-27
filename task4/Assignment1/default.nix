{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/bc59ba15b64d0a0ee1d1764f18b4f3480d2c3e5a.tar.gz") {}
}:
pkgs.mkShell {
  nativeBuildInputs = [
    pkgs.cmake
    pkgs.llvmPackages_12.llvm
    pkgs.llvmPackages_12.clang
    pkgs.ninja
  ];
}
