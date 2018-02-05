FROM python:2.7

WORKDIR /workspace/

RUN echo 'deb http://ftp.uk.debian.org/debian jessie-backports main' > /etc/apt/sources.list.d/soundz.list
RUN apt-get update && apt-get install -y ffmpeg portaudio19-dev vim
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
