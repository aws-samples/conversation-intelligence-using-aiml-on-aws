#!/usr/bin/env python3

#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import aws_cdk as cdk
from constructs import Construct

from ml_stack.cdk.ml_stack import MLStack
from server.cdk.server_stack import ServerStack
from web_app.cdk.app_stack import WebAppStack


class CIStack(Construct):
    def __init__(self, scope: Construct, id: str, *, prod=False):
        super().__init__(scope, id)

        # Server Stack
        ml_stack = MLStack(app, "ci-ml")

        # Server Stack
        server_stack = ServerStack(app, "ci-process")
        server_stack.add_dependency(ml_stack)

        # UI Stack
        web_stack = WebAppStack(app, "ci-web")
        web_stack.add_dependency(server_stack)

        cdk.Tags.of(scope).add("App", "Conversation Intelligence")


app = cdk.App()
CIStack(app, "prod", prod=True)
app.synth()
