with import <nixpkgs> {};

stdenv.mkDerivation {
  name = "server";
  src = ./.;

  buildInputs = [ boost poco ];

  buildPhase = "gcc -o server server.c -lPocoFoundation -lboost_system";

  installPhase = ''
    mkdir -p $out/bin
    cp server $out/bin/
  '';
}