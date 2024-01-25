#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import json
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr

print("Loading List Conversation Function...")

s3 = boto3.client("s3")
step_function_client = boto3.client("stepfunctions")

tableName = os.environ["UploadsTable"]
table = boto3.resource("dynamodb").Table(tableName)


# Does quasi the same things as json.loads from here: https://pypi.org/project/dynamodb-json/
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def handler(event, context):
    # Get the object from the event and show its content type
    try:
        body = table.scan(
            FilterExpression=Attr('executionCompletedAt').exists()
        )
        items = body['Items']
        payload = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps(items, cls=JSONEncoder)
        }
        return payload
    except Exception as e:
        print("Error while getting list from the uploads table")
        print(e)
        return []