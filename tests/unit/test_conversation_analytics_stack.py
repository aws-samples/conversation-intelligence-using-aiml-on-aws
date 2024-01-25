#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import aws_cdk as core
import aws_cdk.assertions as assertions
from conversation_analytics.conversation_analytics_stack import ConversationAnalyticsStack


def test_sqs_queue_created():
    app = core.App()
    stack = ConversationAnalyticsStack(app, "conversation-analytics")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::SQS::Queue", {
        "VisibilityTimeout": 300
    })


def test_sns_topic_created():
    app = core.App()
    stack = ConversationAnalyticsStack(app, "conversation-analytics")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::SNS::Topic", 1)
