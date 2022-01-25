//===-- DeadCodeElimination.h - Example Transformations ------------------*- C++
//-*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#ifndef LLVM_TRANSFORMS_UTILS_DEADCODEELIMINATION_H
#define LLVM_TRANSFORMS_UTILS_DEADCODEELIMINATION_H

#include "llvm/IR/Function.h"
#include "llvm/IR/InstIterator.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/PassManager.h"
#include "llvm/Transforms/Utils/Local.h"

namespace llvm {

class DeadCodeEliminationPass : public FunctionPass<DeadCodeEliminationPass> {
 public:
  PreservedAnalyses run(Function &F, FunctionAnalysisManager &AM);
};

}  // namespace llvm

#endif  // LLVM_TRANSFORMS_UTILS_DEADCODEELIMINATION_H
