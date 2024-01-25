#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import boto3
from urllib.parse import urlparse

print("Checking if sentiment job is complete...")
s3_client = boto3.client("s3")
comprehend_client = boto3.client(service_name="comprehend")


def handler(e, context):
    event = e["event"]
    entities_job_id = event["entities_job_id"]

    describe_job_response = comprehend_client.describe_entities_detection_job(
        JobId=entities_job_id
    )
    job_status = describe_job_response["EntitiesDetectionJobProperties"]["JobStatus"]
    check_entities_job_status = True if job_status == "COMPLETED" else False

    if check_entities_job_status:
        sentiment_output_uri_o = urlparse(
            describe_job_response['EntitiesDetectionJobProperties']['OutputDataConfig']['S3Uri'],
            allow_fragments=False
        )
        event['entities_job_output_file'] = sentiment_output_uri_o.path[1:]

    print(f"Entities Detection Job {entities_job_id} is {check_entities_job_status}!!")
    event['entities_job_status'] = check_entities_job_status

    return {
        "event": event,
        "status": "SUCCEEDED",
    }
