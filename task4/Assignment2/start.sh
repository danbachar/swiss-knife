#!/bin/bash

info() {
    echo "##################################> $1"
}

info "Be sure you are in the nix env"

info "Cloning template, please wait..."
template_name=llvm-template
git clone https://github.com/TUM-DSE/Swiss-Knife-LLVM-Assignments.git $template_name && cd $template_name

info "Updating files"
cp ../llvmpasses Assignment2 -r
cp ../Makefile Assignment2


info "Testing"
cd Assignment2
./run.sh

