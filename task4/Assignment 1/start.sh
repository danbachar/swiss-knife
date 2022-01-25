#!/bin/bash

info() {
    echo "##################################> $1"
}

info "Cloning template, please wait..."

template_name=llvm-template
git clone https://github.com/TUM-DSE/Swiss-Knife-LLVM-Assignments.git $template_name && cd $template_name

info "Cloning LLVM, please wait..."
git clone https://github.com/llvm/llvm-project.git && cd llvm-project

#info "CDing into directories because they exist"
#cd $template_name/llvm-project

info "Building LLVM..."
cmake -S llvm -B build -G "Ninja"

info "Building opt..."
cmake --build build --target opt

info "Opt version is: "
./build/bin/opt --version

info "Copying DeadCodeElimination passes to the right place..."
cp ../../Assignment1/llvm-modified-files/llvm/include/llvm/Transforms/Utils/DeadCodeElimination.h llvm/include/llvm/Transforms/Utils/
cp ../../Assignment1/llvm-modified-files/llvm/lib/Transforms/Utils/DeadCodeElimination.cpp llvm/lib/Transforms/Utils/

info "Copying CmakeLists.txt to the right place..."
cp ../../Assignment1/llvm-modified-files/llvm/lib/Transforms/Utils/CMakeLists.txt llvm/lib/Transforms/Utils/

info "Copying PassRegistry.def to the right place..."
cp ../../Assignment1/llvm-modified-files/llvm/lib/Passes/PassRegistry.def llvm/lib/Passes/

info "Copying PassBuilder.cpp to the right place..."
cp ../../Assignment1/llvm-modified-files/llvm/lib/Passes/PassBuilder.cpp llvm/lib/Passes/

info "Building opt again, after having copied the files..."
cmake --build build --target opt

info "Testing..."
./build/bin/opt -S -passes=dead-code-elimination-pass ../Assignment1/FunctionWithDeadCode.ll

#ninja -C build check-llvm # runs our new test alongside all other llvm lit tests
info 'Finished.'
