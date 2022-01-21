
//===----- boundschecker_pass.cpp - Bounds Checker transformation pass -----===//

#define DEBUG_TYPE "boundschecker"

#include <llvm/Pass.h>
#include <llvm/IR/PassManager.h>
#include <llvm/IR/BasicBlock.h>
#include <llvm/IR/Function.h>
#include <llvm/IR/InlineAsm.h>
#include <llvm/IR/InstIterator.h>
#include <llvm/IR/Instruction.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/Intrinsics.h>
#include <llvm/IR/IntrinsicInst.h>
#include <llvm/IR/InstrTypes.h>
#include <llvm/IR/Constants.h>
#include <llvm/IR/GlobalVariable.h>
#include <llvm/IR/Type.h>
#include <llvm/IR/DerivedTypes.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/IRBuilder.h>
#include <llvm/IR/InstIterator.h>
#include <llvm/IR/LegacyPassManager.h>
#include <llvm/Support/Casting.h>
#include <llvm/IR/Dominators.h>
#include <llvm/ADT/DepthFirstIterator.h>
#include <llvm/ADT/SmallSet.h>
#include <llvm/Transforms/Utils/BasicBlockUtils.h>
#include <llvm/Transforms/IPO/PassManagerBuilder.h>
#include <llvm/Support/CommandLine.h>
#include <llvm/IR/MDBuilder.h>
#include <llvm/IR/Metadata.h>
#include <llvm/Analysis/MemoryBuiltins.h>
#include <llvm/Analysis/TargetLibraryInfo.h>
#include <llvm/Analysis/ScalarEvolution.h>
#include <llvm/Analysis/ScalarEvolutionExpressions.h>
#include <llvm/Analysis/AssumptionCache.h>
#include <llvm/Analysis/LoopAccessAnalysis.h>
#include <llvm/Analysis/LoopInfo.h>
#include <llvm/Analysis/LoopIterator.h>
#include <llvm/Analysis/LoopPass.h>
#include <llvm/Analysis/ValueTracking.h>
#include <llvm/Transforms/Utils/Local.h>

#include <iostream>
#include <map>
#include <set>
#include <utility>
#include <tr1/memory>
#include <tr1/tuple>
#include <assert.h>

#define BoundsCheckerFUNC(F)  (F->getName().startswith("__runtime_"))

#define BoundsChecker_PRINT_DEBUG
#ifdef BoundsChecker_PRINT_DEBUG
#  define dbg(x) x
#else
#  define dbg(x) 
#endif

using namespace llvm;

namespace {
    static void initMain (Function * FN)
    {
        Type* ReturnTy= Type::getVoidTy(FN->getParent()->getContext());
        SmallVector <Type*, 0> ArgTypeList;
        FunctionType * hookfty= FunctionType::get(ReturnTy, ArgTypeList, false);
        FunctionCallee hook= FN->getParent()->getOrInsertFunction("__runtime_main_prologue", hookfty);
        
        Instruction * FirstIns= &*(FN->begin()->begin());
        IRBuilder<> B(FirstIns);
        CallInst* InitIns = B.CreateCall(hook);

    }
    
    static Function* MyMalloc = nullptr;
    static bool instrumentMallocCall (CallBase * CB)
    {
        /* Fill the body */
        //errs() << "Instruction: " << *CB << "\n"; 
	if(!MyMalloc){
	    Function* Malloc = CB->getCalledFunction();
            MyMalloc = Function::Create(Malloc->getFunctionType(),
                                GlobalValue::ExternalLinkage,
                                "__runtime_mymalloc",
                                CB->getModule());

	}
	if(MyMalloc){
	    CB->setCalledFunction(MyMalloc);
        }
        //errs() << "Instruction: " << *CB << "\n"; 
        return true;
    }

    static bool instrumentMemoryRead(LoadInst * LI) 
    {
        /*      Reference   */
        
        /*  Create a function prototype (__runtime_checkbound)  */
        /*  Note: void pointer type (void*) is Int8PtrTy in LLVM */ 
        Type* ReturnTy= Type::getInt8PtrTy(LI->getModule()->getContext());
        Type* ArgumentTy= Type::getInt8PtrTy(LI->getModule()->getContext());
        SmallVector <Type*, 1> ArgTypeList;
        ArgTypeList.push_back(ArgumentTy);
        FunctionType * hookfty= FunctionType::get(ReturnTy, ArgTypeList, false);
        FunctionCallee hook= LI->getModule()->getOrInsertFunction("__runtime_checkbound", hookfty);

        /*  Create a call to the function __runtime_checkbound  */
        IRBuilder<> B(LI);
        Value* Ptr = LI->getPointerOperand();
        /*  Typecast from arbitrary pointer type to runtime function's parameter type (void*). 
         *  LLVM has strict type policy. */
        Value* TmpPtr = B.CreateBitCast(Ptr, hook.getFunctionType()->getParamType(0));
        CallInst* Masked = B.CreateCall(hook, TmpPtr);
        Value* NewPtr = B.CreatePointerCast(Masked, Ptr->getType());

        /*  set the pointer operand with a return value of __runtime_checkbound (dummy tho) */
        LI->setOperand(0, NewPtr);
        
        return true;
    }
    
