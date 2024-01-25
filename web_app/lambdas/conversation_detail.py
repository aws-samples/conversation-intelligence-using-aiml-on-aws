#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import json
import os
from decimal import Decimal

import boto3

print("Loading Conversation Detail Function...")

s3_client = boto3.client("s3")
tableName = os.environ["UploadsTable"]
table = boto3.resource("dynamodb").Table(tableName)
s3_resource = boto3.resource("s3")


# Does quasi the same things as json.loads from here: https://pypi.org/project/dynamodb-json/
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def get_response():
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        },
    }

def get_err_response():
    return {
        'statusCode': 500,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        },
    }


def create_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except Exception as e:
        print(e)
        print("Error while getting list from the uploads table")
        return None

    # The response contains the presigned URL
    return response


def handler(event, context):
    key = event['path'].replace("/details/", "")
    payload = get_response()
    # Get the object from the event and show its content type
    try:
        object_from_table = table.get_item(
            Key={"objectKey": 'input/' + key},
            ConsistentRead=True,
        )

        if "Item" in object_from_table.keys():
            item = object_from_table["Item"]
            s3_bucket = item['bucketName']
            output_key = item['outputFile']
            s3_obj = s3_client.get_object(Bucket=s3_bucket, Key=output_key)
            s3_data = s3_obj['Body'].read().decode('utf-8')
            pre_signed_url = create_presigned_url(s3_bucket, item['key'])
            payload["body"] = s3_data

            try:
                s3_client_data = json.loads(s3_data)
                s3_client_data["ConversationAnalytics"]["SourceInformation"]["TranscribeJobInfo"]["MediaFileUri"] = pre_signed_url
                payload["body"] = json.dumps(s3_client_data, ensure_ascii=False).encode('utf8')
            except Exception as e:
                print(e)
                print("Error while getting s3 media file")

        return payload
    except Exception as e:
        print(e)
        print("Error while getting list from the uploads table")
        return get_err_response()
