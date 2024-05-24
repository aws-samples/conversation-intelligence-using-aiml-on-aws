#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

FROM --platform=linux/amd64 ubuntu:latest

RUN apt-get update \
    && apt-get install -y python3 \
    && apt-get install -y python3-pip \
    && apt-get install -y ffmpeg

WORKDIR /app
ADD . /app
ENV PIP_BREAK_SYSTEM_PACKAGES 1
RUN pip3 install -q boto3~=1.28.65 pydub~=0.25.1
ENTRYPOINT ["python3","chunking.py"]