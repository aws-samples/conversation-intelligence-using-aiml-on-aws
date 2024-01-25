#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

FROM --platform=linux/amd64 ubuntu:latest

RUN apt-get update \
    && apt-get install -y python3 \
    && apt-get install -y python3-pip \
    && apt-get install -y ffmpeg

RUN pip install awscli
RUN aws --version

WORKDIR /app
ADD . /app

RUN pip install -r requirements.txt
ENTRYPOINT ["python3","convert_to_wav.py"]