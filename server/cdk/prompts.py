#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_ssm as ssm,
)

import cfg


class PromptsStack:
    def __init__(self, cdk_scope):
        model_id_param = ssm.StringParameter(
            cdk_scope,
            "model_id",
            description="Parameter to store Bedrock Model ID",
            string_value="anthropic.claude-v2",
        )

        summarization_prompt = ssm.StringParameter(
            cdk_scope,
            "summarization_prompt",
            simple_name=True,
            parameter_name=cfg.SSM_LLM_SUMMARIZATION_NAME,
            description="Prompt template for generating summary of overall chat",
            string_value="<br><br>Human: Answer the questions below, defined in <question></question> based on the "
            "transcript defined in <transcript></transcript>. If you cannot answer the question, "
            "reply with 'n/a'. Use gender neutral pronouns. When you reply, only respond with the "
            "answer. Do not use XML tags in the answer.<br><br>"
            "<question>What is a summary of the transcript?</question><br><br><transcript><br>{"
            "transcript}<br></transcript><br><br>Assistant:",
        )

        topic_prompt = ssm.StringParameter(
            cdk_scope,
            "topic_prompt",
            parameter_name=cfg.SSM_LLM_TOPIC_PROMPT,
            description="Prompt template for finding primary topic",
            string_value="<br><br>Human: Answer the questions below, defined in <question></question> based on the "
            "transcript defined in <transcript></transcript>. If you cannot answer the question, "
            "reply with 'n/a'. Use gender neutral pronouns. When you reply, only respond with the "
            "answer. Do not use XML tags in the answer.<br><br>"
            "<question>What is the topic of the call? For example, iphone issue, "
            "billing issue, cancellation. Only reply with the topic, "
            "nothing more.</question><br><br><transcript><br>{transcript}<br></transcript><br><br>Assistant:",
        )

        product_prompt = ssm.StringParameter(
            cdk_scope,
            "product_prompt",
            parameter_name=cfg.SSM_LLM_PRODUCT_PROMPT,
            description="Prompt template for finding products discussed",
            string_value="<br><br>Human: Answer the questions below, defined in <question></question> based on the "
            "transcript defined in <transcript></transcript>. If you cannot answer the question, "
            "reply with 'n/a'. Use gender neutral pronouns. When you reply, only respond with the "
            "answer. Do not use XML tags in the answer.<br><br>"
            "<question>What product did the customer call about? For example, internet, "
            "broadband, mobile phone, mobile plans. Only reply with the product, "
            "nothing more.</question><br><br><transcript><br>{transcript}<br></transcript><br><br>Assistant:",
        )

        resolved_prompt = ssm.StringParameter(
            cdk_scope,
            "resolved_prompt",
            parameter_name=cfg.SSM_LLM_RESOLVED_PROMPT,
            description="Prompt template for generating resolutions",
            string_value="<br><br>Human: Answer the questions below, defined in <question></question> based on the "
            "transcript defined in <transcript></transcript>. If you cannot answer the question, "
            "reply with 'n/a'. Use gender neutral pronouns. When you reply, only respond with the "
            "answer. Do not use XML tags in the answer.<br><br>"
            "<question>Did the agent resolve the customer's questions? Only reply with yes or "
            "no, nothing more. </question><br><br><transcript><br>{transcript}<br></transcript><br><br>Assistant:",
        )

        callback_prompt = ssm.StringParameter(
            cdk_scope,
            "callback_prompt",
            parameter_name=cfg.SSM_LLM_CALLBACK_PROMPT,
            description="Prompt template for generating callback prompts",
            string_value="<br><br>Human: Answer the questions below, defined in <question></question> based on the "
            "transcript defined in <transcript></transcript>. If you cannot answer the question, "
            "reply with 'n/a'. Use gender neutral pronouns. When you reply, only respond with the "
            "answer. Do not use XML tags in the answer.<br><br>"
            "<question>Was this a callback? (yes or no) Only reply with yes or no, "
            "nothing more.</question><br><br><transcript><br>{transcript}<br></transcript><br><br>Assistant:",
        )

        politeness_prompt = ssm.StringParameter(
            cdk_scope,
            "politeness_prompt",
            parameter_name=cfg.SSM_LLM_POLITE_PROMPT,
            description="Prompt template for checking politeness",
            string_value="<br><br>Human: Answer the question below, defined in <question></question> based on the "
            "transcript defined in <transcript></transcript>. If you cannot answer the question, "
            "reply with 'n/a'. Use gender neutral pronouns. When you reply, only respond with the "
            "answer.Do not use XML tags in the answer.<br><br>"
            "<question>Was the agent polite and professional? (yes or no) Only reply with yes "
            "or no, nothing more.</question><br><br><transcript><br>{transcript}<br></transcript><br><br>Assistant:",
        )

        actions_prompt = ssm.StringParameter(
            cdk_scope,
            "actions_prompt",
            parameter_name=cfg.SSM_LLM_ACTION_PROMPT,
            description="Prompt template for generating actions",
            string_value="<br><br>Human: Answer the question below, defined in <question></question> based on the "
            "transcript defined in <transcript></transcript>. If you cannot answer the question, "
            "reply with 'n/a'. Use gender neutral pronouns. When you reply, only respond with the "
            "answer. Do not use XML tags in the answer.<br><br>"
            "<question>What actions did the Agent take? </question><br><br><transcript><br>{"
            "transcript}<br></transcript><br><br>Assistant:",
        )

        agent_feedback_prompt = ssm.StringParameter(
            cdk_scope,
            "agent_feedback_prompt",
            parameter_name=cfg.SSM_LLM_AGENT_SENTIMENT_PROMPT,
            description="Prompt template for generating actions",
            string_value="<br><br>Human: Return a single word for sentiment of the Agent in either "
            "['Positive','Negative' or 'Neutral'] from this transcript."
            "<br>TRANSCRIPT: {transcript}"
            "<br>SENTIMENT LABEL HERE ('Positive','Negative', or 'Neutral') "
            "<br>Assistant:",
        )

        customer_feedback_prompt = ssm.StringParameter(
            cdk_scope,
            "customer_feedback_prompt",
            parameter_name=cfg.SSM_LLM_CUSTOMER_SENTIMENT_PROMPT,
            description="Prompt template for generating actions",
            string_value="<br><br>Human: Return a single word for sentiment of the Customer in either "
            "['Positive','Negative' or 'Neutral'] from this transcript."
            "<br>TRANSCRIPT: {transcript}"
            "<br>SENTIMENT LABEL HERE ('Positive','Negative', or 'Neutral') "
            "<br>Assistant:",
        )

        self.model_id_param = model_id_param
        self.summarization_prompt = summarization_prompt
        self.topic_prompt = topic_prompt
        self.product_prompt = product_prompt
        self.resolved_prompt = resolved_prompt
        self.callback_prompt = callback_prompt
        self.politeness_prompt = politeness_prompt
        self.actions_prompt = actions_prompt
        self.agent_feedback_prompt = agent_feedback_prompt
        self.customer_feedback_prompt = customer_feedback_prompt
