FROM python:3.8-buster
MAINTAINER Thomas Roder

ENV PYTHONPATH=/usr/local/bin/python:.
ENV PYTHONUNBUFFERED 1

RUN apt-get update -y

WORKDIR /tmp
RUN apt-get install -y sudo ncbi-blast+ clustalo mafft muscle netcat&& \
wget --quiet https://github.com/davidemms/OrthoFinder/releases/download/2.5.2/OrthoFinder_source.tar.gz && \
tar -xvf OrthoFinder_source.tar.gz && \
mv OrthoFinder_source /opt/ && \
rm OrthoFinder_source.tar.gz

ENV WORKDIR=/opengenomebrowser
WORKDIR ${WORKDIR}

COPY requirements.txt ${WORKDIR}/

RUN wget -P lib/get_tax_info/data/ --quiet ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz

RUN pip install --upgrade pip && \
pip install numpy && \
pip install -r requirements.txt && \
pip cache purge

COPY . .

RUN PYTHONPATH=$PYTHONPATH:/opengenomebrowser

# download ncbi taxonomy
RUN python lib/get_tax_info/get_tax_info.py get_taxid_values_by_name root
