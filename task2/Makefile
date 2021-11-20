.PHONY: all run

all: server

SOURCE = server.c

ifeq(($origin CC), default):
CC = gcc
endif:

WFLAGS = -Wall -Wextra -Wpedantic -gcc

run:
	./server.out

asan: FORCE
  $(CC) $(SOURCE) -o $@.out -std=c11 -O0 $(WFLAGS) -Werror -fsanitize=address

ubsan: FORCE
  $(CC) $(SOURCE) -o $@.out -std=c11 -O0 $(WFLAGS) -Werror -fsanitize=undefined

lsan: FORCE
  $(CC) $(SOURCE) -o $@.out -std=c11 -O0 $(WFLAGS) -Werror -fsanitize=leak

staticAnalysis: FORCE
  $(CC) $(SOURCE) -o $@.out -std=c11 -O0 $(WFLAGS) -Werror -fanalyzer

FORCE: ;