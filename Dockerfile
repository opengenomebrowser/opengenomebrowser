FROM python:3.9-buster
MAINTAINER Thomas Roder

ENV PYTHONPATH=/usr/local/bin/python:.
ENV PYTHONUNBUFFERED 1

RUN apt-get update -y

WORKDIR /tmp

# install packages via apt
RUN apt-get install -y sudo ncbi-blast+ clustalo mafft muscle netcat pigz && apt-get clean

# install OrthoFinder
RUN wget --quiet https://github.com/davidemms/OrthoFinder/releases/download/2.5.2/OrthoFinder_source.tar.gz && \
tar -xvf OrthoFinder_source.tar.gz && \
mv OrthoFinder_source /opt/ && \
rm OrthoFinder_source.tar.gz

# install Mummer4
RUN wget --quiet https://github.com/mummer4/mummer/releases/download/v4.0.0rc1/mummer-4.0.0rc1.tar.gz && \
tar -xvf mummer-4.0.0rc1.tar.gz && \
rm mummer-4.0.0rc1.tar.gz && \
cd mummer-4.0.0rc1 && \
./configure --prefix=/usr/local && make && make install && \
ldconfig && \
cd .. && \
rm -rf mummer-4.0.0rc1/

ENV WORKDIR=/opengenomebrowser
WORKDIR ${WORKDIR}

# download NCBI taxdump
RUN wget -P lib/get_tax_info/data/ --quiet ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz

# install python packages
COPY requirements.txt ${WORKDIR}/
RUN pip install --upgrade pip && \
pip install numpy && \
pip install -r requirements.txt && \
pip cache purge

# copy repository into docker
COPY . .

# set PYTHONPATH
RUN PYTHONPATH=$PYTHONPATH:/opengenomebrowser

# load NCBI taxdump
RUN python lib/get_tax_info/get_tax_info.py get_taxid_values_by_name root
