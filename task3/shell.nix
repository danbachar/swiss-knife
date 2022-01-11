# shell.nix
let
  pkgs = import <nixpkgs>  {};
  stdenv = pkgs.stdenv;
  python3 = pkgs.python3.withPackages(p: with p; [
    # python packages here
    psutil
    pandas
    numpy
    netifaces
    matplotlib
    setuptools
    docker
  ]);
in
  stdenv.mkDerivation {
    name = "env";
    src = ./.;
    buildInputs = with pkgs; [ 
        pkgs.go 
        hello 
        gnumake 
        pkgs.dpkg 
        pkgs.percona-server 
        pkgs.boost 
        pkgs.gdb 
        pkgs.rocksdb 
        pkgs.sqlite
        pkgs.mysql57
        pkgs.lua 
        pkgs.sysbench 
        pkgs.gcc48 
        pkgs.gflags 
        pkgs.zlib 
        pkgs.bzip2 
        pkgs.lz4 
        pkgs.zstd 
        pkgs.jdk11_headless 
        pkgs.libevent 
        pkgs.memcached 
        pkgs.libmemcached 
        pkgs.maven 
        python3 
        pkgs.telnet
        php
        autoreconfHook
        popt
        libaio
        perl
        gcc7
        pcre
        glibc.out
        glibc.static
        bc
        ];
}  
