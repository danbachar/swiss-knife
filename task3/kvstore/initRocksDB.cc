#include <cassert>
#include <string>
#include <rocksdb/db.h>
#include <rocksdb/slice.h>
#include <rocksdb/options.h>
#include <iostream>

using namespace ROCKSDB_NAMESPACE;

int main(int argc, char** argv){
    DB* db;
    Options options;
    std::string path = "/tmp/rocksdbBenchmarking";
    if (argc >= 2) 
        path = argv[1];
    options.create_if_missing = true;
    Status status = DB::Open(options, path, &db);
    assert(status.ok());
}
  