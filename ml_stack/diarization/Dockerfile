#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

FROM nvidia/cuda:11.8.0-devel-ubuntu22.04 as base
RUN apt-get -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install \
        python3-pip \
        python3-setuptools \
        ffmpeg \
        git \
         nginx \
         ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -q torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 torchtext==0.15.2 torchdata==0.6.1 --extra-index-url https://download.pytorch.org/whl/cu118 && \
	pip install -q xformers==0.0.20 triton==2.0.0

RUN pip --no-cache-dir install git+https://github.com/pyannote/pyannote-audio.git@28fcf502db86747bafb126720d6b95d7c8277295 setuptools-rust flask gunicorn pydub boto3 botocore

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"

COPY src /opt/program
WORKDIR /opt/program

