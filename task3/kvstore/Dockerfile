FROM mariadb:10.3

USER root

RUN apt-get update

RUN apt-get install -y mariadb-plugin-rocksdb git sysbench

RUN rm -rf /var/cache/apt/lists/*

RUN git clone https://github.com/Percona-Lab/sysbench-tpcc.git

ADD config-file.cnf /etc/mysql/conf.d/config-file.cnf