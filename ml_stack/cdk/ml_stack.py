#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0
import aws_cdk
import cfg
from aws_cdk import (
    aws_iam as iam,
    aws_s3 as s3,
    Stack,
    CfnOutput,
)
from constructs import Construct

# Importing from local stacks
from ml_stack.cdk.diarization_stack import SpeakerDiarizationStack
from ml_stack.cdk.transcription_stack import TranscriptionStack


class MLStack(Stack):
    """
    This is modular stack that creates required components for speaker diarization and transcription. It creates all
    required components including Amazon SageMaker Endpoints, S3 buckets and related required for Conversation
    Intelligence Stack
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Setting tags to all resources within the scope
        aws_cdk.Tags.of(scope).add("Module", "CI ML Stack")

        # S3 bucket to process all temporary files
        ml_output_bucket = s3.Bucket(
            self,
            id=cfg.S3_ML_OUTPUT_BUCKET,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        model_execution_role = iam.Role(
            self,
            "model_execution_role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
        )

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
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                    actions=[
                        "logs:*",
                        "application-autoscaling:DeleteScalingPolicy",
                        "application-autoscaling:DeleteScheduledAction",
                        "application-autoscaling:DeregisterScalableTarget",
                        "application-autoscaling:DescribeScalableTargets",
                        "application-autoscaling:DescribeScalingActivities",
                        "application-autoscaling:DescribeScalingPolicies",
                        "application-autoscaling:DescribeScheduledActions",
                        "application-autoscaling:PutScalingPolicy",
                        "application-autoscaling:PutScheduledAction",
                        "application-autoscaling:RegisterScalableTarget",
                        "cloudwatch:DeleteAlarms",
                        "cloudwatch:DescribeAlarms",
                        "cloudwatch:GetMetricData",
                        "cloudwatch:GetMetricStatistics",
                        "cloudwatch:ListMetrics",
                        "cloudwatch:PutMetricAlarm",
                        "cloudwatch:PutMetricData",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:BatchGetImage",
                        "ecr:CreateRepository",
                        "ecr:Describe*",
                        "ecr:GetAuthorizationToken",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:StartImageScan",
                        "kms:DescribeKey",
                        "kms:ListAliases",
                        "logs:CreateLogDelivery",
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:DeleteLogDelivery",
                        "logs:Describe*",
                        "logs:GetLogDelivery",
                        "logs:GetLogEvents",
                        "logs:ListLogDeliveries",
                        "logs:PutLogEvents",
                        "logs:PutResourcePolicy",
                        "logs:UpdateLogDelivery",
                    ],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                    actions=[
                        "s3:Abort*",
                        "s3:DeleteObject*",
                        "s3:GetBucket*",
                        "s3:GetObject*",
                        "s3:List*",
                        "s3:PutObject",
                        "s3:PutObjectLegalHold",
                        "s3:PutObjectRetention",
                        "s3:PutObjectTagging",
                        "s3:PutObjectVersionTagging",
                    ],
                ),
            ],
        )
        model_execution_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonEC2ContainerRegistryFullAccess"
            )
        )
        model_execution_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonS3FullAccess"
            )
        )
        model_execution_role.attach_inline_policy(sagemaker_invocation_policy)

        SpeakerDiarizationStack(
            cdk_scope=self,
            ml_processing_bucket=ml_output_bucket,
            sagemaker_invocation_policy=sagemaker_invocation_policy,
            model_execution_role=model_execution_role,
        )

        TranscriptionStack(
            cdk_scope=self,
            ml_processing_bucket=ml_output_bucket,
            sagemaker_invocation_policy=sagemaker_invocation_policy,
            model_execution_role=model_execution_role,
        )

        CfnOutput(
            self,
            "ml_process_bucket",
            value=ml_output_bucket.bucket_arn,
            export_name="ml-process-bucket",
        )
