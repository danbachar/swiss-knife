    # shell.nix
    let
    pkgs = import <nixpkgs>  {};
    stdenv = pkgs.stdenv;
    python3 = pkgs.python3.withPackages(p: with p; [
        # python packages here
        psutil
        netifaces
        pandas
        matplotlib
    ]);
    in
    stdenv.mkDerivation {
        name = "env";
        buildInputs = with pkgs; [ python3 pkgs.telnet];
    }  