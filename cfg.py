#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

# Application Configuration
# Note: changing the APP_NAME will result in a new stack being provisioned
APP_NAME = "CI"
APP_VERSION = "v0.1"
CFN_STACK_DESCRIPTION = "Conversation Intelligence on AWS (" + APP_VERSION + ")"
CFN_JDBC_CHANNEL_STACK_DESCRIPTION = (
    "This stack is used for analyze calls, chat transcripts"
)

REGION = "us-west-2"
NAME_PREFIX = "ci"

# HuggingFace AuthToken
HF_TOKEN = 'hf_xxxx'
DZ_MAX_SPEAKERS = 2

# General Naming Constants
S3_ML_OUTPUT_BUCKET = "process"  # Adding Hyphen as S3 name can only be Hyphen
S3_TRANSCRIPT_UPLOAD_BUCKET = "conversations"
S3_TRANSCRIPT_INPUT_BUCKET_PREFIX = "input"
S3_TRANSCRIPT_OUTPUT_BUCKET_PREFIX = "output"
S3_WEB_BUCKET = "web"

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

CI_DIARIZATION_ENDPOINT_PARAM = "ci-diarization-endpoint"
CI_TRANSCRIPTION_ENDPOINT_PARAM = "ci-transcription-endpoint"

ML_MODEL_SUFFIX = "-v1"

# Lambda Related Constants
PYTHON_VERSION = "PYTHON_3_11"
STEP_FUNCTION_WAIT_TIME = 30
