#!/bin/bash

#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

from pydub import AudioSegment

import logging
import os
import sys
import time
import boto3

# Getting S3 File attributes from previous step
BUCKET = os.environ.get("BUCKET", "")
KEY = os.environ.get("KEY", "")
output_s3_key = os.environ.get("output_s3_key", "")
audio_wav_file = os.environ.get("audio_wav_file", "")

# Configuring Logger to DEBUG
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger()
logging.info(f"Converting {KEY} from {BUCKET} to WAV...")

s3_client = boto3.client("s3")

# Constants required for entire workflow
spacer_milli = 2000


# Convert mp3 file to wav format. We are returning WAV file path
def convert_mp3_to_wav(s3_bucket, key):
    fn_start = time.time()
    head, mp3_file_name = os.path.split(key)
    # Download file from S3 bucket locally to convert to wav

    s3_client.download_file(s3_bucket, key, mp3_file_name)
    logging.info(f"Downloaded {KEY} from {BUCKET}...")

    # Converting to WAV Format
    spacer = AudioSegment.silent(duration=spacer_milli)
    audio = AudioSegment.from_mp3(mp3_file_name)
    audio = spacer.append(audio, crossfade=0)
    logging.info(f"Creating WAV file {audio_wav_file}")
    audio.export(audio_wav_file, format="wav")

    logging.info("Time taken for converting to WAV is : " + str(time.time() - fn_start))

    # Copying original file to output dir
    s3_client.upload_file(mp3_file_name, s3_bucket, f"{output_s3_key}/{mp3_file_name}")
    s3_client.upload_file(audio_wav_file, s3_bucket, f"{output_s3_key}/{audio_wav_file}")
    logging.info(f"Uploaded {audio_wav_file} from {BUCKET}...")
    os.environ['audio_wav_file'] = audio_wav_file
    return audio_wav_file


wav_file = convert_mp3_to_wav(BUCKET, KEY)
