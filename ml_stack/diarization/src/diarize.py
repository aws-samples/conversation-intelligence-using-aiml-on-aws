#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

from __future__ import print_function

import json
import os
import random
import string
import time

import boto3
import flask
import torch
from flask import request
from pyannote.audio import Audio
from pyannote.audio import Pipeline

nfs_path = "/tmp/"

os.environ['HF_HOME'] = nfs_path+'/huggingface'
os.environ['HF_DATASETS_CACHE'] = nfs_path+'/huggingface/datasets'
os.environ['TRANSFORMERS_CACHE'] = nfs_path+'/huggingface/models'
os.environ['PYANNOTE_CACHE'] = nfs_path+'/huggingface'
hf_auth_token = os.environ.get("HF_AUTH_TOKEN", "")
diarization_max_speakers = int(os.environ.get("DZ_MAX_SPEAKERS", 2))

prefix = "/opt/ml/"
model_path = os.path.join(prefix, "model")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# spacermilli is used to compute overlaps between conversation
# to minize loss due to interruptions or switching between speakers
spacermilli = 2000
# This is constraining the whole process to two speakers.
# Need to change if the solution should support more speakers
speakers = {'SPEAKER_00': ('Agent',), 'SPEAKER_01': ('Customer',)}
app = flask.Flask(__name__)


def generate_random_string(length=20):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


def read_json_file(file_path):
    try:
        with open(file_path, 'r') as json_file:
            # data = json.load(json_file)
            data = json.loads(json_file.read())
            return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def download_s3_file(s3_uri, local_path):
    try:
        # Parse the S3 URI
        s3_uri_parts = s3_uri.split('/')
        if len(s3_uri_parts) < 4:
            print("Invalid S3 URI format. It should be 's3://bucket_name/key_name'")
            return

        bucket_name = s3_uri_parts[2]
        key_name = "/".join(s3_uri_parts[3:])

        # Create a Boto3 S3 client
        s3_client = boto3.client('s3')

        # Download the file from S3
        s3_client.download_file(bucket_name, key_name, local_path)
        print(f"File downloaded to {local_path}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def diarization(wav_file_path):
    print(f"Starting Speaker diarization of {wav_file_path}")
    fn_start = time.time()
    
    pipeline = Pipeline.from_pretrained('pyannote/speaker-diarization-3.0',
                                        use_auth_token=hf_auth_token).to(device)
    io = Audio(mono='downmix', sample_rate=16000)
    waveform, sample_rate = io(wav_file_path)
    dz = pipeline({"waveform": waveform, "sample_rate": sample_rate}, max_speakers=diarization_max_speakers)
    diarization_file_path = wav_file_path.replace('.wav', '') + '_diarization.txt'

    with open(diarization_file_path, "w") as text_file:
        text_file.write(str(dz))

    print(f'Time taken for Speaker Diarization of {wav_file_path} is : {str(time.time() - fn_start)}')
    return diarization_file_path


@app.route("/ping", methods=["GET"])
def ping():
    return {"message": "ok"}


@app.route("/invocations", methods=["POST"])
def diarize():
    res = None
    print(f"Content type: {flask.request.content_type}")
    text = request.data.decode("utf-8")
    data = json.loads(text)

    input_location = data['input_location']
    task = data['task']

    input_audio_file_name = nfs_path+generate_random_string(20)+'.wav'
    download_s3_file(input_location, input_audio_file_name)

    diarization_file_path = diarization(input_audio_file_name)
    print("Diarizatio Completed, result path is:", diarization_file_path)
    result_file = open(diarization_file_path, "r")
    res = result_file.read()
    result_file.close()

    return flask.Response(response=res, status=200, mimetype="text/plain")

