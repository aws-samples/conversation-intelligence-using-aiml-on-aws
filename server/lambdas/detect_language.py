#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import boto3
from botocore.exceptions import ClientError

print("Loading Detect Language...")
s3_client = boto3.client("s3")
comprehend_client = boto3.client(service_name="comprehend")


def detect_languages(text_file_path):
    """
    Detects languages used in a document.

    :param text_file_path: The document to inspect.
    :return: The list of languages along with their confidence scores.
    """
    try:
        with open(text_file_path) as f:
            text = f.read()

        response = comprehend_client.detect_dominant_language(Text=text)
        languages = response["Languages"]
    except ClientError:
        print("Couldn't detect languages.")
        raise
    else:
        return languages


def handler(e, context):
    event = e["event"]
    s3_bucket = event["bucket"]
    output_key = event["output_s3_key"]
    original_transcription_file = event["original_transcription_file"]
    temp_file_path = "/tmp/" + original_transcription_file

    s3_client.download_file(s3_bucket, f"{output_key}/{original_transcription_file}", temp_file_path)

    languages = detect_languages(temp_file_path)
    dominant_language_code = languages[0]["LanguageCode"]
    supported_languages = {
        "en": "english",
        "hi": "hindi",
        "ta": "tamil",
        "te": "telugu",
        "mr": "marathi",
        "bn": "bengali",
        "gu": "gujarati",
        "kn": "kannada",
        "ml": "malayalam",
        "pa": "punjabi",
        "ur": "urdu",
    }

    event["dominant_language_code"] = dominant_language_code
    event["dominant_language"] = supported_languages[dominant_language_code]

    return {
        "event": event,
        "status": "SUCCEEDED",
    }
