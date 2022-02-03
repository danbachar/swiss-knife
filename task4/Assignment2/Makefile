TARGET   = mytest 
TARGETOPT = mytest_opt

# CHECK THE PATH! AND MODIFY ME! from here  ##################

RUNTIMELIB = ./runtime_lib/
RUNTIMEOBJ = $(RUNTIMELIB)/obj/runtime.o
SRCDIR = ./tests/
OBJDIR = ./tests/obj/
BOUNDSCHECK_PASS = ./llvmpasses/SwissBoundsChecker.so
BOUNDSCHECKOPT_PASS = ./llvmpasses/SwissBoundsCheckerOpt.so

CC = clang
CXX = clang++
LLC = llc 
LLVMLINK = llvm-link
OPT = opt

OPTLEVEL = -O1
CFLAGS = -flto -Xclang -load -Xclang $(BOUNDSCHECK_PASS) 
CFLAGSOPT = -flto -Xclang -load -Xclang $(BOUNDSCHECKOPT_PASS) 
LDFLAGS = -lm

SOURCES  := $(wildcard $(SRCDIR)/*.c)
OBJECTS  := $(SOURCES:$(SRCDIR)/%.c=$(OBJDIR)/%.o)
HOOKED   = ./tests/obj/hooked.o  
LLVMLINKED   = ./tests/obj/llvmlinked.o  

all: $(TARGET) $(TARGETOPT) IR 

$(TARGET) : $(SOURCES)
	@mkdir -p $(@D)
	clang $(CFLAGS) $(LDFLAGS) -Xlinker $(RUNTIMEOBJ) $(SOURCES) -o $@ 
	@echo "-- Compiling "$<" complete"

$(TARGETOPT) : $(SOURCES)
	@mkdir -p $(@D)
	clang $(CFLAGSOPT) $(LDFLAGS) -Xlinker $(RUNTIMEOBJ) $(SOURCES) -o $@ 
	@echo "-- Compiling "$<" complete"

IR : 
	# compile manually
	clang -O1 -flto -emit-llvm tests/main.c -c -o tests/main.bc
	clang -O1 -flto -emit-llvm tests/src1.c -c -o tests/src1.bc
	clang -O1 -flto -emit-llvm tests/src2.c -c -o tests/src2.bc
	# link bitcode file
	llvm-link tests/main.bc tests/src1.bc tests/src2.bc -o tests/base.bc
	# do boundschecker pass (Assignment2.1)
	opt -load llvmpasses/SwissBoundsChecker.so -boundschecker < tests/base.bc > tests/assignment2.1.bc
	# do boundschecker_opt pass (Assignment2.2)
	opt -load llvmpasses/SwissBoundsCheckerOpt.so -boundschecker_opt < tests/base.bc > tests/assignment2.2.bc
	# convert .bc to human-readable .ll file
	llvm-dis tests/base.bc
	llvm-dis tests/assignment2.1.bc
	llvm-dis tests/assignment2.2.bc

.PHONY: clean
clean:
	rm -f $(OBJECTS) mytest


