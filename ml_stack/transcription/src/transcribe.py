#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

from __future__ import print_function

import glob
import json
import os
import random
import string
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
    def transcribe(cls, chunks_path, task, s3_output_uri):
        model = cls.get_model()
        temp_loc = generate_random_string(length=20)
        if not os.path.exists(nfs_path + temp_loc):
            os.makedirs(nfs_path + temp_loc)

        if(task=="translate_transcribe"):
            print("Translation+Transcribe task")
            voice_files = list_files_in_directory(chunks_path)

            for voice_file in voice_files:    
                result = " "
                print(voice_file)
                segments, info = model.transcribe(voice_file, beam_size=5, task="translate")
                
                for segment in segments:
                    result += segment.text
                                
                out_file = nfs_path + temp_loc + '/'+ extract_filename_without_extension(voice_file)+'.translated.txt'
                with open(out_file, 'w') as file:
                    file.write(result)

                upload_file_to_s3(out_file, s3_output_uri)
                segments, info = model.transcribe(voice_file, beam_size=5)

                for segment in segments:
                    result +=segment.text

                out_file = nfs_path + temp_loc + '/'+ extract_filename_without_extension(voice_file)+'.original.txt'
                with open(out_file, 'w') as file:
                    file.write(result)

                upload_file_to_s3(out_file, s3_output_uri)

        elif(task=="translate"):
            print("Translation task only")
            voice_files = list_files_in_directory(chunks_path)

            for voice_file in voice_files:    
                result = " "
                print(voice_file)
                segments, info = model.transcribe(voice_file, beam_size=5, task="translate")
                
                for segment in segments:
                    result += segment.text
                                
                out_file = nfs_path + temp_loc + '/'+ extract_filename_without_extension(voice_file)+'.translated.txt'
                with open(out_file, 'w') as file:
                    file.write(result)

                upload_file_to_s3(out_file, s3_output_uri)

        else:
            print("Transcribe task only")
            voice_files = list_files_in_directory(chunks_path)

            for voice_file in voice_files:
                result = " " 
                print(voice_file)
                segments, info = model.transcribe(voice_file, beam_size=5)
                for segment in segments:
                    result += segment.text

                out_file = nfs_path + temp_loc + '/'+ extract_filename_without_extension(voice_file)+'.original.txt'
                with open(out_file, 'w') as file:
                    file.write(result)

                upload_file_to_s3(out_file, s3_output_uri)

        return "OK"


app = flask.Flask(__name__)


def generate_random_string(length=20):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


def extract_filename_without_extension(file_path):
    base_name = os.path.basename(file_path)
    filename_without_extension, _ = os.path.splitext(base_name)
    return filename_without_extension


def upload_file_to_s3(file_path, s3_uri):
    # Parse the S3 URI to extract the bucket name and the key (filename)
    parsed_uri = urlparse(s3_uri)
    bucket_name = parsed_uri.netloc
    key = parsed_uri.path.lstrip('/')

    # Use the local file's name as the key (filename) in S3
    key = os.path.join(key, os.path.basename(file_path))

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
    for obj in objects.get('Contents', []):
        # Construct the local file path by removing the key prefix
        local_file_path = os.path.join(local_folder, obj['Key'].replace(key_prefix, '', 1))

        # Download the file from S3
        s3.download_file(bucket_name, obj['Key'], local_file_path)
        print(f"Downloaded: {obj['Key']} to {local_file_path}")


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
    print(f"Input chunks location: {input_location}")

    chunk_folder_path = nfs_path+generate_random_string(20)
    download_s3_bucket_from_uri(input_location, chunk_folder_path)
    res = TranslateService.transcribe(chunk_folder_path, task, output_location)    
    print(f"Completed {task} for {input_location}")
    return flask.Response(response=res, status=200, mimetype="text/plain")

