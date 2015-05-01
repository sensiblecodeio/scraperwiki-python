FROM ubuntu:14.04

RUN apt-get update
RUN apt-get install -y python3-pip

RUN apt-get install -y python3-nose
RUN apt-get install -y ack-grep vim
RUN apt-get install -y python3-lxml
RUN apt-get install -y python-lxml python-nose python-pip

RUN locale-gen en_GB.UTF-8

RUN mkdir -p /home/nobody && \
    chown nobody /home/nobody
USER nobody
ENV HOME=/home/nobody \
    PATH=/home/nobody/.local/bin:$PATH \
    LANG=en_GB.UTF-8
WORKDIR /home/nobody

RUN mkdir -p /home/nobody/.local/bin
RUN echo python3 $* > /home/nobody/.local/bin/python
RUN chmod +x /home/nobody/.local/bin/python
RUN pip3 install --user requests sqlalchemy alembic
RUN pip install --user requests sqlalchemy alembic
COPY . /home/nobody/
RUN python3 tests.py
RUN python2 tests.py
