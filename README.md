# Conversation Intelligence using Artifical Intelligence (AI) / Machine Learning(ML) on AWS

> Jump to [deployment steps](#2-steps-to-deploy)

## 1. Overview

Businesses and industries often need to provide customer help: before a purchase of your product or service, during an
existing customer support instance, or throughout their core workflow. For example, a healthcare company may want to
engage users on a weight loss program or a fintech company might want to verify identity information or explain loan
application steps - customer interaction happens in many ways. The key is being ready to help your customers when and
how they need it. No matter what the situation is, you as a business, need to ensure few things,

- **Understand your customer well and their journey** - where is your customer coming from, why are they here and what
  is
  the best way to solve their problems.
- **Understand outcome and business impact** – how well you served them, how brief contacts were required to solve the
  issue, how much was the ROI for your business, how much future wallet would it bring.
- **Understand the opportunities** - how do we use all the data to continuously improve customer experience and margins.
- **Understand compliance needs** – Are there certain regulations that we need to adhere to? GDPR? HIPAA?

Many organizations currently rely on a manual quality control process for customer interactions. This involves randomly
sampling a limited number of conversations for analysis. For regulated industries like healthcare and fintech, more
rigorous analysis of customer conversations may be required for conformity and protocol adherence. Additionally, there
is often a failure to quickly identify emerging themes and training opportunities across
conversations.

Organizations interact with customers across multiple channels - phone, video, chat etc. A robust "conversation
intelligence" solution that combines AI/ML technologies is needed to enable processing of entire customer conversations,
regardless of channel.

This sample solution leverages open source models and AWS AI and ML services to extract insights from audio calls, chat
conversations and potentially video. Key capabilities include:

- Sentiment analysis
- Identifying call drivers and emerging trends
- Agent coaching opportunities
- Compliance monitoring and adherence

By processing all customer interactions with AI/ML, this sample solution provides comprehensive coverage and actionable
insights. The open source foundations and AWS services make it easy to configure for your needs.

### 1.1 About this solution

At AWS, there are many ways in which we can build conversation intelligence. This project is inspired by our
other sample solutions that are listed below,

- Post Call Analytics using Amazon Transcribe - https://github.com/aws-samples/amazon-transcribe-post-call-analytics
- Live Call Analytics - https://github.com/aws-samples/amazon-transcribe-live-call-analytics

This sample solution is for those organizations that need to use open-source or custom models that are specifically
built for them. It does most of the heavy lifting associated with providing an end-to-end workflow that can process
call recordings, chat transcripts from your existing workflow. It provides actionable insights to spot emerging trends,
identify agent coaching opportunities, and assess the general sentiment of calls.

### 1.2 Architecture

This sample is modular and can be plugged in to your existing analytics workflows to analyze conversations. Refer the
architecture below.

![Alt Reference Architecture to build Conversation Intelligence using AIML on AWS](images/architecture.png "Reference Architecture to build Conversation Intelligence using AIML on AWS")

The solution supports MP3, WAV and can easily customized to support other audio types. If you have videos, by using
Amazon Elemental MediaConvert, we can extract audio and process audio through this solution. Please take a look at the
process flow below,

![Alt Process flow to build Conversation Intelligence using AIML on AWS](images/process-flow.png "Process flow to build Conversation Intelligence using AIML on AWS")

#### 1.2.1 Speaker Diarization

The first step is to identify speakers. To improve accuracy, and identifiy speakers on the conversation, we
need to first perform diarization. Speaker Diarization is the process of the model helping you understand, "Who spoke
when?". We can use models like Pyannote Audio or Nvidia’s NeMo to diarize input audio files. We use Pyannote.audio,
which is an
open-source toolkit written in Python for speaker diarization. This is based on PyTorch machine learning framework, and
it comes with state-of-the-art pretrained models and pipelines. It can be further finetuned to your own data for even
better performance.

#### 1.2.2 Splitting Audio Files

After diarization, we split original input file to audio clips based on speaker diarization data. The model then takes
audio input and gives text output.

#### 1.2.3 Transcription and Translation

In this solution, we use Faster-Whisper with CTranslate2. faster-whisper is a reimplementation of Whisper model using
CTranslate2, which is a fast inference engine for Transformer models. This implementation claims to have upto 4 times
faster performance than whisper for the same accuracy while using less memory.

> This solution is model agnostic, and you can use any model of your choice by changing container scripts
> under ```ml_stack``` with minimal code change.

After transcription is over, we do translation using same whisper model and give audio as input.

#### 1.2.4 Entities and Sentiment Detection

The solution use Amazon Comprehend, natural language processing / NLP service that uses machine learning to uncover
information in unstructured data. We extract sentiment, entities using Comprehend. We can easily extend this to detect
PII and mask if need be

#### 1.2.5 Generative AI to summarize,generate action items, checking conformity and more

Finally, using generated transcripts, the solution use Generative AI models such as ```Anthropic Claude v2```
on ```Amazon Bedrock``` to summarize the conversation. We’ve built various prompts to extract actions, issues, call back
and other KPIs as needed. For example, you can build a prompt to check if the agent greeted customers properly. And
ended call asking for feedback. And can also get in to complex needs like extracting answers of security question and
comparing with the database to ensure the caller was legitimate.

## 2. Steps to deploy

### 2.1 Setting up cloud environment to build models and web application

> Please note that the models used in this sample solution need significant storage and network. We
> recommend to use AWS Cloud9 IDE to build and deploy. Also, since this build ML model containers
> and deploy to Amazon SageMaker Inference Endpoints, its better to run these on Cloud9. Follow instructions
> from [Setting up Cloud9](https://docs.aws.amazon.com/cloud9/latest/user-guide/setup-express.html) and make sure you
> have enough storage to build models (recommended to have 100GB). After provisioning, ensure you increased disk
> capacity to 100 GB following the steps
>
here [Resize Environment Storage](https://docs.aws.amazon.com/cloud9/latest/user-guide/move-environment.html#move-environment-resize)

This project is set up like a standard Python based CDK project. The initialization process also creates a virtualenv
within this project, stored under the .venv directory. To create the virtualenv it assumes that there is a `python3`
executable in your path with access to the `venv` package. If for any reason the automatic creation of the virtualenv
fails, you can create the virtualenv manually once the init process completes.

To manually create a virtualenv on MacOS and Linux:

```
python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following step to activate your
virtualenv.

```
source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
pip install -r requirements.txt
```

To add additional dependencies, for example other CDK libraries, just add to your requirements.txt file and rerun
the `pip install -r requirements.txt` command.

### 2.2 Setting up AWS environment

We need to configure access credentials in the cloud environment before deploying the CDK stack. For that,
run ```aws configure``` command for the first time to confiture account.

```
aws configure
```

Then ensure you have configured the right region and modified [```cfg.py```](cfg.py). It's ideal to pick a region that
has access to Amazon Bedrock

```
REGION = "us-west-2"
```

### 2.3 Building web application

The web application based on [Cloudscape](https://cloudscape.design/). The source code is
within [```web_app/ci-portal```](web_app/ci-portal). We need to install and build using npm.

```
cd web_app/ci-portal
npm install
npm run build
```

### 2.4 Enable Amazon Bedrock Model Access

Amazon Bedrock users need to request access to models before they are available for use. Model access can be managed
only in the Amazon Bedrock console. To request access to a models, select the Model access link in the left side
navigation panel in the Amazon Bedrock console.
> As a prerequisite, you need
> to [add model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html) Amazon Bedrock in the
> region where you are deploying this solution.

### 2.5 Configure HuggingFace Access token in ```cfg.py```

We are using ```pyannote/speaker-diarization-3.0```and ```pyannote/segmentation-3.0``` which are pretrained models from
HuggingFace. Please ensure you add your [HuggingFace Security Token](https://huggingface.co/docs/hub/security-tokens)
to [```cfg.py```](cfg.py), or else, the solution will fail while executing.

> To create access token, go to your settings in HuggingFace portal, then click on
> the [Access Tokens tab](https://huggingface.co/settings/tokens). Also, make sure token has access to both these models
> by going to the respective models
> page [pyannote/speaker-diarization-3.0](https://huggingface.co/pyannote/speaker-diarization-3.0)
> and [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0) to check if you can access using
> token.

```
HF_TOKEN = 'hf_xxxx'
```

### 2.6 Bootstrap and Deploy the stacks

If you are setting up CDK environment for the first time in the region, then run

```
cdk bootstrap
```

Finally, you can run the following command to deploy all stacks.

```
cdk deploy --all
```

You can optionally do ```cdk deploy --all --require-approval never``` flag which will skip confirming any changes to the
stack deployment and will continue with deployment.

Congratulations! 🎉 You have completed all the steps for setting up conversation intelligence sample solution using AIML
on AWS.

_The CDK stack will deploy two ```g5.2xlarge``` instances for SageMaker Inference Endpoints which will be running all
the time. We recommend to adjust application scaling policy in [diarization_stack](ml_stack/cdk/diarization_stack.py)
and [transcription_stack](ml_stack/cdk/transcription_stack.py) based on your usage pattern._

### 2.7 Other useful CDK commands
* `cdk ls`          list all stacks in the app
* `cdk synth`       emits the synthesized CloudFormation template
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk docs`        open CDK documentation

### 2.8 CDK Stack Details
There are three stakes in this solution

1. ```ml_stack``` - Stack with speaker diarization and transcription models and its respective resources. The stack
   use ```Amazon SageMaker``` to deploy inference endpoints
2. ```server``` - Stack with all the functions and workflows using ```AWS Lambda``` and ```AWS Step Functions```
3. ```web_app``` - Stack with the dashboard application and APIs
   using ```Amazon API Gateway```, ```AWS Lambda```, ```AWS Amplify```

### 2.9 Clean up 
For deleting this stack, run following cdk command.
```
$ cdk destroy --all
```
_Please note that the processed files, and logs will still persist based on the configured policies._  