FROM python:3.8-buster
MAINTAINER Thomas Roder

ENV PYTHONPATH=/usr/local/bin/python:.
ENV PYTHONUNBUFFERED 1

RUN apt-get update -y

WORKDIR /tmp
RUN apt-get install -y sudo ncbi-blast+ clustalo mafft muscle netcat&& \
wget --quiet https://github.com/davidemms/OrthoFinder/releases/download/2.5.1/OrthoFinder_source.tar.gz && \
tar -xvf OrthoFinder_source.tar.gz && \
mv OrthoFinder_source /opt/ && \
rm OrthoFinder_source.tar.gz

ENV WORKDIR=/opengenomebrowser
WORKDIR ${WORKDIR}

COPY requirements.txt ${WORKDIR}/

RUN pip install --upgrade pip && \
pip install numpy && \
pip install -r requirements.txt && \
pip cache purge

COPY . .

RUN PYTHONPATH=$PYTHONPATH:/opengenomebrowser
