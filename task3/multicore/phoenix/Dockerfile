FROM python:3

WORKDIR /root 

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get update \
    && apt-get install time vim libreadline-dev -q -y

RUN git clone https://github.com/kozyraki/phoenix.git
ADD patch ./phoenix/patch
RUN cd phoenix/patch \
    && patch -p1 < 01-Makefile.patch -d ~/phoenix \
    && patch -p1 < 02-stddefines.patch -d ~/phoenix \
    && patch -p1 < 03-matrix_mult.patch -d ~/phoenix

WORKDIR /root/phoenix/phoenix++-1.0
RUN mkdir lib \
    && make

WORKDIR /root/phoenix/sample_apps
COPY Makefile ./

# The folloing four command patches the src code, as the original codes are too old
# 1. patch for library cpc
# 2. patch for unneeded code for solaris
# 3. patch for c99 inline semantic
# 4. patch for file size overflow
RUN find ./ -name Makefile | xargs sed -i 's/-lcpc//' \                   
    && find ./ -name MapReduceScheduler.c | xargs sed -i '465,476d' \     
    && sed -i 's/inline/extern inline/' ./reverse_index/stddefines.h \    
    && sed -i '40s/int/long/' ./word_count/MapReduceScheduler.h \         
    && make

WORKDIR /root/phoenix
COPY benchmark.py ./
CMD ["python3", "-u", "./benchmark.py"]
