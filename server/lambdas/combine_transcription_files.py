#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import boto3
import gzip
import json
import pickle
import re
import server_constants
import time

print("Loading Combing Transcription Files...")
s3_client = boto3.client("s3")
tmp_prefix = '/tmp/'

def combine_txt_transcriptions(TRANSCRIPTION_FILE_NAME, groups, txt_chunks_s3_key, language, BUCKET, output_s3_key):
    fn_start = time.time()
    gidx = -1

    # Download Group
    tmp_groups = tmp_prefix + groups
    s3_client.download_file(BUCKET, f"{output_s3_key}/{groups}", tmp_groups)
    group_file = open(tmp_groups, "rb")
    groups = pickle.load(group_file)

    local_transcription_file = tmp_prefix + TRANSCRIPTION_FILE_NAME
    text_file = open(local_transcription_file, "w")

    # Download transcription model output file
    tmp_output_path = tmp_prefix + 'data.json.gz'
    s3_client.download_file(BUCKET, f"{output_s3_key}/{txt_chunks_s3_key}", tmp_output_path)
    with gzip.open(tmp_output_path, 'r+') as file:
        model_output = json.load(file)
    
    is_translation = language not in {'original', 'en'}
    original_txt_prefix, translated_txt_prefix = 'original_', 'translated_'

    for group in groups:
        speaker = group[0].split()[-1]
        if speaker not in server_constants.SPEAKERS:
            continue
        speaker_str = server_constants.SPEAKERS[speaker]
        speaker_str = re.sub("[!^:(),']", "", str(speaker))
        gidx += 1

        original_text_info = model_output.get(f'{original_txt_prefix}{gidx}', {})
        translated_text_info = model_output.get(f'{translated_txt_prefix}{gidx}', {})

        chunk_info = translated_text_info if is_translation else original_text_info
        chunk_txt = re.sub(r'[!\n]', '', chunk_info.get('text', '')).strip()

        if not chunk_txt:
            continue

        chunk_str = speaker_str + ":" + str(chunk_txt)
        res = re.sub(r"[!\n]", "", chunk_str)
        text_file.write(f'{res}\n')

    group_file.close()
    text_file.close()

    s3_client.upload_file(
        local_transcription_file,
        BUCKET,
        f"{output_s3_key}/{TRANSCRIPTION_FILE_NAME}",
    )
    print(
        "Time taken for combining all transcriptions : " + str(time.time() - fn_start)
    )
    return TRANSCRIPTION_FILE_NAME


def get_language(language):
    return "en" if language == "original" else language


def handler(e, context):
    # Get the object from the event and show its content type
    event = e["event"]
    BUCKET = event["bucket"]
    output_s3_key = event["output_s3_key"]
    groups = event["groups"]
    txt_chunks_s3_key = event["txt_chunks_s3_key"]
    TRANSCRIPTION_FILE_NAME = str(event["original_transcription_file"])
    language = event["dominant_language_code"]

    if language != 'original' and language != 'en':
        TRANSCRIPTION_FILE_NAME = TRANSCRIPTION_FILE_NAME.replace('original', 'translated')
        TRANSCRIPTION_FILE_NAME = TRANSCRIPTION_FILE_NAME.replace('en', 'translated')

    try:
        combine_txt_transcriptions(TRANSCRIPTION_FILE_NAME, groups, txt_chunks_s3_key, language, BUCKET, output_s3_key)
        return {"event": event, "status": "SUCCEEDED"}

    except Exception as e:
        print(e)
        print(
            "Error getting object {}. Make sure they exist and your bucket is in the same region as "
            "this function.".format(TRANSCRIPTION_FILE_NAME)
        )
        raise e
