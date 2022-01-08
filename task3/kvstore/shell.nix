# shell.nix
let
  pkgs = import <nixpkgs>  {};
  stdenv = pkgs.stdenv;
  python3 = pkgs.python3.withPackages(p: with p; [
    # python packages here
    psutil
    pandas
    matplotlib
    setuptools
    docker
  ]);
in
  stdenv.mkDerivation {
    name = "env";
    buildInputs = with pkgs; [ hello gnumake pkgs.sysbench pkgs.dpkg pkgs.percona-server pkgs.boost pkgs.gdb pkgs.rocksdb pkgs.mysql57 pkgs.gcc48 pkgs.sqlite pkgs.gflags pkgs.zlib pkgs.bzip2 pkgs.lz4 pkgs.zstd pkgs.jdk11_headless pkgs.libevent pkgs.memcached pkgs.libmemcached pkgs.maven python3 pkgs.telnet];
}  