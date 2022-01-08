docker-compose down
docker-compose up --build -d --remove-orphans
sleep 5
docker exec -it kvstore_myrocks_1 mysql -e "DROP DATABASE IF EXISTS sbtest;"
docker exec -it kvstore_myrocks_1 mysql -e "CREATE DATABASE sbtest;"
docker exec -it kvstore_myrocks_1 mysql -e "DROP USER IF EXISTS 'sbtest'@'localhost';"
docker exec -it kvstore_myrocks_1 mysql -e "CREATE USER 'sbtest'@'localhost';"
docker exec -it kvstore_myrocks_1 mysql -e "GRANT ALL PRIVILEGES ON * . * TO 'sbtest'@'localhost';"
docker exec -it kvstore_myrocks_1 mysql -e "FLUSH PRIVILEGES;"
# prepare
docker exec -it -w /sysbench-tpcc kvstore_myrocks_1 ./tpcc.lua --mysql-socket=/var/run/mysqld/mysqld.sock --mysql-user=root --mysql-db=sbtest --time=30 --threads=64 --report-interval=10 --tables=10 --scale=10 --use_fk=0 --mysql_storage_engine=rocksdb --mysql_table_options='COLLATE latin1_bin' --trx_level=RC --db-driver=mysql prepare
mkdir ./result/tpcc/
# benchmark
for THREADS in 2 4 8 16 32 64 
do
	(docker exec -it -w /sysbench-tpcc kvstore_myrocks_1 ./tpcc.lua --mysql-socket=/var/run/mysqld/mysqld.sock --mysql-user=root --mysql-db=sbtest --time=30 --threads=$THREADS --report-interval=10 --tables=10 --scale=10 --db-driver=mysql run) > ./result/tpcc/tpcc_result_$THREADS.txt
done
# cleanup
docker exec -it -w /sysbench-tpcc kvstore_myrocks_1 ./tpcc.lua --mysql-socket=/var/run/mysqld/mysqld.sock --mysql-user=root --mysql-db=sbtest --time=30 --threads=64 --report-interval=10 --tables=10 --scale=10 --db-driver=mysql cleanup