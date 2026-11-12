"""GitHub Actions access to AWS without stored keys (OIDC).

GitHub's token for a workflow run is exchanged for short-lived credentials of these
roles; the trust policy accepts only this repository:

- DeployRole (main branch only): assumes the CDK bootstrap roles, which do the actual
  deployment (cdk deploy), so this role itself holds no broad permissions.
- EvalRole (any branch or pull request of the repository): invokes the Bedrock models
  the retrieval uses and reads the corpus from S3, for the evaluation gate
  (.github/workflows/eval.yml). Read-only plus model calls: a pull request cannot
  change anything in the project.

Deployed once by hand (cdk deploy SdRag-CiCd); the role ARNs then go to the
repository's Actions variables.
"""

from aws_cdk import CfnOutput, Duration, Stack
from aws_cdk import aws_iam as iam
from constructs import Construct

REPO = "yosangjeong/sd-rag"


class CiCdStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, bucket_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        provider = iam.OpenIdConnectProvider(
            self,
            "GitHub",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
        )

        def principal(sub: str) -> iam.WebIdentityPrincipal:
            return iam.WebIdentityPrincipal(
                provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                    },
                    "StringLike": {"token.actions.githubusercontent.com:sub": sub},
                },
            )

        deploy = iam.Role(
            self,
            "DeployRole",
            assumed_by=principal(f"repo:{REPO}:ref:refs/heads/main"),
            max_session_duration=Duration.hours(1),
        )
        deploy.add_to_policy(
            iam.PolicyStatement(
                actions=["sts:AssumeRole"],
                resources=[f"arn:aws:iam::{self.account}:role/cdk-*-{self.account}-{self.region}"],
            )
        )

        evaluate = iam.Role(
            self,
            "EvalRole",
            assumed_by=principal(f"repo:{REPO}:*"),
            max_session_duration=Duration.hours(1),
        )
        evaluate.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=[
                    f"arn:aws:bedrock:{self.region}::foundation-model/{m}"
                    for m in (
                        "amazon.titan-embed-text-v2:0",
                        "zai.glm-4.7",
                        "qwen.qwen3-vl-235b-a22b",
                    )
                ],
            )
        )
        evaluate.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:ListBucket"],
                resources=[f"arn:aws:s3:::{bucket_name}", f"arn:aws:s3:::{bucket_name}/corpus/*"],
            )
        )
        CfnOutput(self, "DeployRoleArn", value=deploy.role_arn)
        CfnOutput(self, "EvalRoleArn", value=evaluate.role_arn)
