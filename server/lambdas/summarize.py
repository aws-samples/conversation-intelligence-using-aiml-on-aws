#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import json
import os

import boto3

print("Loading Summarization Fn...")
s3_client = boto3.client("s3")
ssm_client = boto3.client("ssm")

# Defaults
AWS_REGION = (
    os.environ["AWS_REGION_OVERRIDE"]
    if "AWS_REGION_OVERRIDE" in os.environ
    else os.environ["AWS_REGION"]
)
ENDPOINT_URL = os.environ.get(
    "ENDPOINT_URL", f"https://bedrock-runtime.{AWS_REGION}.amazonaws.com"
)
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "256"))
MODEL_ID = str(os.getenv("MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0"))

DEFAULT_MAX_TOKENS = 1024
SUCCESS = "SUCCESS"
FAILED = "FAILED"

bedrock_client = None

SSM_LLM_SUMMARIZATION_NAME = "ci_summarization_prompt"
SSM_LLM_ACTION_PROMPT = "ci_action_prompt"
SSM_LLM_TOPIC_PROMPT = "ci_topic_prompt"
SSM_LLM_PRODUCT_PROMPT = "ci_product_prompt"
SSM_LLM_RESOLVED_PROMPT = "ci_resolved_prompt"
SSM_LLM_CALLBACK_PROMPT = "ci_callback_prompt"
SSM_LLM_POLITE_PROMPT = "ci_politeness_prompt"
SSM_LLM_AGENT_SENTIMENT_PROMPT = "ci_agent_sentiment_prompt"
SSM_LLM_CUSTOMER_SENTIMENT_PROMPT = "ci_customer_sentiment_prompt"

def get_request_body(modelId, parameters, prompt):
    provider = modelId.split(".")[0]
    request_body = None
    if provider == "anthropic":
        request_body = { "messages": [{"role": "user","content": [{"type": "text","text": prompt}]}],"anthropic_version": "bedrock-2023-05-31","max_tokens": DEFAULT_MAX_TOKENS}
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
        generated_text = response_body["content"][0]["text"]
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
        request_body = { "messages": [{"role": "user","content": [{"type": "text","text": prompt}]}],"anthropic_version": "bedrock-2023-05-31","max_tokens": MAX_TOKENS}
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
        generated_text = response_body["content"][0]["text"]
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


def merge_json(original, addition):
    for k, v in addition.items():
        if k not in original:
            original[k] = v
        else:
            if isinstance(v, dict):
                merge_json(original[k], v)
            elif isinstance(v, list):
                for i in range(len(v)):
                    merge_json(original[k][i], v[i])
            else:
                if not original[k]:
                    original[k] = v


def handler(e, context):
    merge_json(e[0], e[1])
    merged_event = e[0]
    event = merged_event["event"]
    s3_bucket = event["bucket"]
    output_key = event["output_s3_key"]
    original_transcription_file = event["original_transcription_file"]
    language = event["dominant_language_code"]

    # Download original transcript file
    if language != 'original' and language != 'en':
        original_transcription_file = original_transcription_file.replace('original', 'translated')
        original_transcription_file = original_transcription_file.replace('en', 'translated')

    temp_transcription_file_path = "/tmp/" + original_transcription_file

    s3_client.download_file(
        s3_bucket,
        f"{output_key}/{original_transcription_file}",
        temp_transcription_file_path,
    )

    transcript_data = ""
    with open(temp_transcription_file_path, "rt") as file:
        for line in file.readlines():
            transcript_data += line.strip() + "\n"

    try:
        llm_summarization_prompt = ssm_client.get_parameter(
            Name=SSM_LLM_SUMMARIZATION_NAME
        )
        prompt = llm_summarization_prompt["Parameter"]["Value"]
        query_response = generate_bedrock_query(prompt, transcript_data, "")
        event["Summarization"] = query_response

        llm_action_prompt = ssm_client.get_parameter(
            Name=SSM_LLM_ACTION_PROMPT
        )
        prompt = llm_action_prompt["Parameter"]["Value"]
        query_response = generate_bedrock_query(prompt, transcript_data, "")
        event["ActionItems"] = query_response

        llm_topic_prompt = ssm_client.get_parameter(
            Name=SSM_LLM_TOPIC_PROMPT
        )
        prompt = llm_topic_prompt["Parameter"]["Value"]
        query_response = generate_bedrock_query(prompt, transcript_data, "")
        event["Topic"] = query_response

        llm_polite_prompt = ssm_client.get_parameter(
            Name=SSM_LLM_POLITE_PROMPT
        )
        prompt = llm_polite_prompt["Parameter"]["Value"]
        query_response = generate_bedrock_query(prompt, transcript_data, "")
        event["Politeness"] = query_response

        llm_callback_prompt = ssm_client.get_parameter(
            Name=SSM_LLM_CALLBACK_PROMPT
        )
        prompt = llm_callback_prompt["Parameter"]["Value"]
        query_response = generate_bedrock_query(prompt, transcript_data, "")
        event["Callback"] = query_response

        llm_product_prompt = ssm_client.get_parameter(
            Name=SSM_LLM_PRODUCT_PROMPT
        )
        prompt = llm_product_prompt["Parameter"]["Value"]
        query_response = generate_bedrock_query(prompt, transcript_data, "")
        event["Product"] = query_response

        llm_resolved_prompt = ssm_client.get_parameter(
            Name=SSM_LLM_RESOLVED_PROMPT
        )
        prompt = llm_resolved_prompt["Parameter"]["Value"]
        query_response = generate_bedrock_query(prompt, transcript_data, "")
        event["Resolution"] = query_response

        llm_agent_sentiment_prompt = ssm_client.get_parameter(
            Name=SSM_LLM_AGENT_SENTIMENT_PROMPT
        )
        prompt = llm_agent_sentiment_prompt["Parameter"]["Value"]
        query_response = generate_bedrock_query(prompt, transcript_data, "")
        event["AgentSentiment"] = str(query_response).split(',', 1)[0]

        llm_customer_sentiment_prompt = ssm_client.get_parameter(
            Name=SSM_LLM_CUSTOMER_SENTIMENT_PROMPT
        )
        prompt = llm_customer_sentiment_prompt["Parameter"]["Value"]
        query_response = generate_bedrock_query(prompt, transcript_data, "")
        event["CustomerSentiment"] = str(query_response).split(',', 1)[0]

        print(f"Summarization compeleted for {output_key}")
    except Exception as err:
        query_response = "An error occurred generating Bedrock query response."
        print(err)

    return {
        "event": event,
        "status": "SUCCEEDED",
    }
