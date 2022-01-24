#!/bin/bash


info() {
    echo "##################################> $1"
}

info "Cloning template, please wait..."

template_name=llvm-template
git clone https://github.com/TUM-DSE/Swiss-Knife-LLVM-Assignments.git $llvm-template

cd $template_name && nix-shell

cd 'Assignment 1'

info "Cloning LLVM, please wait..."
git clone https://github.com/llvm/llvm-project.git && cd llvm-project

info "Building LLVM..."
cmake -S llvm -B build -G "Ninja"

info "Building opt..."
cmake --build build –-target opt

info "Opt version is: "
./build/bin/opt --version

info "Copying DeadCodeElimination passes to the right place..."
cp ../../llvm-modified-files/llvm/include/llvm/Transforms/Utils/DeadCodeElimination.h llvm/include/Transform/Utils/
cp ../../llvm-modified-files/llvm/lib/Transforms/Utils/DeadCodeElimination.cpp llvm/lib/Transforms/Utils/
cp ../../llvm-modified-files/llvm/lib/Transforms/Utils/CMakeLists.txt llvm/lib/Transforms/Utils/
cp ../../llvm-modified-files/llvm/lib/Passes/PassRegistry.def llvm/lib/Passes/
cp ../../llvm-modified-files/llvm/lib/Passes/PassBuilder.cpp llvm/lib/Passes/

info "Building opt again, after having copied the DeadCodeElimination files..."
cmake --build build –-target opt