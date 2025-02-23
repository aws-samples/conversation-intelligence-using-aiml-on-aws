#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu20.04 as base
RUN apt-get -y update
RUN apt upgrade -y
RUN apt install software-properties-common -y
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install \
        python3.10 \
        python3-pip \
        python3-setuptools \
        ffmpeg \
        git \
        nginx \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*
    

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"

RUN pip install --upgrade torch==2.4.1 
RUN pip --no-cache-dir install -U torchvision torchaudio torchtext torchdata
RUN	pip install -q xformers triton
RUN pip --no-cache-dir install git+https://github.com/pyannote/pyannote-audio.git@28fcf502db86747bafb126720d6b95d7c8277295 setuptools-rust flask gunicorn pydub boto3 botocore
RUN pip install --upgrade numpy==1.26.4

COPY src /opt/program
WORKDIR /opt/program

