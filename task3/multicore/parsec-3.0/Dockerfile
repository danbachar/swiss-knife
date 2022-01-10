FROM debian:latest

RUN mkdir /home/parsec-3.0

RUN apt-get clean && apt-get update && apt-get install -y \
	patch\
	wget\
        xz-utils

RUN wget -nv -P /home/parsec-3.0 http://parsec.cs.princeton.edu/download/3.0/parsec-3.0.tar.gz \
&& tar -C /home/ -xvf /home/parsec-3.0/parsec-3.0.tar.gz \
&& rm /home/parsec-3.0/parsec-3.0.tar.gz

WORKDIR /home/parsec-3.0
COPY patchfile ./
COPY autorun.sh ./
COPY requirements.txt ./
RUN patch -d /home/parsec-3.0 -p1 < /home/parsec-3.0/patchfile


RUN apt-get update && apt-get install -y \
        g++ \
        gettext\
        libtbb-dev\
        m4\
        make\
        xorg-dev\
        python3\
        python3-pip \
    && pip install --no-cache-dir -r requirements.txt \
    && chmod +x autorun.sh

RUN /bin/bash -c "source env.sh && ./autorun.sh"
COPY benchmark.py ./
COPY entrypoint.sh /
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
CMD python3 -u benchmark.py
