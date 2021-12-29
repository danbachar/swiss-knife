# shell.nix
let
  pkgs = import <nixpkgs>  {};
  stdenv = pkgs.stdenv;
  python3 = pkgs.python3.withPackages(p: with p; [
    # python packages here
    psutil
    pandas
    netifaces
    matplotlib
  ]);
in
  stdenv.mkDerivation {
    name = "env";
    buildInputs = with pkgs; [ hello gnumake pkgs.gcc48 pkgs.gflags pkgs.zlib pkgs.bzip2 pkgs.lz4 pkgs.zstd pkgs.jdk11_headless pkgs.libevent pkgs.memcached pkgs.libmemcached pkgs.maven python3 pkgs.telnet];
}  