#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import os
import typing

import aws_cdk
from aws_cdk import (
    aws_s3 as s3,
    Stack,
    aws_s3_deployment as s3_deployment,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as cloudfront_origins,
    aws_cognito as cognito,
    aws_apigatewayv2_authorizers_alpha as gtwy_auth,
    aws_apigateway as api_gtwy,
    aws_cognito_identitypool_alpha as id_pool,
    CfnOutput,
    aws_ssm as ssm,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    Duration,
    aws_logs as logs,
    BundlingOptions,
)
from aws_cdk.aws_cognito_identitypool_alpha import (
    IdentityPoolAuthenticationProviders,
    UserPoolAuthenticationProvider,
)
from constructs import Construct

import cfg


class WebAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Setting tags to all resources within the scope
        aws_cdk.Tags.of(scope).add("Module", "Web Stack")
        ci_lambda_runtime = typing.cast(_lambda.Runtime, _lambda.Runtime.PYTHON_3_11)

        chatbot_prompt = ssm.StringParameter(
            self,
            "chatbot_prompt",
            description="Prompt template for chatbot",
            parameter_name=cfg.SSM_LLM_CHATBOT_NAME,
            string_value="<br><br>Human: You are an AI chatbot. Carefully read the following transcript within "
            "<transcript></transcript> tags. Provide a short answer to the question at the end. If the "
            "answer cannot be determined from the transcript, then reply saying Sorry, I don't know. Use "
            "gender neutral pronouns. Do not use XML tags in the answer.<br><question><br>{question}"
            "<br></question><br><transcript><br>{transcript}<br></transcript><br><br>Assistant:",
        )

        uploads_table_name = ssm.StringParameter.from_string_parameter_name(
            self,
            "ci_uploads_ddb_param",
            string_parameter_name="ci_uploads_ddb",
        )

        # [Added by Anup] Creating DynamoDB Table to keep user custom prompts
        custom_prompt_table = dynamodb.Table(
            self,
            "ci_custom_prompt",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="type", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        # [Added by Anup] Saving Custom Prompts Table name in parameter store
        ssm.StringParameter(
            self,
            "ci_custom_prompt_table",
            parameter_name="ci_custom_prompt_table",
            string_value=custom_prompt_table.table_name
        )

        uploads_table = dynamodb.Table.from_table_name(
            self, "ci_uploads_table", table_name=uploads_table_name.string_value
        )

        input_bucket_name = ssm.StringParameter.from_string_parameter_name(
            self,
            "ci_io_bucket_name",
            string_parameter_name="ci_io_bucket",
        )

        input_bucket = s3.Bucket.from_bucket_name(
            self, "ci_io_bucket", bucket_name=input_bucket_name.string_value
        )

        webapp_bucket = s3.Bucket(
            self, id=cfg.S3_WEB_BUCKET, access_control=s3.BucketAccessControl.PRIVATE
        )

        origin_access_identity = cloudfront.OriginAccessIdentity(self, "ci_app_oai")
        webapp_bucket.grant_read(origin_access_identity)

        distribution = cloudfront.Distribution(
            self,
            "ci_cdn",
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404, response_page_path="/index.html"
                )
            ],
            default_behavior=cloudfront.BehaviorOptions(
                origin=cloudfront_origins.S3Origin(
                    webapp_bucket, origin_access_identity=origin_access_identity
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY
            ),
        )

        web_deployment = s3_deployment.BucketDeployment(
            self,
            "ci_web_app_deployment",
            sources=[
                s3_deployment.Source.asset(os.path.join("./web_app/ci-portal/build")),
            ],
            distribution=distribution,
            destination_bucket=webapp_bucket,
        )

        lambda_role = iam.Role(
            self,
            "ci_app_role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "SecretsManagerReadWrite"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSageMakerFullAccess"
                ),
            ],
        )

        proxy_func = _lambda.Function(
            self,
            "proxy_fn",
            runtime=ci_lambda_runtime,
            handler="proxy.handler",
            code=_lambda.Code.from_asset("web_app/lambdas"),
            role=lambda_role,
        )

        user_pool = cognito.UserPool(
            self,
            "user_pool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
        )

        cognito_app_client = cognito.UserPoolClient(
            self, "user_pool_client_id", user_pool=user_pool, generate_secret=False
        )

        user_pool_auth_provider = UserPoolAuthenticationProvider(
            user_pool=user_pool, user_pool_client=cognito_app_client
        )
        identity_pool_auth_providers = IdentityPoolAuthenticationProviders(
            user_pools=[user_pool_auth_provider]
        )

        cognito_idp = id_pool.IdentityPool(
            self,
            "identity_provider",
            allow_unauthenticated_identities=False,
            authentication_providers=identity_pool_auth_providers,
        )

        cognito_http_authorizer = gtwy_auth.HttpUserPoolAuthorizer(
            "http_authorizer", user_pool, user_pool_clients=[cognito_app_client]
        )

        api_log_group = logs.LogGroup(self, "ci_api_logs")
        api_log_group.grant_write(cognito_idp.authenticated_role)

        rest_api = api_gtwy.RestApi(
            self,
            "ci_rest_api",
            cloud_watch_role=True,
            deploy_options=api_gtwy.StageOptions(
                stage_name="dev",
                access_log_destination=api_gtwy.LogGroupLogDestination(
                    log_group=api_log_group
                ),
                access_log_format=api_gtwy.AccessLogFormat.json_with_standard_fields(
                    caller=True,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=True,
                ),
            ),
            default_cors_preflight_options=api_gtwy.CorsOptions(
                allow_headers=[
                    "Content-Type",
                    "X-Amz-Date",
                    "Authorization",
                    "X-Api-Key",
                    "x-amz-security-token",
                ],
                allow_methods=["OPTIONS", "GET", "POST", "PUT", "PATCH", "DELETE"],
                allow_origins=["*"],
                allow_credentials=True,
                max_age=Duration.seconds(300),
            ),
        )

        client_metric = rest_api.metric_count()

        list_fn = _lambda.Function(
            self,
            "list_api_fn",
            runtime=ci_lambda_runtime,
            handler="list_conversations.handler",
            code=_lambda.Code.from_asset("web_app/lambdas"),
            role=lambda_role,
            environment={"UploadsTable": uploads_table.table_name},
        )
        list_fn.grant_invoke(cognito_idp.authenticated_role)
        uploads_table.grant_full_access(cognito_idp.authenticated_role)

        uploads_table.grant_read_write_data(list_fn.role)
        uploads_table.grant_read_write_data(cognito_idp.authenticated_role)

        list_api = rest_api.root.add_resource("list")
        list_fn_integration = api_gtwy.LambdaIntegration(
            credentials_passthrough=True,
            handler=list_fn,
        )
        list_api.add_method(
            http_method="ANY",
            authorization_type=api_gtwy.AuthorizationType(
                api_gtwy.AuthorizationType.IAM
            ),
            integration=list_fn_integration,
        ).grant_execute(cognito_idp.authenticated_role)

        details_fn = _lambda.Function(
            self,
            "details_api_fn",
            runtime=ci_lambda_runtime,
            handler="conversation_detail.handler",
            code=_lambda.Code.from_asset("web_app/lambdas"),
            role=lambda_role,
            environment={"UploadsTable": uploads_table.table_name},
        )
        details_fn.grant_invoke(cognito_idp.authenticated_role)

        details_api = rest_api.root.add_resource("details")
        details_with_id = details_api.add_resource("{key}")
        details_fn_integration = api_gtwy.LambdaIntegration(
            credentials_passthrough=True,
            handler=details_fn,
        )
        details_with_id.add_method(
            http_method="ANY",
            authorization_type=api_gtwy.AuthorizationType(
                api_gtwy.AuthorizationType.IAM
            ),
            integration=details_fn_integration,
        ).grant_execute(cognito_idp.authenticated_role)

        input_bucket.grant_read(details_fn.role)

        # Summarization stack to process output json file
        genai_fn_policy = iam.Policy(
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

        genai_fn = _lambda.Function(
            self,
            "genai_query_api_fn",
            runtime=ci_lambda_runtime,
            handler="genai_query.handler",
            timeout=Duration.minutes(15),
            code=_lambda.Code.from_asset(
                "web_app/lambdas",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install boto3 -t /asset-output && cp -au . /asset-output",
                    ],
                ),
            ),
            role=lambda_role,
            environment={"UploadsTable": uploads_table.table_name},
        )
        genai_fn.grant_invoke(cognito_idp.authenticated_role)
        genai_fn.role.attach_inline_policy(genai_fn_policy)

        genai_api = rest_api.root.add_resource("genai")
        genai_with_id = genai_api.add_resource("{key}")
        genai_fn_integration = api_gtwy.LambdaIntegration(
            credentials_passthrough=True,
            handler=genai_fn,
        )
        genai_with_id.add_method(
            http_method="ANY",
            authorization_type=api_gtwy.AuthorizationType(
                api_gtwy.AuthorizationType.IAM
            ),
            integration=genai_fn_integration,
        ).grant_execute(cognito_idp.authenticated_role)
        input_bucket.grant_read(genai_fn.role)
        chatbot_prompt.grant_read(genai_fn.role)

        prompts_fn = _lambda.Function(
            self,
            "ci_prompts_admin_api_fn",
            runtime=ci_lambda_runtime,
            handler="prompts_admin.handler",
            code=_lambda.Code.from_asset("web_app/lambdas"),
            role=lambda_role,
        )
        prompts_fn.grant_invoke(cognito_idp.authenticated_role)
        prompts_api = rest_api.root.add_resource("prompts")
        prompts_with_id = prompts_api.add_resource("{key}")
        prompts_fn_integration = api_gtwy.LambdaIntegration(
            credentials_passthrough=True,
            handler=prompts_fn,
        )
        prompts_with_id.add_method(
            http_method="ANY",
            authorization_type=api_gtwy.AuthorizationType(
                api_gtwy.AuthorizationType.IAM
            ),
            integration=prompts_fn_integration,
        ).grant_execute(cognito_idp.authenticated_role)

        # [Added By Anup] Lambda to Support User-defined Prompts
        custom_prompt_lambda_role = iam.Role(
            self,
            "ci_custom_prompt_fn_role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"),
            ],
        )
        
        userprompts_fn =  _lambda.Function(
            self,
            "ci_user_prompts_admin_fn",
            runtime=ci_lambda_runtime,
            handler="user_prompts.handler",
            code=_lambda.Code.from_asset("web_app/lambdas"),
            role=custom_prompt_lambda_role,
            environment={"CustomPromptsTable": custom_prompt_table.table_name},
        )
        
        userprompts_fn.grant_invoke(cognito_idp.authenticated_role)
        userprompts_api = rest_api.root.add_resource("custom")
        userprompts_with_id = userprompts_api.add_resource("{key}")
        userprompts_fn_integration = api_gtwy.LambdaIntegration(
            credentials_passthrough=True,
            handler=userprompts_fn,
        )
        
        userprompts_with_id.add_method(
            http_method="ANY",
            authorization_type=api_gtwy.AuthorizationType(
                api_gtwy.AuthorizationType.IAM
            ),
            integration=userprompts_fn_integration,
        ).grant_execute(cognito_idp.authenticated_role)

        web_deployment.add_source(s3_deployment.Source.data(
            "aws-config.js",
            """
const awsmobile = {
    aws_project_region: '"""+aws_cdk.Stack.of(self).region+"""',
    aws_cognito_region: '"""+aws_cdk.Stack.of(self).region+"""',
    aws_cognito_identity_pool_id:'"""+cognito_idp.identity_pool_id+"""',
    aws_user_pools_id:'"""+user_pool.user_pool_id+"""',
    aws_user_pools_web_client_id: '"""+cognito_app_client.user_pool_client_id+"""',
    aws_cognito_username_attributes: ['EMAIL'],
    aws_cognito_mfa_configuration: 'OFF',
    aws_cognito_password_protection_settings: {
        passwordPolicyMinLength: 8,
        passwordPolicyCharacters: ['REQUIRES_LOWERCASE', 'REQUIRES_UPPERCASE', 'REQUIRES_NUMBERS', 'REQUIRES_SYMBOLS'],
    },
    aws_cognito_verification_mechanisms: ['EMAIL'],
    API: {
        endpoints: [
            {
                name: 'ci-api',
                endpoint: '"""+rest_api.url[:-1]+"""',
            },
        ],
    }
};
window.aws_config = awsmobile;
            """
        ))

        CfnOutput(
            self,
            "ci_distribution",
            value=distribution.domain_name,
            export_name="ci-distribution",
        )
        CfnOutput(
            self,
            "ci_api_gateway",
            value=rest_api.url,
            export_name="api-gateway",
        )
        CfnOutput(
            self,
            "ci_user_pool_client_id",
            value=cognito_app_client.user_pool_client_id,
            export_name="user-pool-client-id",
        )
        CfnOutput(
            self,
            "ci_user_pool_id",
            value=user_pool.user_pool_id,
            export_name="user-pool-id",
        )
        CfnOutput(
            self,
            "ci_identity_provider_id",
            value=cognito_idp.identity_pool_id,
            export_name="identity-provider-id",
        )
