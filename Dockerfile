FROM python:3.8-buster
MAINTAINER Thomas Roder

ENV PYTHONPATH=/usr/local/bin/python:.
ENV PYTHONUNBUFFERED 1

RUN apt-get update -y

WORKDIR /tmp
RUN apt-get install -y ncbi-blast+ clustalo mafft muscle netcat&& \
wget --quiet https://github.com/davidemms/OrthoFinder/releases/download/2.3.12/OrthoFinder.tar.gz && \
tar -xvf OrthoFinder.tar.gz && \
mv OrthoFinder /opt/ && \
rm OrthoFinder.tar.gz

ENV WORKDIR=/opengenomebrowser
WORKDIR ${WORKDIR}

COPY requirements.txt ${WORKDIR}/

RUN pip install --upgrade pip && \
pip install numpy && \
pip install -r requirements.txt && \
pip cache purge

COPY . .

RUN mv OpenGenomeBrowser/settings_template.py OpenGenomeBrowser/settings.py

RUN PYTHONPATH=$PYTHONPATH:/opengenomebrowser

EXPOSE 8000
CMD ["start.sh"]