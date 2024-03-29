FROM python:3.10-bullseye
MAINTAINER Thomas Roder

ENV PYTHONPATH=/usr/local/bin/python:.
ENV PYTHONUNBUFFERED 1
ENV PATH="/root/.local/bin:${PATH}"
ENV FOLDER_STRUCTURE=/folder_structure

RUN apt-get update -y

WORKDIR /tmp

# install packages via apt
RUN apt-get install -y sudo ncbi-blast+ clustalo mafft muscle netcat pigz tree && apt-get clean

# install Mummer4
RUN wget --quiet https://github.com/mummer4/mummer/releases/download/v4.0.0rc1/mummer-4.0.0rc1.tar.gz && \
    tar -xvf mummer-4.0.0rc1.tar.gz && \
    rm mummer-4.0.0rc1.tar.gz && \
    cd mummer-4.0.0rc1 && \
    ./configure --prefix=/usr/local && make && make install && \
    ldconfig && \
    cd .. && \
    rm -r mummer-4.0.0rc1/

# install OrthoFinder
RUN wget --quiet https://github.com/davidemms/OrthoFinder/releases/download/2.5.4/OrthoFinder_source.tar.gz && \
    tar -xvf OrthoFinder_source.tar.gz && \
    mv OrthoFinder_source /opt/ && \
    rm OrthoFinder_source.tar.gz

ENV WORKDIR=/opengenomebrowser
WORKDIR ${WORKDIR}

# download NCBI taxdump
RUN wget -P lib/get_tax_info/data/ --quiet ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz

# install poetry
RUN pip install --upgrade pip && \
    pip install poetry && \
    pip cache purge

# get dependencies
COPY pyproject.toml ${WORKDIR}/
COPY poetry.lock ${WORKDIR}/

# install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi && \
    yes | poetry cache clear --all pypi && \
    pip cache purge

# install GenDisCal
RUN install_gendiscal --path=/usr/local/bin

# copy repository into docker
COPY . .

# set PYTHONPATH
RUN PYTHONPATH=$PYTHONPATH:/opengenomebrowser

# load NCBI taxdump
RUN python lib/get_tax_info/get_tax_info.py get_taxid_values_by_name root
