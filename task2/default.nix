with import <nixpkgs> {};
{ pkgs ? import (fetchTarball https://git.io/Jf0cc) {} }:

let customPython = pkgs.python38.buildEnv.override {
  extraLibs = [ pkgs.python38Packages.pandas pkgs.python38Packages.numpy pkgs.python38Packages.matplotlib ];
};
in
stdenv.mkDerivation {
  name = "server";
  src = ./.;

  buildInputs = [ boost poco customPython liburing ];

  buildPhase = ''
    gcc -o server server.c -lPocoFoundation -lboost_system
    gcc -o server_select server_select.c -lPocoFoundation -lboost_system
    gcc -o server_epoll server_epoll.c -lPocoFoundation -lboost_system
    gcc -o server_thread server_thread.c -lPocoFoundation -lboost_system -lpthread
    gcc -o server_epoll_multiprocess server_epoll_multiprocess.c -lPocoFoundation -lboost_system
    gcc -o server_uring -g server_uring.c -lPocoFoundation -lboost_system -l:liburing.a
  '';

  installPhase = ''
    mkdir -p $out/bin
    cp server server_select server_epoll server_thread server_epoll_multiprocess server_uring $out/bin/
  '';
}
