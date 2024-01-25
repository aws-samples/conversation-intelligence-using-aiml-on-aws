#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import json
import os

import boto3

print("Loading Gen AI Query Fn...")
s3_client = boto3.client("s3")
ssm_client = boto3.client("ssm")
tableName = os.environ["UploadsTable"]
table = boto3.resource("dynamodb").Table(tableName)
s3_resource = boto3.resource("s3")

# Defaults
AWS_REGION = (
    os.environ["AWS_REGION_OVERRIDE"]
    if "AWS_REGION_OVERRIDE" in os.environ
    else os.environ["AWS_REGION"]
)
ENDPOINT_URL = os.environ.get(
    "ENDPOINT_URL", f"https://bedrock-runtime.{AWS_REGION}.amazonaws.com"
)
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))
MODEL_ID = str(os.getenv("MODEL_ID", "anthropic.claude-v2"))

DEFAULT_MAX_TOKENS = 1024
SUCCESS = "SUCCESS"
FAILED = "FAILED"
bedrock_client = None
SSM_LLM_CHATBOT_NAME = "ci_chatbot_prompt"


def get_request_body(modelId, parameters, prompt):
    provider = modelId.split(".")[0]
    request_body = None
    if provider == "anthropic":
        request_body = {"prompt": prompt, "max_tokens_to_sample": DEFAULT_MAX_TOKENS}
        request_body.update(parameters)
    elif provider == "ai21":
        request_body = {"prompt": prompt, "maxTokens": DEFAULT_MAX_TOKENS}
        request_body.update(parameters)
    elif provider == "amazon":
        textGenerationConfig = {"maxTokenCount": DEFAULT_MAX_TOKENS}
        textGenerationConfig.update(parameters)
        request_body = {
            "inputText": prompt,
            "textGenerationConfig": textGenerationConfig,
        }
    else:
        raise Exception("Unsupported provider: ", provider)
    return request_body


def get_generate_text(modelId, response):
    provider = modelId.split(".")[0]
    generated_text = None
    if provider == "anthropic":
        response_body = json.loads(response.get("body").read().decode())
        generated_text = response_body.get("completion")
    elif provider == "ai21":
        response_body = json.loads(response.get("body").read())
        generated_text = response_body.get("completions")[0].get("data").get("text")
    elif provider == "amazon":
        response_body = json.loads(response.get("body").read())
        generated_text = response_body.get("results")[0].get("outputText")
    else:
        raise Exception("Unsupported provider: ", provider)
    return generated_text


def get_bedrock_client():
    client = boto3.client(
        service_name="bedrock-runtime",
        region_name=AWS_REGION,
        endpoint_url=ENDPOINT_URL,
    )
    return client


def call_llm(parameters, prompt):
    modelId = MODEL_ID
    body = get_request_body(modelId, parameters, prompt)
    client = boto3.client(
        service_name="bedrock-runtime",
        region_name=AWS_REGION,
        endpoint_url=ENDPOINT_URL,
    )
    response = client.invoke_model(
        body=json.dumps(body),
        modelId=modelId,
        accept="application/json",
        contentType="application/json",
    )
    generated_text = get_generate_text(modelId, response)
    return generated_text


def get_bedrock_request_body(modelId, parameters, prompt):
    provider = modelId.split(".")[0]
    request_body = None
    if provider == "anthropic":
        request_body = {"prompt": prompt, "max_tokens_to_sample": MAX_TOKENS}
        request_body.update(parameters)
    elif provider == "ai21":
        request_body = {"prompt": prompt, "maxTokens": MAX_TOKENS}
        request_body.update(parameters)
    elif provider == "amazon":
        textGenerationConfig = {"maxTokenCount": MAX_TOKENS}
        textGenerationConfig.update(parameters)
        request_body = {
            "inputText": prompt,
            "textGenerationConfig": textGenerationConfig,
        }
    else:
        raise Exception("Unsupported provider: ", provider)
    return request_body


def get_bedrock_generate_text(modelId, response):
    provider = modelId.split(".")[0]
    generated_text = None
    if provider == "anthropic":
        response_body = json.loads(response.get("body").read().decode())
        generated_text = response_body.get("completion")
    elif provider == "ai21":
        response_body = json.loads(response.get("body").read())
        generated_text = response_body.get("completions")[0].get("data").get("text")
    elif provider == "amazon":
        response_body = json.loads(response.get("body").read())
        generated_text = response_body.get("results")[0].get("outputText")
    else:
        raise Exception("Unsupported provider: ", provider)
    generated_text = generated_text.replace("```", "")
    return generated_text


def call_bedrock(parameters, prompt):
    global bedrock_client
    modelId = MODEL_ID
    body = get_bedrock_request_body(modelId, parameters, prompt)
    if bedrock_client is None:
        bedrock_client = get_bedrock_client()
    response = bedrock_client.invoke_model(
        body=json.dumps(body),
        modelId=modelId,
        accept="application/json",
        contentType="application/json",
    )
    generated_text = get_bedrock_generate_text(modelId, response)
    return generated_text


def generate_bedrock_query(prompt, transcript, question):
    # first check to see if this is one prompt, or many prompts as a json
    prompt = prompt.replace("<br>", "\n")
    prompt = prompt.replace("{transcript}", transcript)
    if question != "":
        prompt = prompt.replace("{question}", question)
    parameters = {"temperature": 0}
    generated_text = call_bedrock(parameters, prompt)
    return generated_text


def get_response():
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
        },
    }


def get_err_response():
    return {
        "statusCode": 500,
        "headers": {
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
        },
    }


def handler(event, context):
    key = event["path"].replace("/genai/", "")
    request = json.loads(event["body"])
    payload = get_response()
    query_response = ""
    try:
        object_from_table = table.get_item(
            Key={"objectKey": "input/" + key},
            ConsistentRead=True,
        )
        if "Item" in object_from_table.keys():
            item = object_from_table["Item"]
            s3_bucket = item["bucketName"]
            output_key = item["outputFile"]
            s3_obj = s3_client.get_object(Bucket=s3_bucket, Key=output_key)
            s3_data = s3_obj["Body"].read().decode("utf-8")
            s3_client_data = json.loads(s3_data)
            if "TranslatedTranscript" in s3_client_data:
                transcript_data = s3_client_data["TranslatedTranscript"]
            else:
                transcript_data = s3_client_data["RawTranscript"]
            transcript_data = "".join(transcript_data)
            llm_summarization_prompt = ssm_client.get_parameter(
                Name=SSM_LLM_CHATBOT_NAME
            )
            prompt = llm_summarization_prompt["Parameter"]["Value"]
            query_response = generate_bedrock_query(prompt, transcript_data, request["query"])
            print(f"Got response from {MODEL_ID} for {key}")
    except Exception as err:
        query_response = "An error occurred generating Bedrock query response."
        print(query_response)
        print(err)
        return get_err_response()

    payload["body"] = query_response
    return payload
