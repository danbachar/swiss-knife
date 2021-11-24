with (import <nixpkgs> {});
mkShell {
  buildInputs = [
    python38Packages.pandas
    python38Packages.matplotlib
    python38Packages.netifaces
  ];
}
