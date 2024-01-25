#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import pickle
import re
import time
import boto3
import server_constants

print("Loading Combing Transcription Files...")
s3_client = boto3.client("s3")
tmp_prefix = '/tmp/'

spacermilli = 2000
def millisec(time_str):
    spl = time_str.split(":")
    s = int((int(spl[0]) * 60 * 60 + int(spl[1]) * 60 + float(spl[2])) * 1000)
    return s


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

    for g in groups:
        shift = re.findall("[0-9]+:[0-9]+:[0-9]+\.[0-9]+", string=g[0])[0]
        # Start time in the original video
        shift = millisec(shift) - spacermilli
        shift = max(shift, 0)
        gidx += 1

        file_prefix = language
        if language != 'original' and language != 'en':
            file_prefix = "translated"
        # Download chunks locally to combine
        download_file_path = f"{txt_chunks_s3_key}{gidx}.{file_prefix}.txt"
        tmp_chunk_path = f"{tmp_prefix}{gidx}.{file_prefix}.txt"

        s3_client.download_file(BUCKET, download_file_path, tmp_chunk_path)
        captions = open(tmp_chunk_path, "r+")

        if captions:
            speaker = g[0].split()[-1]
            if speaker in server_constants.SPEAKERS:
                speaker = server_constants.SPEAKERS[speaker]
                # Removing speaker text with (), comma and other characters
                speaker_str = re.sub("[!^:(),']", "", str(speaker))
                for c in captions:
                    s = speaker_str + ":" + str(c)
                    res = re.sub(r"[!\n]", "", s)
                    text_file.write(res + "\n")
        captions.close()

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
