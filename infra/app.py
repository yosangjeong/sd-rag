"""CDK app entrypoint. Stacks are added here as the system is built.

All Regional resources go to the project's selected Region (ap-southeast-2).
The account ID is not hard-coded: the CDK CLI fills CDK_DEFAULT_ACCOUNT from
the current AWS credentials, so the public repo does not expose it.
"""

import os

import aws_cdk as cdk

REGION = "ap-southeast-2"

app = cdk.App()
env = cdk.Environment(account=os.environ.get("CDK_DEFAULT_ACCOUNT"), region=REGION)

# Stacks will be registered here, e.g.:
#   NetworkStack(app, "SdRag-Network", env=env)

app.synth()
