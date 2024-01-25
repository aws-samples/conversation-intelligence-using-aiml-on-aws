#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

FROM --platform=linux/amd64 ubuntu:latest

RUN apt-get update \
    && apt-get install -y python3 \
    && apt-get install -y python3-pip \
    && apt-get install -y ffmpeg

WORKDIR /app
ADD . /app

RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3","chunking.py"]