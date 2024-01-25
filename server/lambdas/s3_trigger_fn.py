#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import json
import os
import urllib.parse
import uuid

import boto3

import server_constants as config

print("Loading S3 Trigger Function...")

s3 = boto3.client("s3")
step_function_client = boto3.client("stepfunctions")
step_functions_arn = os.environ[config.CI_STEPS]

tableName = os.environ["UploadsTable"]
table = boto3.resource("dynamodb").Table(tableName)


def start_workflow(bucket, key, last_modified, content_type, content_length):
    response = step_function_client.start_execution(
        stateMachineArn=step_functions_arn,
        name=str(uuid.uuid4()),
        input=json.dumps({"bucket": bucket, "key": key}),
    )

    payload = {
        "objectKey": key,
        "inputKey": key,
        "bucketName": bucket,
        "lastModified": last_modified,
        "contentType": content_type,
        "contentLength": content_length,
        "executionArn": response["executionArn"],
        "executionStartedAt": response["startDate"].isoformat(),
    }
    table.put_item(Item=payload)
    return {
        "executionArn": response["executionArn"],
        "started": response["startDate"].isoformat(),
        "object": key,
    }


def handler(event, context):
    # print("Received event: " + json.dumps(event, indent=2))
    # Get the object from the event and show its content type
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )

    try:
        s3_object = s3.get_object(Bucket=bucket, Key=key)
        last_modified = s3_object["LastModified"].isoformat()
        content_type = s3_object["ContentType"]
        content_length = s3_object["ContentLength"]
        object_key = key + ":" + s3_object["LastModified"].strftime('%s')
        object_from_table = table.get_item(
            Key={"objectKey": key},
            ConsistentRead=True,
        )

        if "Item" not in object_from_table:
            return start_workflow(bucket, key, last_modified, content_type, content_length)
        else:
            item = object_from_table["Item"]
            existing_item_last_modified = item["lastModified"]
            if last_modified != existing_item_last_modified:
                print(f"Starting {key} again as its uploaded again!!!")
                return start_workflow(bucket, key, last_modified, content_type, content_length)
            else:
                print(f"{key} is already getting processed")
        return {
            "object": key,
            "status": f"{key} is already getting processed"
        }
    except Exception as e:
        print(e)
        print(
            "Error while getting object {}{} and trigger CI workflow.".format(
                key, bucket
            )
        )
        raise e
