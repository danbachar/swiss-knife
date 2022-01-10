    # shell.nix
    let
    pkgs = import <nixpkgs>  {};
    stdenv = pkgs.stdenv;
    python3 = pkgs.python3.withPackages(p: with p; [
        # python packages here
        netifaces
        pandas
        matplotlib
    ]);
    in
    stdenv.mkDerivation {
        name = "env";
        src = ./.;
        buildInputs = with pkgs; [ python3 pkgs.telnet];
    }