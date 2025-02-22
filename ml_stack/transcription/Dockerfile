#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu20.04
RUN apt-get -y update
RUN apt upgrade -y
RUN apt install software-properties-common -y
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install \
        python3.10 \
        python3-pip \
        python3.10-venv \
        python3-setuptools \
        cargo \
        ffmpeg \
        git \
         nginx \
         ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"

# Set up virtual environment
ENV VIRTUAL_ENV=/opt/program/venv
RUN python3.10 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --upgrade torch==2.4.1 
RUN pip install faster-whisper
RUN pip install setuptools-rust flask gunicorn boto3 botocore

WORKDIR /opt/program
COPY src /opt/program

