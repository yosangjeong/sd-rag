"""CDK app entrypoint.

All Regional resources go to the project's selected Region (ap-southeast-2).
The account ID is not hard-coded: the CDK CLI fills CDK_DEFAULT_ACCOUNT from
the current AWS credentials, so the public repo does not expose it.
"""

import os

import aws_cdk as cdk

from stacks.app import AppStack
from stacks.cicd import CiCdStack
from stacks.data import DataStack
from stacks.network import NetworkStack

REGION = "ap-southeast-2"

app = cdk.App()
env = cdk.Environment(account=os.environ.get("CDK_DEFAULT_ACCOUNT"), region=REGION)

network = NetworkStack(app, "SdRag-Network", env=env)
# termination protection for the real deployment; a rehearsal passes -c rehearsal=true
rehearsal = app.node.try_get_context("rehearsal") == "true"
data = DataStack(app, "SdRag-Data", network=network, env=env, termination_protection=not rehearsal)
AppStack(app, "SdRag-App", network=network, data=data, env=env)
CiCdStack(app, "SdRag-CiCd", bucket_name=data.bucket.bucket_name, env=env)

cdk.Tags.of(app).add("project", "sd-rag")

app.synth()
