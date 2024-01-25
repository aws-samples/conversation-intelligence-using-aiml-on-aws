#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import os
import boto3
import json

print("Loading Diarization Function...")
s3_client = boto3.client("s3")
sagemaker_client = boto3.client("sagemaker")
sagemaker_runtime = boto3.client("sagemaker-runtime")
model_endpoint = os.environ["MODEL_ENDPOINT"]


def handler(e, context):
    # Get the object from the event and show its content type
    event = e["event"]
    s3_bucket = event["bucket"]
    key = event["key"]
    output_key = event["output_s3_key"]
    wav_file = event["audio_wav_file"]

    try:
        param_data = {
            "input_location": f"s3://{s3_bucket}/{output_key}/{wav_file}",
            "task": "Diarize"
        }
        diarization_file_suffix = "diarization_parameter.json"
        input_param_file_path = "/tmp/" + diarization_file_suffix
        with open(input_param_file_path, "w") as json_file:
            json.dump(param_data, json_file)

        diarization_param_s3_key = f"{output_key}/{diarization_file_suffix}"

        s3_client.upload_file(
            input_param_file_path, s3_bucket, diarization_param_s3_key
        )

        response = sagemaker_runtime.invoke_endpoint_async(
            EndpointName=model_endpoint,
            InputLocation=f"s3://{s3_bucket}/{diarization_param_s3_key}",
            ContentType="application/json"
        )

        output_location = response["OutputLocation"]
        event["diarization_out_path"] = output_location
        print(f"Diarization Output Location: {output_location}")
        return {"event": event, "status": "SUCCEEDED"}
    except Exception as e:
        print(e)
        print(
            "Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as "
            "this function.".format(key, s3_bucket)
        )
        raise e
