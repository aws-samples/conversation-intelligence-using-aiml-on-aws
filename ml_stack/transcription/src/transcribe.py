#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

from __future__ import print_function

import glob
import gzip
import json
import os
import uuid
from urllib.parse import urlparse

import boto3
import flask
import torch
from faster_whisper import WhisperModel
from flask import request, json


nfs_path = "/tmp/"

os.environ['HF_HOME'] = nfs_path+'/huggingface'
os.environ['HF_DATASETS_CACHE'] = nfs_path+'/huggingface/datasets'
os.environ['TRANSFORMERS_CACHE'] = nfs_path+'/huggingface/models'

prefix = "/opt/ml/"
model_size = "large-v2"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class TranslateService(object):
    model = None

    @classmethod
    def get_model(cls):
        if cls.model == None:
            cls.model = WhisperModel(model_size, device="cuda", compute_type="float16")
        return cls.model

    @classmethod
    def get_file_info(cls, model, voice_file_name: str, task: str) -> dict:
        """Perform required task for given file"""
        segments, info = model.transcribe(voice_file_name, beam_size=5, task=task)
        text = ' '
        for segment in segments:
            text += segment.text
        return {
            'text': text,
            'language': info.language,
            'language_probability': info.language_probability,
        }

    @classmethod
    def process_chunks(cls, model, audio_chunk_path: str, task: str, chunk_prefix: str) -> dict:
        """Process all audio files in given path & provide information as a dict.
        
        Sample:
            audio_chunk_path structure
                /tmp/advdsd/
                    0.wav
                    1.wav
                    2.wav
            task - `translate`
            chunk_prefix - `translated_`
        
        Output:
            {
                'translated_0': {'text': 'Hi', 'language': 'en', 'language_probability': 0.9},
                'translated_1': {'text': 'How are you?', 'language': 'en', 'language_probability': 0.89},
                'translated_2': {'text': 'I am good', 'language': 'en', 'language_probability': 0.85}
            }
        
        """
        voice_files = list_files_in_directory(audio_chunk_path)
        chunk_wise_data_map = {}
        for file in voice_files:
            chunk_name = file.split('/')[-1].replace('.wav', '')
            chunk_wise_data_map[f'{chunk_prefix}{chunk_name}'] = cls.get_file_info(model, file, task)
        return chunk_wise_data_map

    @classmethod
    def transcribe(cls, chunks_path, task, s3_output_uri) -> str:
        """Process all audio files in given path & upload the output as json gzip file in provided S3 location"""
        model = cls.get_model()
        transcription_info, translation_info = {}, {}

        if task == 'translate_transcribe':
            transcription_info = cls.process_chunks(model, chunks_path, 'transcribe', 'original_')
            translation_info = cls.process_chunks(model, chunks_path, 'translate', 'translated_')
        elif task == 'translate':
            translation_info = cls.process_chunks(model, chunks_path, 'translate', 'translated_')
        else:
            # By default perform transcribe task
            transcription_info = cls.process_chunks(model, chunks_path, 'transcribe', 'original_')

        # Prepare final data to be dumped to s3 as a gzip file
        final_data = {'transcription_info': transcription_info, 'translation_info': translation_info}
        dump_file = f'{nfs_path}op_{generate_random_string()}.json.gz'
        with gzip.open(dump_file, 'wb') as f:
            f.write(json.dumps(final_data, ensure_ascii=False).encode('utf-8'))

        upload_file_to_s3(dump_file, s3_output_uri)
        return 'OK'


app = flask.Flask(__name__)


def generate_random_string() -> str:
    return uuid.uuid4().hex


def upload_file_to_s3(file_path, s3_uri):
    # Parse the S3 URI to extract the bucket name and the key (filename)
    parsed_uri = urlparse(s3_uri)
    bucket_name = parsed_uri.netloc
    key = parsed_uri.path.lstrip('/')

    # Initialize a Boto3 S3 client with AWS credentials
    s3 = boto3.client('s3')

    try:
        # Upload the file to S3
        s3.upload_file(file_path, bucket_name, key)
        print(f"Uploaded {file_path} to {s3_uri}")
    except Exception as e:
        print(f"Error: {e}")


def download_s3_bucket_from_uri(s3_uri, local_folder):
    # Parse the S3 URI to extract the bucket name and key prefix
    parsed_uri = urlparse(s3_uri)
    bucket_name = parsed_uri.netloc
    key_prefix = parsed_uri.path.lstrip('/')

    # Initialize a Boto3 S3 client
    s3 = boto3.client('s3')

    # List objects in the S3 bucket with the specified key prefix
    objects = s3.list_objects_v2(Bucket=bucket_name, Prefix=key_prefix)

    # Check if the local folder exists, if not, create it
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)

    # Download each object from the S3 bucket to the local folder
    object_count = 0
    for obj in objects.get('Contents', []):
        # Construct the local file path by removing the key prefix
        local_file_path = os.path.join(local_folder, obj['Key'].replace(key_prefix, '', 1))

        # Download the file from S3
        s3.download_file(bucket_name, obj['Key'], local_file_path)
        print(f"Downloaded: {obj['Key']} to {local_file_path}")
        object_count += 1
    return object_count



def clear_directory(path: str):
    """Delete directory & all its contents from given path"""
    try:
        for file in list_files_in_directory(path):
            os.remove(file)
    except FileNotFoundError:
        pass
    except Exception:
        pass


def list_files_in_directory(directory):
    file_list = glob.glob(os.path.join(directory, '*'))
    return file_list


@app.route("/ping", methods=["GET"])
def ping():
    return {"message": "ok"}


@app.route("/invocations", methods=["POST"])
def transcribe():
    res = None
    text = request.data.decode("utf-8")
    data = json.loads(text)

    input_location = data['input_location']
    task = data['task']
    output_location = data['output_location']
    print(f'Input chunks location: {input_location}')

    chunk_folder_path = f'{nfs_path}{generate_random_string()}'
    objects_count = download_s3_bucket_from_uri(input_location, chunk_folder_path)
    print(f'Downloaded {objects_count} files from S3')

    res = TranslateService.transcribe(chunk_folder_path, task, output_location)    
    print(f'Completed {task} for {input_location}')

    # Clear storage
    clear_directory(chunk_folder_path)

    return flask.Response(response=res, status=200, mimetype='text/plain')

