SOURCES = boundschecker_pass.cpp 
LIB_NAME = SwissBoundsChecker.so

SOURCES_OPT = boundschecker_pass_optimized.cpp
OPTLIB_NAME = SwissBoundsCheckerOpt.so

LDFLAGS = $(shell llvm-config --ldflags)
CXXFLAGS = -ggdb3 -Wall -fno-rtti -fPIC -shared $(shell llvm-config --cxxflags)

all: $(LIB_NAME) $(OPTLIB_NAME)

$(LIB_NAME): $(SOURCES)
	g++ $(CXXFLAGS) $(LDFLAGS) $^ -o $@

$(OPTLIB_NAME): $(SOURCES_OPT)
	g++ $(CXXFLAGS) $(LDFLAGS) $^ -o $@

clean:
	rm -f $(LIB_NAME)
