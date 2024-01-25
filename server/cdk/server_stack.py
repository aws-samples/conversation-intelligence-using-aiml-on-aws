#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import typing

import aws_cdk
from aws_cdk import (
    aws_s3 as _s3,
    aws_s3_notifications,
    aws_lambda as _lambda,
    Duration,
    Stack,
    aws_batch as batch,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_iam as iam,
    BundlingOptions,
    aws_ssm as ssm,
    aws_dynamodb as dynamodb,
    Fn,
    Size,
    CfnOutput
)

from constructs import Construct
from server.cdk.prompts import PromptsStack
from server.cdk.step_function import StepFunctionStack

import cfg


class ServerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Setting tags to all resources within the scope
        aws_cdk.Tags.of(scope).add("Module", "Server Stack")
        ci_lambda_runtime = typing.cast(_lambda.Runtime, _lambda.Runtime.PYTHON_3_11)

        # Initializing all prompts that are part of process stack
        prompts = PromptsStack(cdk_scope=self)

        # Task execution IAM role for Fargate
        task_execution_role = iam.Role(
            self,
            "task_execution_role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ],
        )

        batch_job_role = iam.Role(
            self,
            "job_role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        comprehend_job_role = iam.Role(
            self,
            "comprehend_job_role",
            assumed_by=iam.ServicePrincipal("comprehend.amazonaws.com"),
        )

        comprehend_job_policy = iam.Policy(
            self,
            "detect_sentiment_policy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                    actions=[
                        "iam:PassRole",
                        "comprehend:DetectDominantLanguage",
                        "comprehend:DetectEntities",
                        "comprehend:DetectKeyPhrases",
                        "comprehend:DetectPiiEntities",
                        "comprehend:DetectSentiment",
                        "comprehend:StartDominantLanguageDetectionJob",
                        "comprehend:StartSentimentDetectionJob",
                        "comprehend:StartEntitiesDetectionJob",
                        "comprehend:StartKeyPhrasesDetectionJob",
                        "comprehend:DescribeDominantLanguageDetectionJob",
                        "comprehend:DescribeEntitiesDetectionJob",
                        "comprehend:DescribeKeyPhrasesDetectionJob",
                        "comprehend:DescribePiiEntitiesDetectionJob",
                        "comprehend:DescribeSentimentDetectionJob",
                    ],
                )
            ],
        )
        comprehend_job_role.attach_inline_policy(comprehend_job_policy)

        sagemaker_invocation_policy = iam.Policy(
            self,
            "sagemaker_invocation_policy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                    actions=[
                        "sagemaker:InvokeEndpoint",
                        "sagemaker:InvokeEndpointAsync",
                    ],
                )
            ],
        )

        # This resource alone will create a private/public subnet in each AZ as well as nat/internet gateway(s)
        vpc = ec2.Vpc(self, "ci_vpc", max_azs=3)

        # Creating Audio/Input Processing Bucket
        transcripts_input_bucket = _s3.Bucket(
            self,
            id=cfg.S3_TRANSCRIPT_UPLOAD_BUCKET,
            encryption=_s3.BucketEncryption.S3_MANAGED,
        )

        ssm.StringParameter(
            self,
            "io_bucket_param",
            parameter_name="ci_io_bucket",
            string_value=transcripts_input_bucket.bucket_name
        )

        # Creating DDB Table to store all metadata related to conversation file uploads and processing
        uploads_table = dynamodb.Table(
            self,
            "ci_uploads_ddb",
            partition_key=dynamodb.Attribute(
                name="objectKey", type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        ssm.StringParameter(
            self,
            "uploads_ddb_param",
            parameter_name="ci_uploads_ddb",
            string_value=uploads_table.table_name
        )

        # Fetching model output processing bucket from ML Stack
        ml_stack_output_bucket = _s3.Bucket.from_bucket_arn(
            self,
            "input_bucket_from_arn",
            bucket_arn=Fn.import_value("ml-process-bucket"),
        )

        # Mp3 to WAV related Batch stack
        self.mp3_to_wav_job_queue = batch.JobQueue(self, "mp3_batch")

        mp3_to_wav_compute_environment = batch.FargateComputeEnvironment(
            self,
            "mp3_to_wav_compute_env",
            # spot=True,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            vpc=vpc,
        )

        self.mp3_to_wav_job_queue.add_compute_environment(
            mp3_to_wav_compute_environment, 0
        )

        self.mp3_to_wav_job_def = batch.EcsJobDefinition(
            self,
            "convert_mp3_to_wav_job_def",
            container=batch.EcsFargateContainerDefinition(
                self,
                "convert_mp3_to_wav_container_def",
                image=ecs.ContainerImage.from_asset("./server/containers/mp3towav"),
                memory=Size.mebibytes(4096),
                cpu=2,
                execution_role=task_execution_role,
                job_role=batch_job_role,
            ),
            retry_attempts=1,
        )

        # Chunking related Batch stack
        self.chunking_job_queue = batch.JobQueue(self, "chunking_job_queue")

        chunking_compute_environment = batch.FargateComputeEnvironment(
            self,
            "chunking_compute_env",
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            vpc=vpc,
        )

        self.chunking_job_queue.add_compute_environment(chunking_compute_environment, 0)

        self.chunking_job_def = batch.EcsJobDefinition(
            self,
            "chunking_job_def",
            container=batch.EcsFargateContainerDefinition(
                self,
                "chunking_container_def",
                image=ecs.ContainerImage.from_asset("./server/containers/chunking"),
                memory=Size.mebibytes(8 * 1024),
                cpu=4,
                execution_role=task_execution_role,
                job_role=batch_job_role,
            ),
            retry_attempts=1,
        )

        # Lambda Stack
        self.check_input_file_type_fn = _lambda.Function(
            self,
            id="check_input_types_fn",
            runtime=ci_lambda_runtime,
            handler="check_input_file_type.handler",
            timeout=Duration.minutes(3),
            code=_lambda.Code.from_asset(
                "server/lambdas",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install fleep -t /asset-output && cp -au . /asset-output",
                    ],
                ),
            ),
        )

        diarization_model_endpoint = ssm.StringParameter.from_string_parameter_name(
            self,
            "diarization_model_endpoint",
            string_parameter_name=cfg.CI_DIARIZATION_ENDPOINT_PARAM,
        )

        self.diarization_fn = _lambda.Function(
            self,
            id="diarization_fn",
            runtime=ci_lambda_runtime,
            handler="diarization.handler",
            code=_lambda.Code.from_asset("server/lambdas"),
            timeout=Duration.minutes(3),
            environment={"MODEL_ENDPOINT": diarization_model_endpoint.string_value},
        )

        self.check_diarization_output_fn = _lambda.Function(
            self,
            id="check_diarization_output_fn",
            runtime=ci_lambda_runtime,
            handler="check_diarization_file.handler",
            code=_lambda.Code.from_asset("server/lambdas"),
            timeout=Duration.minutes(3),
        )

        transcription_model_endpoint = ssm.StringParameter.from_string_parameter_name(
            self,
            "transcription_model_endpoint",
            string_parameter_name=cfg.CI_TRANSCRIPTION_ENDPOINT_PARAM,
        )

        self.transcription_fn = _lambda.Function(
            self,
            id="transcription_fn",
            runtime=ci_lambda_runtime,
            handler="transcription.handler",
            code=_lambda.Code.from_asset("server/lambdas"),
            timeout=Duration.minutes(3),
            environment={
                "TRANSCRIPTION_ENDPOINT": transcription_model_endpoint.string_value
            },
        )

        self.transcription_output_fn = _lambda.Function(
            self,
            id="transcription_check_output_fn",
            runtime=ci_lambda_runtime,
            handler="check_transcription_files.handler",
            code=_lambda.Code.from_asset("server/lambdas"),
            timeout=Duration.minutes(3),
        )

        self.combine_file_output_fn = _lambda.Function(
            self,
            id="compile_transcription_output_fn",
            runtime=ci_lambda_runtime,
            handler="combine_transcription_files.handler",
            code=_lambda.Code.from_asset("server/lambdas"),
            timeout=Duration.minutes(5),
        )

        # Lambda StepFunction stack to detect language
        self.detect_language_fn = _lambda.Function(
            self,
            id="detect_languages_fn",
            runtime=ci_lambda_runtime,
            handler="detect_language.handler",
            code=_lambda.Code.from_asset("server/lambdas"),
        )

        # Lambda StepFunction stack to detect sentiment
        self.start_comprehension_fn = _lambda.Function(
            self,
            id="start_comprehend_job_fn",
            runtime=ci_lambda_runtime,
            handler="start_comprehension.handler",
            code=_lambda.Code.from_asset("server/lambdas"),
            environment={"comprehend_job_role": comprehend_job_role.role_arn},
        )

        self.check_sentiment_job_fn = _lambda.Function(
            self,
            id="check_sentiment_job_fn",
            runtime=ci_lambda_runtime,
            handler="detect_sentiment_job_status.handler",
            code=_lambda.Code.from_asset("server/lambdas"),
        )

        self.check_entities_job_fn = _lambda.Function(
            self,
            id="check_entities_job_fn",
            runtime=ci_lambda_runtime,
            handler="detect_entities_job_status.handler",
            code=_lambda.Code.from_asset("server/lambdas"),
        )

        # Summarization stack to process output json file
        summarize_fn_policy = iam.Policy(
            self,
            "summarize_fn_policy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                    actions=["bedrock:InvokeModel"],
                )
            ],
        )

        self.summarize_fn = _lambda.Function(
            self,
            id="summarize_fn",
            handler="summarize.handler",
            timeout=Duration.minutes(15),
            runtime=ci_lambda_runtime,
            # We are pip installing boto3 as bedrock is not available by default
            code=_lambda.Code.from_asset(
                "server/lambdas",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install boto3 -t /asset-output && cp -au . /asset-output",
                    ],
                ),
            ),
        )

        self.post_processing_fn = _lambda.Function(
            self,
            id="post_processing_fn",
            runtime=ci_lambda_runtime,
            handler="post_processor.handler",
            code=_lambda.Code.from_asset("server/lambdas"),
            environment={"UploadsTable": uploads_table.table_name},
            timeout=Duration.minutes(3)
        )

        s3_trigger_lambda = _lambda.Function(
            self,
            id="s3_upload_trigger_fn",
            runtime=ci_lambda_runtime,
            code=_lambda.Code.from_asset("server/lambdas"),
            handler="s3_trigger_fn.handler",
            environment={"UploadsTable": uploads_table.table_name},
        )

        # create s3 notification for lambda function
        notification = aws_s3_notifications.LambdaDestination(s3_trigger_lambda)

        # assign notification for the s3 event type (ex: OBJECT_CREATED)
        transcripts_input_bucket.add_event_notification(
            _s3.EventType.OBJECT_CREATED,
            notification,
            _s3.NotificationKeyFilter(prefix=cfg.S3_TRANSCRIPT_INPUT_BUCKET_PREFIX),
        )

        # Granting Read Permission for Lambda to Input bucket
        transcripts_input_bucket.grant_read(s3_trigger_lambda)
        transcripts_input_bucket.grant_read_write(self.check_input_file_type_fn.role)
        transcripts_input_bucket.grant_read_write(self.detect_language_fn.role)
        transcripts_input_bucket.grant_read_write(self.check_sentiment_job_fn.role)
        transcripts_input_bucket.grant_read_write(self.post_processing_fn.role)
        transcripts_input_bucket.grant_read_write(self.diarization_fn.role)
        transcripts_input_bucket.grant_read_write(self.transcription_fn.role)
        transcripts_input_bucket.grant_read_write(self.summarize_fn.role)
        transcripts_input_bucket.grant_read_write(comprehend_job_role)
        transcripts_input_bucket.grant_read_write(self.transcription_output_fn.role)
        transcripts_input_bucket.grant_read_write(self.combine_file_output_fn.role)
        transcripts_input_bucket.grant_read_write(self.check_diarization_output_fn.role)

        uploads_table.grant_read_write_data(self.post_processing_fn.role)
        uploads_table.grant_read_write_data(s3_trigger_lambda.role)

        ml_stack_output_bucket.grant_read(self.diarization_fn)
        ml_stack_output_bucket.grant_read_write(self.transcription_fn)
        ml_stack_output_bucket.grant_read_write(self.transcription_output_fn)
        ml_stack_output_bucket.grant_read_write(self.check_diarization_output_fn)

        prompts.model_id_param.grant_read(self.summarize_fn.role)
        prompts.summarization_prompt.grant_read(self.summarize_fn.role)
        prompts.actions_prompt.grant_read(self.summarize_fn.role)
        prompts.topic_prompt.grant_read(self.summarize_fn.role)
        prompts.product_prompt.grant_read(self.summarize_fn.role)
        prompts.resolved_prompt.grant_read(self.summarize_fn.role)
        prompts.callback_prompt.grant_read(self.summarize_fn.role)
        prompts.politeness_prompt.grant_read(self.summarize_fn.role)
        prompts.agent_feedback_prompt.grant_read(self.summarize_fn.role)
        prompts.customer_feedback_prompt.grant_read(self.summarize_fn.role)

        self.start_comprehension_fn.role.attach_inline_policy(comprehend_job_policy)
        self.detect_language_fn.role.attach_inline_policy(comprehend_job_policy)
        self.check_sentiment_job_fn.role.attach_inline_policy(comprehend_job_policy)
        self.check_entities_job_fn.role.attach_inline_policy(comprehend_job_policy)

        self.summarize_fn.role.attach_inline_policy(summarize_fn_policy)

        # Granting read/write access to Batch>Container Tasks
        transcripts_input_bucket.grant_read_write(batch_job_role)

        self.diarization_fn.role.attach_inline_policy(sagemaker_invocation_policy)
        self.transcription_fn.role.attach_inline_policy(sagemaker_invocation_policy)

        # Initializing all prompts that are part of process stack
        step_function_stack = StepFunctionStack(cdk_scope=self)
        ci_step = step_function_stack.ci_step
        ci_step.grant_start_execution(s3_trigger_lambda)

        # Adding ARN of State Machine to Lambda
        s3_trigger_lambda.add_environment("ci_workflow", ci_step.state_machine_arn)

        CfnOutput(
            self,
            "ci_conversation_bucket_name",
            value=transcripts_input_bucket.bucket_name,
            export_name="conversation-bucket-name",
        )

        CfnOutput(
            self,
            "ci_step_function_name",
            value=ci_step.state_machine_name,
            export_name="step-function-name",
        )
