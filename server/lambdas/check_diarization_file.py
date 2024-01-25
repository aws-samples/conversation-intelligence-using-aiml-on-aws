#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import urllib

import boto3
from botocore.exceptions import ClientError
import server_constants as cfg

print("Loading Check Diarization Files...")
s3_client = boto3.client("s3")
tmp_prefix = "/tmp/"
max_retry_attempt = cfg.LAMBDA_MAX_RETRIES


def handler(e, context):
    # Get the object from the event and show its content type
    event = e["event"]
    s3_bucket = event["bucket"]
    output_key = event['output_s3_key']
    diarization_file = event["diarization_file"]
    retry_count = int(event["diarization_retry_count"])
    event["diarization_retry_count"] = retry_count + 1
    try:
        download_location = event["diarization_out_path"]
        tmp_diarization_file = "/tmp/" + diarization_file
        output_url = urllib.parse.urlparse(download_location)
        download_bucket = output_url.netloc
        download_key = output_url.path[1:]
        upload_file_key = f"{output_key}/{diarization_file}"
        try:
            s3_client.download_file(download_bucket, download_key, tmp_diarization_file)
            s3_client.upload_file(tmp_diarization_file, s3_bucket, upload_file_key)
            event["diarization_complete"] = True
        except ClientError as e:
            if retry_count > max_retry_attempt:
                with open(tmp_diarization_file, "w") as empty_file:
                    empty_file.write("-")
                empty_file.close()
                s3_client.upload_file(tmp_diarization_file, s3_bucket, upload_file_key)
                event["diarization_complete"] = True
                print(f"Diarization file ready {output_key}{diarization_file}.txt")
                return {
                    "event": event,
                    "status": "SUCCEEDED",
                }
            print(f"Diarization file not ready {output_key}{diarization_file}.txt")
        return {
            "event": event,
            "status": "SUCCEEDED",
        }
    except Exception as e:
        print(e)
        print(
            "Error getting object {}. Make sure they exist and your bucket is in the same region as "
            "this function.".format(diarization_file)
        )
        raise e
