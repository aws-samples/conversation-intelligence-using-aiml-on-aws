#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import boto3
import urllib
from botocore.exceptions import ClientError

import server_constants as cfg

print("Loading Check Transcription Files...")
s3_client = boto3.client("s3")
tmp_prefix = "/tmp/"

# This will allow the loop to wait for 40 loops * 30 seconds = 20 mins
max_retry_attempt = cfg.LAMBDA_MAX_RETRIES


def handler(e, context):
    # Get the object from the event and show its content type
    event = e["event"]
    s3_bucket = event["bucket"]
    transcription_output_uri = event["transcription_output"]
    retry_count = int(event["transcription_retries"])
    event["transcription_retries"] = retry_count + 1
    language = event["dominant_language_code"]
    try:
        retry_count = retry_count + 1
        try:
            task = "transcribe" if ((language == "original") or (language == "en")) else "translate"
            input_param_file_path = f"{tmp_prefix}{task}.json"

            output_url = urllib.parse.urlparse(transcription_output_uri)
            download_bucket = output_url.netloc
            download_key = output_url.path[1:]

            s3_client.download_file(download_bucket, download_key, input_param_file_path)
            transcription_output = open(input_param_file_path, "r")
            print(f"Transcription completed at {transcription_output_uri}")
            event['transcription_complete'] = True
            transcription_output.close()
        except ClientError as e:
            if retry_count > max_retry_attempt:
                raise e
        return {"event": event, "status": "SUCCEEDED"}
    except Exception as e:
        print(e)
        print(
            "Error getting object {}. Make sure they exist and your bucket is in the same region as "
            "this function.".format(transcription_output_uri)
        )
        raise e
