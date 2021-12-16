include rocksdb/make_config.mk

ifndef DISABLE_JEMALLOC
	ifdef JEMALLOC
		PLATFORM_CXXFLAGS += -DROCKSDB_JEMALLOC -DJEMALLOC_NO_DEMANGLE
	endif
	EXEC_LDFLAGS := $(JEMALLOC_LIB) $(EXEC_LDFLAGS) -lpthread
	PLATFORM_CXXFLAGS += $(JEMALLOC_INCLUDE)
endif

ifneq ($(USE_RTTI), 1)
	CXXFLAGS += -fno-rtti
endif

CFLAGS += -Wstrict-prototypes

.PHONY: clean librocksdb

all: initRocksDB

initRocksDB: librocksdb initRocksDB.cc
	$(CXX) $(CXXFLAGS) $@.cc -o$@ rocksdb/librocksdb.a -Irocksdb/include -O2 -std=c++11 $(PLATFORM_LDFLAGS) $(PLATFORM_CXXFLAGS) $(EXEC_LDFLAGS)
	$$(mkdir -p bin && mv initRocksDB ./bin/initRocksDB)

.c.o:
	$(CC) $(CFLAGS) -c $< -o $@ -Irocksdb/include

clean:
	rm -rf ./bin/*

librocksdb:
	cd rocksdb && $(MAKE) static_lib