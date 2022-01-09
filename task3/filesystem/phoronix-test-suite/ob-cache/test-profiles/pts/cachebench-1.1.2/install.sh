#!/bin/sh

tar -zxvf llcbench-20170104.tar.gz
cd llcbench/

cd cachebench
sed -i '.orig' '/#include <malloc.h>/d' cachebench.c
cd ~/llcbench

make linux-mpich
make cache-bench
echo $? > ~/install-exit-status

cd ..

echo "#!/bin/sh
cd llcbench/cachebench/
./cachebench \$@ > \$LOG_FILE" > cachebench
chmod +x cachebench
