#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import os
import boto3
import fleep

print("Loading Check Input Function...")
s3_client = boto3.client("s3")


def handler(event, context):
    # Get the object from the event and show its content type
    s3_bucket = event["bucket"]
    key = event["key"]
    try:
        response = s3_client.get_object(Bucket=s3_bucket, Key=key)
        content_type = response["ContentType"]
        # Create all input variables that are required
        head, file_name = os.path.split(key)

        file_name_without_extn = os.path.splitext(os.path.basename(key))[0]
        # job_id = str(uuid.uuid4())
        job_id = file_name_without_extn
        output_key = 'output/' + job_id
        chat_transcript_file_path = file_name_without_extn + ".original.txt"

        # Download original transcript file
        temp_file_path = "/tmp/" + file_name_without_extn
        s3_client.download_file(
            s3_bucket,
            key,
            temp_file_path,
        )

        with open(temp_file_path, "rb") as file:
            info = fleep.get(file.read(128))

        print("File Type as detected by Fleep")
        print(info.type)
        print(info.extension)
        print(info.mime)

        if info.extension:
            content_type = info.extension[0]

        if content_type == 'mp3' or content_type == "audio/mp3":
            wav_file_name = file_name_without_extn + ".wav"
            event['audio_wav_file'] = wav_file_name

        elif content_type == 'wav' or content_type == "audio/wav":
            # Copying WAV File to output folder
            wav_file_name = file_name_without_extn + ".wav"
            s3_client.upload_file(temp_file_path, s3_bucket, f"{output_key}/{wav_file_name}")
            event['audio_wav_file'] = wav_file_name

        elif content_type == 'text/plain':
            s3_client.upload_file(temp_file_path, s3_bucket, f"{output_key}/{chat_transcript_file_path}")

        else:
            return {
                "event": event,
                "status": "FAILED",
                "content_type": content_type
            }

        event['content_type'] = content_type
        event['input_file'] = file_name_without_extn
        event['output_s3_key'] = output_key
        event['audio_chunks_s3_key'] = output_key + "/chunks/"
        event['txt_chunks_s3_key'] = output_key + "/txt_chunks/"
        event['diarization_file'] = file_name_without_extn + '.diarization.txt'
        event['output_file'] = file_name_without_extn + ".json"
        event['original_transcription_file'] = chat_transcript_file_path
        event['dominant_language_code'] = 'original'
        event['dominant_language'] = 'original'
        event['groups'] = 'groups'
        event['diarization_complete'] = False
        event['diarization_retry_count'] = 0
        event['transcription_complete'] = False
        event['transcription_retries'] = 0

        return {
            "event": event,
            "status": "SUCCEEDED",
            "content_type": content_type
        }
    except Exception as e:
        print(e)
        print(
            "Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as "
            "this function.".format(key, s3_bucket)
        )
        raise e
