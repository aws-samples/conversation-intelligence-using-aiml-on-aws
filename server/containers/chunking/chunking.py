#!/bin/bash

#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import logging
import os
import re
import sys
import time
import pickle

import boto3
from pydub import AudioSegment

# Getting S3 File attributes from previous step
BUCKET = os.environ.get("BUCKET", "")
KEY = os.environ.get("KEY", "")
output_s3_key = os.environ.get("output_s3_key", "")
audio_wav_file = os.environ.get("audio_wav_file", "")
audio_chunks_s3_key = os.environ.get("audio_chunks_s3_key", "")
diarization_file = os.environ.get("diarization_file", "")
groups = os.environ.get("groups", "")


# Configuring Logger to DEBUG
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger()
logger.info(f"Chunking of {audio_wav_file} from {output_s3_key}...")

s3_client = boto3.client("s3")


# Utility function to change text to millisec
def millisec(time_str):
    spl = time_str.split(":")
    s = (int)((int(spl[0]) * 60 * 60 + int(spl[1]) * 60 + float(spl[2])) * 1000)
    return s


def upload_directory(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            head, file_name = os.path.split(file_path)
            s3_client.upload_file(file_path, BUCKET, f"{audio_chunks_s3_key}{file_name}")


def chunk_wav_files():
    fn_start = time.time()

    s3_client.download_file(BUCKET, f"{output_s3_key}/{audio_wav_file}", audio_wav_file)
    logger.info(f"Downloaded {audio_wav_file}...")

    s3_client.download_file(BUCKET, f"{output_s3_key}/{diarization_file}", diarization_file)
    logger.info(f"Downloaded {diarization_file}...")

    dzs = open(diarization_file).read().splitlines()
    groups_array = []
    g = []
    last_end = 0

    for d in dzs:
        if g and (g[0].split()[-1] != d.split()[-1]):
            groups_array.append(g)
            g = []

        g.append(d)

        end = re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=d)[1]
        end = millisec(end)

        # Segment engulfed by a previous segment
        if last_end > end:
            groups_array.append(g)
            g = []
        else:
            last_end = end
    if g:
        groups_array.append(g)

    # Chunk wav files in to chunks based on diarization data
    audio = AudioSegment.from_wav(audio_wav_file)
    gidx = -1

    # create chunk directory
    does_exist = os.path.exists(audio_chunks_s3_key)
    if not does_exist:
        os.makedirs(audio_chunks_s3_key)

    for g in groups_array:
        start = re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=g[0])[0]
        end = re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=g[-1])[1]
        start = millisec(start)
        end = millisec(end)
        # print(start, end)
        gidx += 1
        audio[start:end].export(audio_chunks_s3_key + str(gidx) + '.wav', format='wav')

    # print(*groups, sep='\n')
    upload_directory(audio_chunks_s3_key)
    print('Time taken for Chunking WAV is : ' + str(time.time() - fn_start))

    fn_start = time.time()
    with open(groups, 'wb') as f:
        pickle.dump(groups_array, f, protocol=pickle.HIGHEST_PROTOCOL)
        f.close()

    s3_client.upload_file(groups, BUCKET, f"{output_s3_key}/{groups}")
    # Returning Chunk Indexes, Chunk Groups and WAV Chunk Folder Path
    print('Time taken for Uploading Group File is : ' + str(time.time() - fn_start))
    return gidx, groups, audio_chunks_s3_key


chunk_wav_files()
