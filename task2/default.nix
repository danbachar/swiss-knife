with import <nixpkgs> {};

stdenv.mkDerivation {
  name = "server";
  src = ./.;

  buildInputs = [ boost poco ];

  buildPhase = ''
    gcc -o server server.c -lPocoFoundation -lboost_system
    gcc -o server_select server_select.c -lPocoFoundation -lboost_system
  '';

  installPhase = ''
    mkdir -p $out/bin
    cp server server_select $out/bin/
  '';
}