    static bool instrumentMemoryWrite(StoreInst * SI) 
    {
        /*  Fill the body. 
         *  Consider instrumentMemoryRead function above. */
         
        /*  Create a function prototype (__runtime_checkbound)  */
        /*  Note: void pointer type (void*) is Int8PtrTy in LLVM */ 
        Type* ReturnTy= Type::getInt8PtrTy(SI->getModule()->getContext());
        Type* ArgumentTy= Type::getInt8PtrTy(SI->getModule()->getContext());
        SmallVector <Type*, 1> ArgTypeList;
        ArgTypeList.push_back(ArgumentTy);
        FunctionType * hookfty= FunctionType::get(ReturnTy, ArgTypeList, false);
        FunctionCallee hook= SI->getModule()->getOrInsertFunction("__runtime_checkbound", hookfty);

        /*  Create a call to the function __runtime_checkbound  */
        IRBuilder<> B(SI);
        Value* Ptr = SI->getPointerOperand();
        /*  Typecast from arbitrary pointer type to runtime function's parameter type (void*). 
         *  LLVM has strict type policy. */
        Value* TmpPtr = B.CreateBitCast(Ptr, hook.getFunctionType()->getParamType(0));
        CallInst* Masked = B.CreateCall(hook, TmpPtr);
        Value* NewPtr = B.CreatePointerCast(Masked, Ptr->getType());

        /*  set the pointer operand with a return value of __runtime_checkbound (dummy tho) */
        SI->setOperand(0, NewPtr);
        
        return true;
    }

    class BoundsCheckerModule : public ModulePass {
        public:
            static char ID;

            BoundsCheckerModule() : ModulePass(ID) { }

            virtual bool runOnModule(Module& M) {

                bool Changed = false;

                for (auto F = M.begin(); F != M.end(); ++F) {
                    /*  If F is a function declaration i.e. it is not defined, 
                     *  or F is a run-time hook function to be inserted, 
                     *  we skip instrumentation. */
                    if (F->isDeclaration() || BoundsCheckerFUNC(F)) {
                        continue; 
                    }
                    if (F->getName().equals("main")) {
                        /*  This inserts a call to a run-time function, that set up data structures */
                    }
                    for (auto BI= F->begin(); BI!= F->end(); ++BI) {
                        for (auto II= BI->begin(); II!=BI->end(); ++II) {

                            Instruction * Ins= &*II;

                            /*  Instrument a LoadInst (memory read) */
                            if (auto * LI= dyn_cast<LoadInst>(Ins)) {
                                /* We skip checking memory access to constant (e.g. global variables),
                                 * since we check only heap for this assignment */
                                if (isa<Constant>(LI->getPointerOperand())) continue;
                                
                                Changed= instrumentMemoryRead(LI);
                            }
                            /*  Instrument a StoreInst (memory write) */
                            else if (auto * SI= dyn_cast<StoreInst>(Ins)) {
                                /* We skip checking memory access to constant (e.g. global variables),
                                 * since we check only heap for this assignment */
                                if (isa<Constant>(SI->getPointerOperand())) continue;
                                
                                Changed= instrumentMemoryWrite(SI);
                            }
                            /*  Instrument a CallBase  */
                            else if (auto * CB= dyn_cast<CallBase>(Ins)) {

                                Function * CalleeFn= CB->getCalledFunction();

                                /*  We instrument only calls to a function 
                                 *  (we do not handle function pointers etc) */
                                if (!CalleeFn) continue;

                                /*  We instrument only calls to malloc function  */
                                /*  We consider only C programs, so do not handle name mangling here */
                                if (CalleeFn->getName().equals("malloc")) {
                                    Changed= instrumentMallocCall(CB);
                                }
                            }
                            else {;}
                        }
                    }
                    if (F->getName().equals("main")) {
                        /*  This inserts a call to a run-time function 
                         *  setting up data structure */
                        initMain(&*F);
                    }
                }
                
                return Changed;
            };
    };
} // endof namespace

            char BoundsCheckerModule::ID = 0;
            static RegisterPass<BoundsCheckerModule> X("boundschecker", "Bounds Checker Pass", false, false);

            static void registerPass(const PassManagerBuilder &,
                    legacy::PassManagerBase &PM) {
        PM.add(new BoundsCheckerModule());
    }
    //apply the module pass at this phase because EarlyAsPossible can cause UB
    static RegisterStandardPasses
    RegisterMyPass(PassManagerBuilder::EP_ModuleOptimizerEarly,
                   registerPass);

    //to keep the pass available even in -O0
    static RegisterStandardPasses
    RegisterMyPass_non_opt(PassManagerBuilder::EP_EnabledOnOptLevel0,
                   registerPass);

