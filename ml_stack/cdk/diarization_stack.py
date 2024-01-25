#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0
import os

from aws_cdk import (
    aws_sagemaker as sagemaker,
    aws_ssm as ssm,
    aws_applicationautoscaling as autoscaling,
    CfnOutput
)
from aws_cdk.aws_ecr_assets import DockerImageAsset

import cfg


class SpeakerDiarizationStack:
    """
    This is modular stack that creates required components for speaker diarization. It creates Container Image,
    and uploads to ECR Repository. Then it also creates Amazon SageMaker Endpoint Configuration using which the stack
    creates Amazon SageMaker Endpoint for inference

    Important: This file is created for modularity. It's not a CDK Construct itself.

    :param cdk_scope: Scope from CDK Construct
    :param model_execution_role: Execution Role required for SageMaker Model / Container
    :param ml_processing_bucket: Bucket where all files are processed and output stored
    :param sagemaker_invocation_policy: Invocation policy that should be attached to the SageMaker model
    """
    def __init__(self, cdk_scope, model_execution_role,
                 ml_processing_bucket, sagemaker_invocation_policy):

        # Speaker Diarization Image
        diarization_image = DockerImageAsset(
            cdk_scope,
            "diarization_image",
            asset_name="diarization_image",
            directory=os.path.join("./ml_stack/diarization"),
        )

        container = sagemaker.CfnModel.ContainerDefinitionProperty(
            image=diarization_image.image_uri,
            image_config=sagemaker.CfnModel.ImageConfigProperty(
                repository_access_mode="Platform",
            ),
            environment={"HF_AUTH_TOKEN": cfg.HF_TOKEN, "DZ_MAX_SPEAKERS": cfg.DZ_MAX_SPEAKERS},
        )

        diarization_model = sagemaker.CfnModel(
            cdk_scope,
            "diarization_model",
            execution_role_arn=model_execution_role.role_arn,
            containers=[container],
            model_name="diarization-model" + cfg.ML_MODEL_SUFFIX,
        )

        diarization_variant_name = "variant-1"

        diarization_product_variant = sagemaker.CfnEndpointConfig.ProductionVariantProperty(
            model_name="diarization-model" + cfg.ML_MODEL_SUFFIX,
            variant_name=diarization_variant_name,
            instance_type="ml.g5.2xlarge",
            initial_instance_count=1,
            initial_variant_weight=1,
        )

        async_config = sagemaker.CfnEndpointConfig.AsyncInferenceConfigProperty(
            output_config=sagemaker.CfnEndpointConfig.AsyncInferenceOutputConfigProperty(
                s3_output_path=f"s3://{ml_processing_bucket.bucket_name}/diarization/"
            ),
            client_config=sagemaker.CfnEndpointConfig.AsyncInferenceClientConfigProperty(
                max_concurrent_invocations_per_instance=2
            ),
        )

        diarization_endpoint_config = sagemaker.CfnEndpointConfig(
            scope=cdk_scope,
            id="diarization_config",
            production_variants=[diarization_product_variant],
            endpoint_config_name="diarization-config" + cfg.ML_MODEL_SUFFIX,
            async_inference_config=async_config,
        )
        diarization_endpoint_config.add_dependency(diarization_model)

        diarization_endpoint = sagemaker.CfnEndpoint(
            scope=cdk_scope,
            id="diarization_endpoint",
            endpoint_config_name=diarization_endpoint_config.attr_endpoint_config_name,
            endpoint_name="diarization" + cfg.ML_MODEL_SUFFIX,
        )
        diarization_endpoint.add_dependency(diarization_endpoint_config)
        diarization_scaling_target = autoscaling.CfnScalableTarget(
            cdk_scope,
            "diarization_scaling_target",
            min_capacity=1,
            max_capacity=3,
            resource_id=f"endpoint/{diarization_endpoint.endpoint_name}/variant/{diarization_variant_name}",
            role_arn=model_execution_role.role_arn,
            scalable_dimension="sagemaker:variant:DesiredInstanceCount",
            service_namespace="sagemaker"
        )
        diarization_scaling_target.add_dependency(diarization_endpoint)

        diarization_scaling_policy = autoscaling.CfnScalingPolicy(
            cdk_scope,
            "diarization_scaling_policy",
            policy_name="diarization_scaling_policy",
            policy_type="TargetTrackingScaling",
            resource_id=f"endpoint/{diarization_endpoint.endpoint_name}/variant/{diarization_variant_name}",
            scalable_dimension="sagemaker:variant:DesiredInstanceCount",
            service_namespace="sagemaker",
            target_tracking_scaling_policy_configuration=autoscaling.CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty(
                target_value=15,
                scale_in_cooldown=120,
                scale_out_cooldown=20,
                customized_metric_specification=autoscaling.CfnScalingPolicy.CustomizedMetricSpecificationProperty(
                    metric_name="ApproximateBacklogSizePerInstance",
                    namespace="AWS/SageMaker",
                    dimensions=[autoscaling.CfnScalingPolicy.MetricDimensionProperty(
                        name="EndpointName",
                        value=diarization_endpoint.endpoint_name
                    )],
                    statistic="Average"
                )
            )
        )
        diarization_scaling_policy.add_dependency(diarization_scaling_target)

        ssm.StringParameter(
            cdk_scope,
            "ci_diarization_endpoint",
            parameter_name=cfg.CI_DIARIZATION_ENDPOINT_PARAM,
            string_value=diarization_endpoint.endpoint_name,
        )

        CfnOutput(
            cdk_scope,
            "diarization_endpoint_name",
            value=diarization_endpoint.endpoint_name,
            export_name="diarization-endpoint-name",
        )
