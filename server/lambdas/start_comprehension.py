#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import os

import boto3
from botocore.exceptions import ClientError

print("Loading Start Comprehend Jobs...")
comprehend_client = boto3.client(service_name="comprehend")


def detect_sentiment(dominant_language_code, comprehend_job_role, s3_uri, s3_output_uri):
    """
    Detects the overall sentiment expressed in a document. Sentiment can
    be positive, negative, neutral, or a mixture.

    :param comprehend_job_role:
    :param dominant_language_code:
    :param s3_uri: Input bucket URI
    :param s3_output_uri: Output bucket URI
    :return: The Job response that returns sentiments along with their confidence scores.
    """
    try:
        response = comprehend_client.start_sentiment_detection_job(
            LanguageCode=dominant_language_code,
            DataAccessRoleArn=comprehend_job_role,
            InputDataConfig={
                "S3Uri": s3_uri,
                "InputFormat": "ONE_DOC_PER_LINE"},
            OutputDataConfig={
                "S3Uri": s3_output_uri
            },
        )
        print("Started topic modeling job %s.", response["JobId"])
    except ClientError:
        print("Couldn't start topic modeling job.")
        raise
    else:
        return response


def detect_entities(dominant_language_code, comprehend_job_role, s3_uri, s3_output_uri):
    """
    Detects the overall sentiment expressed in a document. Sentiment can
    be positive, negative, neutral, or a mixture.

    :param comprehend_job_role:
    :param dominant_language_code:
    :param s3_uri: Input bucket URI:
    :param s3_output_uri: Output bucket URI:
    :return: The Job response that returns sentiments along with their confidence scores.
    """
    try:
        response = comprehend_client.start_entities_detection_job(
            LanguageCode=dominant_language_code,
            DataAccessRoleArn=comprehend_job_role,
            InputDataConfig={
                "S3Uri": s3_uri,
                "InputFormat": "ONE_DOC_PER_LINE"},
            OutputDataConfig={
                "S3Uri": s3_output_uri
            },
        )
        print("Started topic modeling job %s.", response["JobId"])
    except ClientError:
        print("Couldn't start topic modeling job.")
        raise
    else:
        return response


def handler(e, context):

    event = e["event"]
    s3_bucket = event["bucket"]
    output_key = event["output_s3_key"]
    original_transcription_file = event["original_transcription_file"]
    language = event["dominant_language_code"]

    comprehend_job_role = os.environ["comprehend_job_role"]
    sentiment_file_name = "sentiment"
    entities_file_name = "entities"

    # Hardcoding this language as we are using translated transcript
    language = "en"

    s3_uri = f"s3://{s3_bucket}/{output_key}/{original_transcription_file}"
    s3_sentiment_output_uri = f"s3://{s3_bucket}/{output_key}/{sentiment_file_name}"
    s3_entities_output_uri = f"s3://{s3_bucket}/{output_key}/{entities_file_name}"

    sentiment_response = detect_sentiment(
        language, comprehend_job_role, s3_uri, s3_sentiment_output_uri
    )
    event["sentiment_job_id"] = sentiment_response['JobId']

    entities_response = detect_entities(
        language, comprehend_job_role, s3_uri, s3_entities_output_uri
    )
    event["entities_job_id"] = entities_response['JobId']

    return {
        "event": event,
        "status": "SUCCEEDED",
    }
