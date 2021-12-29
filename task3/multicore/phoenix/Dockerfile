FROM python:3

WORKDIR /root 

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get update \
    && apt-get install time vim -q -y

RUN git clone https://github.com/kozyraki/phoenix.git
ADD patch ./phoenix/patch
RUN cd phoenix/patch \
    && patch -p1 < 01-Makefile.patch -d ~/phoenix \
    && patch -p1 < 02-stddefines.patch -d ~/phoenix

WORKDIR /root/phoenix/phoenix++-1.0

COPY benchmark.py ./
RUN mkdir lib \
    && make

CMD ["python3", "-u", "./benchmark.py"]
