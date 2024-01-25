#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import boto3
from urllib.parse import urlparse

print("Checking if sentiment job is complete...")
s3_client = boto3.client("s3")
comprehend_client = boto3.client(service_name="comprehend")


def handler(e, context):
    event = e["event"]
    sentiment_job_id = event["sentiment_job_id"]

    describe_job_response = comprehend_client.describe_sentiment_detection_job(
        JobId=sentiment_job_id
    )
    job_status = describe_job_response["SentimentDetectionJobProperties"]["JobStatus"]
    check_sentiment_job_status = True if job_status == "COMPLETED" else False

    if check_sentiment_job_status:
        sentiment_output_uri_o = urlparse(
            describe_job_response['SentimentDetectionJobProperties']['OutputDataConfig']['S3Uri'],
            allow_fragments=False
        )
        event['sentiment_job_output_file'] = sentiment_output_uri_o.path[1:]

        # print(sentiment_file_name)
        # tmp_file = '/tmp/'+sentiment_file_name
        # s3_client.download_file(sentiment_output_uri_o.netloc, sentiment_output_uri_o.path[1:], tmp_file)
        # print(f"Downloaded {tmp_file}")

    print(f"Sentiment Detection Job {sentiment_job_id} is {check_sentiment_job_status}!!")
    event['sentiment_job_status'] = check_sentiment_job_status

    return {
        "event": event,
        "status": "SUCCEEDED",
    }
