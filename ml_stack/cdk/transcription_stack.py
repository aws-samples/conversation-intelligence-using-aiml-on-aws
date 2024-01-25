#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import os
import cfg
from aws_cdk import (
    aws_sagemaker as sagemaker,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_applicationautoscaling as autoscaling,
    CfnOutput
)
from aws_cdk.aws_ecr_assets import DockerImageAsset


class TranscriptionStack:
    """
    This is modular stack that creates required components for transcription. It creates Container Image,
    and uploads to ECR Repository. Then it also creates Amazon SageMaker Endpoint Configuration using which the stack
    creates Amazon SageMaker Endpoint for inference

    Important: This file is created for modularity. It's not a CDK Construct itself.

    :param cdk_scope: Scope from CDK Construct
    :param model_execution_role: Execution Role required for SageMaker Model / Container
    :param ml_processing_bucket: Bucket where all files are processed and output stored
    :param sagemaker_invocation_policy: Invocation policy that should be attached to the SageMaker model
    """

    def __init__(self, cdk_scope, model_execution_role, ml_processing_bucket,
                 sagemaker_invocation_policy):
        # Transcription ML Endpoint
        transcription_image = DockerImageAsset(
            cdk_scope,
            "transcription_image",
            asset_name="transcription_image",
            directory=os.path.join("./ml_stack/transcription"),
        )

        transcription_execution_role = iam.Role(
            cdk_scope,
            "transcription_execution_role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
        )

        transcription_execution_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonEC2ContainerRegistryFullAccess"
            )
        )
        transcription_execution_role.attach_inline_policy(sagemaker_invocation_policy)

        transcription_container = sagemaker.CfnModel.ContainerDefinitionProperty(
            image=transcription_image.image_uri,
            image_config=sagemaker.CfnModel.ImageConfigProperty(
                repository_access_mode="Platform",
            ),
            environment={"HF_AUTH_TOKEN": cfg.HF_TOKEN},
        )

        transcription_model = sagemaker.CfnModel(
            cdk_scope,
            "transcription_model",
            execution_role_arn=model_execution_role.role_arn,
            containers=[transcription_container],
            model_name="transcription-model" + cfg.ML_MODEL_SUFFIX,
        )

        transcription_variant_name = "variant-1"

        transcription_variant = sagemaker.CfnEndpointConfig.ProductionVariantProperty(
            model_name="transcription-model" + cfg.ML_MODEL_SUFFIX,
            variant_name=transcription_variant_name,
            instance_type="ml.g5.2xlarge",
            initial_instance_count=1,
            initial_variant_weight=1,
        )

        transcription_async_config = sagemaker.CfnEndpointConfig.AsyncInferenceConfigProperty(
            output_config=sagemaker.CfnEndpointConfig.AsyncInferenceOutputConfigProperty(
                s3_output_path=f"s3://{ml_processing_bucket.bucket_name}/transcription/"
            ),
            client_config=sagemaker.CfnEndpointConfig.AsyncInferenceClientConfigProperty(
                max_concurrent_invocations_per_instance=2
            ),
        )

        transcription_endpoint_config = sagemaker.CfnEndpointConfig(
            scope=cdk_scope,
            id="transcription_config",
            production_variants=[transcription_variant],
            endpoint_config_name="transcription-config" + cfg.ML_MODEL_SUFFIX,
            async_inference_config=transcription_async_config,
        )
        transcription_endpoint_config.add_dependency(transcription_model)

        transcription_endpoint = sagemaker.CfnEndpoint(
            scope=cdk_scope,
            id="transcription_endpoint",
            endpoint_config_name=transcription_endpoint_config.attr_endpoint_config_name,
            endpoint_name="transcription" + cfg.ML_MODEL_SUFFIX,
        )
        transcription_endpoint.add_dependency(transcription_endpoint_config)

        scaling_target = autoscaling.CfnScalableTarget(
            cdk_scope,
            "transcription_scaling_target",
            min_capacity=1,
            max_capacity=10,
            resource_id=f"endpoint/{transcription_endpoint.endpoint_name}/variant/{transcription_variant_name}",
            role_arn=transcription_execution_role.role_arn,
            scalable_dimension="sagemaker:variant:DesiredInstanceCount",
            service_namespace="sagemaker"
        )
        scaling_target.add_dependency(transcription_endpoint)

        scaling_policy = autoscaling.CfnScalingPolicy(
            cdk_scope,
            "transcription_scaling_policy",
            policy_name="transcription_scaling_policy",
            policy_type="TargetTrackingScaling",
            resource_id=f"endpoint/{transcription_endpoint.endpoint_name}/variant/{transcription_variant_name}",
            scalable_dimension="sagemaker:variant:DesiredInstanceCount",
            service_namespace="sagemaker",
            target_tracking_scaling_policy_configuration=autoscaling.CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty(
                target_value=10.0,
                scale_in_cooldown=1800.0,
                scale_out_cooldown=20.0,
                customized_metric_specification=autoscaling.CfnScalingPolicy.CustomizedMetricSpecificationProperty(
                    metric_name="ApproximateBacklogSizePerInstance",
                    namespace="AWS/SageMaker",
                    dimensions=[autoscaling.CfnScalingPolicy.MetricDimensionProperty(
                        name="EndpointName",
                        value=transcription_endpoint.endpoint_name
                    )],
                    statistic="Average"
                )
            )
        )
        scaling_policy.add_dependency(scaling_target)

        ssm.StringParameter(
            cdk_scope,
            "ci_transcription_endpoint",
            parameter_name=cfg.CI_TRANSCRIPTION_ENDPOINT_PARAM,
            string_value=transcription_endpoint.endpoint_name,
        )

        ssm.StringParameter(
            cdk_scope,
            "ci_transcription_endpoint_variant",
            parameter_name="ci-transcription-endpoint-variant",
            string_value=transcription_variant_name
        )

        CfnOutput(
            cdk_scope,
            "transcription_endpoint_name",
            value=transcription_endpoint.endpoint_name,
            export_name="transcription-endpoint-name",
        )
