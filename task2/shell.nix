with (import <nixpkgs> {});
mkShell {
  buildInputs = [
    perl
    python38Packages.pandas
    python38Packages.matplotlib
    python38Packages.netifaces
  ];
}
