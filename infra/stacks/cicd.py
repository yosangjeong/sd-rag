"""GitHub Actions access to AWS without stored keys (OIDC).

GitHub's token for a workflow run is exchanged for short-lived credentials of these
roles; the trust policy accepts only this repository:

- DeployRole (jobs in the `aws` environment only, which allows the main branch): assumes the CDK bootstrap roles, which do the actual
  deployment (cdk deploy), so this role itself holds no broad permissions.
- EvalRole (pull requests and main of the repository): invokes the Bedrock models
  the retrieval uses and Textract (the OCR check), and reads the corpus from S3, for the evaluation gate
  (.github/workflows/eval.yml). Read-only plus model calls: a pull request cannot
  change anything in the project.

Deployed once by hand (cdk deploy SdRag-CiCd); the role ARNs then go to the
repository's Actions variables.
"""

from aws_cdk import CfnOutput, Duration, Stack
from aws_cdk import aws_iam as iam
from constructs import Construct

from stacks.app import MODELS

# GitHub's token subject, in the immutable form the repository uses ("use_immutable_subject":
# owner and repository names carry their numeric IDs, so a deleted and re-created repository
# with the same name does not match). Check with:
#   gh api repos/yosangjeong/sd-rag/actions/oidc/customization/sub
REPO = "yosangjeong@22970102/sd-rag@1456241745"


class CiCdStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, bucket_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        provider = iam.OpenIdConnectProvider(
            self,
            "GitHub",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
        )

        def principal(sub: list[str]) -> iam.WebIdentityPrincipal:
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
            # a job with `environment: aws` (deploy.yml) gets the subject
            # "repo:<repo>:environment:aws"; the environment allows the main branch only
            # (repository settings). No ":ref:refs/heads/main" subject: any workflow on main
            # without the environment (and its protection rules) could then deploy
            assumed_by=principal([f"repo:{REPO}:environment:aws"]),
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
            assumed_by=principal([f"repo:{REPO}:pull_request", f"repo:{REPO}:ref:refs/heads/main"]),
            max_session_duration=Duration.hours(1),
        )
        evaluate.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                # the same models as the service roles (app.py), so a model change
                # reaches the gate too
                resources=[f"arn:aws:bedrock:{self.region}::foundation-model/{m}" for m in MODELS],
            )
        )
        # the index step OCRs with the Textract check on (backend config ocr_check=True);
        # Textract accepts only "*" as the resource
        evaluate.add_to_policy(
            iam.PolicyStatement(actions=["textract:AnalyzeDocument"], resources=["*"])
        )
        evaluate.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:ListBucket"],
                resources=[f"arn:aws:s3:::{bucket_name}", f"arn:aws:s3:::{bucket_name}/corpus/*"],
            )
        )
        CfnOutput(self, "DeployRoleArn", value=deploy.role_arn)
        CfnOutput(self, "EvalRoleArn", value=evaluate.role_arn)
