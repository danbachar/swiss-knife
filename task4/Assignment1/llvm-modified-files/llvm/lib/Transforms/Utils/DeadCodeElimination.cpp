//===-- DeadCodeElimination.cpp - Example Transformations
//--------------------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "llvm/Transforms/Utils/DeadCodeElimination.h"

using namespace llvm;

PreservedAnalyses DeadCodeEliminationPass::run(Function &F,
                                               FunctionAnalysisManager &AM) {
  char changed = 1;
  // some instructions may become dead after we remove other instructions, so we
  // nned to repeat until no instructions are removed in an interation
  while (changed) {
    changed = 0;
    // A working list to store instructions that should be removed
    SmallVector<Instruction *> worklist;
    for (inst_iterator I = inst_begin(F), E = inst_end(F); I != E; ++I) {
      // Add trivially dead instructions to worklist
      if (isInstructionTriviallyDead(&*I)) {
        worklist.push_back(&*I);
        changed = 1;
      } else {
          // ???
      }
    }
    // Delete instructions that are dead
    while (!worklist.empty()) {
      Instruction *I = worklist.pop_back_val();

      // before eliminating the instruction, add all child operations that
      // become dead when nulling out to the worklist
      for (unsigned i = 0, e = I->getNumOperands(); i != e; ++i) {
        Value *op = I->getOperand(i);
        I->setOperand(i, nullptr);

        Instruction *instFromOp = dyn_cast<Instruction>(op);
        if (
            // verify that the operation is not used
            op->use_empty() && op != I &&
            instFromOp
            // check if the operation is trivially dead
            && isInstructionTriviallyDead(instFromOp))
          worklist.push_back(instFromOp);
      }

      I->eraseFromParent();
    }
  }
  errs() << "DeadCodeElimination pass is running\n";
  return PreservedAnalyses::all();
}