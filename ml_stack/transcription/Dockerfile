#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04
RUN apt-get -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install \
        python3-pip \
        python3-setuptools \
        ffmpeg \
        git \
         nginx \
         ca-certificates \
    && rm -rf /var/lib/apt/lists/*

#RUN pip --no-cache-dir install git+https://github.com/openai/whisper.git setuptools-rust flask gunicorn boto3 botocore
RUN pip install --force-reinstall "faster-whisper @ https://github.com/guillaumekln/faster-whisper/archive/refs/heads/master.tar.gz"
RUN pip install setuptools-rust flask gunicorn boto3 botocore

RUN pip install torch==2.0.1+cu118 -f https://download.pytorch.org/whl/torch_stable.html

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"

COPY src /opt/program
WORKDIR /opt/program
