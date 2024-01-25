#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

import diarize as myapp

# This is just a simple wrapper for gunicorn to find your app.
# If you want to change the algorithm file, simply change "predictor" above to the
# new file.

app = myapp.app
