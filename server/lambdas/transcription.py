#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import json
import os

import boto3

print("Loading Transcription Function...")
s3_client = boto3.client("s3")
sagemaker_client = boto3.client("sagemaker")
sagemaker_runtime = boto3.client("sagemaker-runtime")
endpoint_name = os.environ["TRANSCRIPTION_ENDPOINT"]
tmp_prefix = "/tmp/"


def invoke_sagemaker_endpoint(payload_location):
    response = sagemaker_runtime.invoke_endpoint_async(
        EndpointName=endpoint_name,
        InputLocation=payload_location,
        ContentType="application/json",
    )
    output_location = response["OutputLocation"]
    return output_location


def handler(e, context):
    # Get the object from the event and show its content type
    event = e["event"]
    s3_bucket = event["bucket"]
    key = event["key"]
    output_key = event["output_s3_key"]
    audio_chunk_key = event["audio_chunks_s3_key"]
    txt_chunk_key = event["txt_chunks_s3_key"]
    language = event["dominant_language_code"]

    try:
        audio_chunk_uri = f"s3://{s3_bucket}/{audio_chunk_key}"
        txt_chunk_uri = f"s3://{s3_bucket}/{txt_chunk_key}"
        task = "transcribe" if ((language == "original") or (language == "en")) else "translate"
        payload = {
            "input_location": audio_chunk_uri,
            "output_location": txt_chunk_uri,
            "task": task,
        }

        input_param_file_path = f"{tmp_prefix}{task}.json"
        with open(input_param_file_path, "w") as json_file:
            json.dump(payload, json_file)

        param_file_uri = f"{output_key}/{task}.json"
        s3_client.upload_file(
            input_param_file_path, s3_bucket, param_file_uri
        )

        response_location = invoke_sagemaker_endpoint(f"s3://{s3_bucket}/{param_file_uri}")
        event["transcription_output"] = response_location
        event['transcription_complete'] = False
        event['transcription_retries'] = 0
        print(f"Started Transcription {key}")

        return {"event": event, "status": "SUCCEEDED"}
    except Exception as e:
        print(e)
        print(
            "Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as "
            "this function.".format(key, s3_bucket)
        )
        raise e
