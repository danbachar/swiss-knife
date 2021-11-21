with import <nixpkgs> {};

stdenv.mkDerivation {
  name = "server";
  src = ./.;

  buildInputs = [ boost poco ];

  buildPhase = ''
    gcc -o server server.c -lPocoFoundation -lboost_system
    gcc -o server_select server_select.c -lPocoFoundation -lboost_system
    gcc -o server_epoll server_epoll.c -lPocoFoundation -lboost_system
    gcc -o server_thread server_thread.c -lPocoFoundation -lboost_system -lpthread
    gcc -o server_epoll_multitask server_epoll_multitask.c -lPocoFoundation -lboost_system
  '';

  installPhase = ''
    mkdir -p $out/bin
    cp server server_select server_epoll server_thread server_epoll_multitask $out/bin/
  '';
}
