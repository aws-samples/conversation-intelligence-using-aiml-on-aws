#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import json
import boto3

ssm_client = boto3.client("ssm")
SSM_LLM_CHATBOT_NAME = "ci_chatbot_prompt"
SSM_LLM_SUMMARIZATION_NAME = "ci_summarization_prompt"
SSM_LLM_ACTION_PROMPT = "ci_action_prompt"
SSM_LLM_TOPIC_PROMPT = "ci_topic_prompt"
SSM_LLM_PRODUCT_PROMPT = "ci_product_prompt"
SSM_LLM_RESOLVED_PROMPT = "ci_resolved_prompt"
SSM_LLM_CALLBACK_PROMPT = "ci_callback_prompt"
SSM_LLM_POLITE_PROMPT = "ci_politeness_prompt"
SSM_LLM_AGENT_SENTIMENT_PROMPT = "ci_agent_sentiment_prompt"
SSM_LLM_CUSTOMER_SENTIMENT_PROMPT = "ci_customer_sentiment_prompt"


def handler(event, context):
    url_key = event["path"].replace("/prompts/", "")

    if url_key == "update":
        request = json.loads(event["body"])
        key = request["title"]
        if key == 'Chatbot':
            ssm_client.put_parameter(
                Name=SSM_LLM_CHATBOT_NAME,
                Value=request["prompt"],
                Type="String",
                Overwrite=True,
            )
        elif key == "Summarization":
            ssm_client.put_parameter(
                Name=SSM_LLM_SUMMARIZATION_NAME,
                Value=request["prompt"],
                Type="String",
                Overwrite=True,
            )
        elif key == "Action Item":
            ssm_client.put_parameter(
                Name=SSM_LLM_ACTION_PROMPT,
                Value=request["prompt"],
                Type="String",
                Overwrite=True,
            )
        elif key == "Topic":
            ssm_client.put_parameter(
                Name=SSM_LLM_TOPIC_PROMPT,
                Value=request["prompt"],
                Type="String",
                Overwrite=True,
            )
        elif key == "Product":
            ssm_client.put_parameter(
                Name=SSM_LLM_PRODUCT_PROMPT,
                Value=request["prompt"],
                Type="String",
                Overwrite=True,
            )
        elif key == "Resolution":
            ssm_client.put_parameter(
                Name=SSM_LLM_RESOLVED_PROMPT,
                Value=request["prompt"],
                Type="String",
                Overwrite=True,
            )
        elif key == "Callback":
            ssm_client.put_parameter(
                Name=SSM_LLM_CALLBACK_PROMPT,
                Value=request["prompt"],
                Type="String",
                Overwrite=True,
            )
        elif key == "Politeness":
            ssm_client.put_parameter(
                Name=SSM_LLM_POLITE_PROMPT,
                Value=request["prompt"],
                Type="String",
                Overwrite=True,
            )
        elif key == "Agent Sentiment":
            ssm_client.put_parameter(
                Name=SSM_LLM_AGENT_SENTIMENT_PROMPT,
                Value=request["prompt"],
                Type="String",
                Overwrite=True,
            )
        elif key == "Customer Sentiment":
            ssm_client.put_parameter(
                Name=SSM_LLM_CUSTOMER_SENTIMENT_PROMPT,
                Value=request["prompt"],
                Type="String",
                Overwrite=True,
            )
        print(f'Prompt updated for {request["prompt"]}')

    prompts = []
    llm_chatbot_prompt = ssm_client.get_parameter(Name=SSM_LLM_CHATBOT_NAME)
    prompts.append({
        "title": "Chatbot",
        "prompt": llm_chatbot_prompt["Parameter"]["Value"]
    })

    llm_summarization_prompt = ssm_client.get_parameter(Name=SSM_LLM_SUMMARIZATION_NAME)
    prompts.append({
        "title": "Summarization",
        "prompt": llm_summarization_prompt["Parameter"]["Value"]
    })

    llm_action_prompt = ssm_client.get_parameter(Name=SSM_LLM_ACTION_PROMPT)
    prompts.append({
        "title": "Action Item",
        "prompt": llm_action_prompt["Parameter"]["Value"]
    })

    llm_topic_prompt = ssm_client.get_parameter(Name=SSM_LLM_TOPIC_PROMPT)
    prompts.append({
        "title": "Topic",
        "prompt": llm_topic_prompt["Parameter"]["Value"]
    })

    llm_product_prompt = ssm_client.get_parameter(Name=SSM_LLM_PRODUCT_PROMPT)
    prompts.append({
        "title": "Product",
        "prompt": llm_product_prompt["Parameter"]["Value"]
    })

    llm_resolved_prompt = ssm_client.get_parameter(Name=SSM_LLM_RESOLVED_PROMPT)
    prompts.append({
        "title": "Resolution",
        "prompt": llm_resolved_prompt["Parameter"]["Value"]
    })

    llm_callback_prompt = ssm_client.get_parameter(Name=SSM_LLM_CALLBACK_PROMPT)
    prompts.append({
        "title": "Callback",
        "prompt": llm_callback_prompt["Parameter"]["Value"]
    })

    llm_polite_prompt = ssm_client.get_parameter(Name=SSM_LLM_POLITE_PROMPT)
    prompts.append({
        "title": "Politeness",
        "prompt": llm_polite_prompt["Parameter"]["Value"]
    })

    llm_agent_sentiment_prompt = ssm_client.get_parameter(Name=SSM_LLM_AGENT_SENTIMENT_PROMPT)
    prompts.append({
        "title": "Agent Sentiment",
        "prompt": llm_agent_sentiment_prompt["Parameter"]["Value"]
    })

    llm_customer_sentiment_prompt = ssm_client.get_parameter(Name=SSM_LLM_CUSTOMER_SENTIMENT_PROMPT)
    prompts.append({
        "title": "Customer Sentiment",
        "prompt": llm_customer_sentiment_prompt["Parameter"]["Value"]
    })

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
            'Content-Type':'application/json'
        },
        "body": json.dumps(prompts)
    }
