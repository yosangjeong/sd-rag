"""Synth-time checks of the data and app stacks: security settings that must hold."""

from functools import lru_cache

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from stacks.app import AppStack
from stacks.data import DataStack
from stacks.network import NetworkStack


@lru_cache(maxsize=1)
def _templates() -> tuple[Template, Template]:
    app = cdk.App()
    env = cdk.Environment(account="111111111111", region="ap-southeast-2")
    net = NetworkStack(app, "N", env=env)
    data = DataStack(app, "D", network=net, env=env)
    app_stack = AppStack(app, "A", network=net, data=data, env=env)
    return Template.from_stack(data), Template.from_stack(app_stack)


def test_opensearch_in_vpc_https_encrypted():
    data, _ = _templates()
    data.has_resource_properties(
        "AWS::OpenSearchService::Domain",
        {
            "VPCOptions": Match.object_like({"SubnetIds": Match.any_value()}),
            "DomainEndpointOptions": Match.object_like({"EnforceHTTPS": True}),
            "EncryptionAtRestOptions": {"Enabled": True},
            "NodeToNodeEncryptionOptions": {"Enabled": True},
        },
    )


def test_no_self_sign_up():
    data, _ = _templates()
    data.has_resource_properties(
        "AWS::Cognito::UserPool", {"AdminCreateUserConfig": {"AllowAdminCreateUserOnly": True}}
    )


def test_buckets_block_public_access():
    data, app = _templates()
    for t in (data, app):
        for b in t.find_resources("AWS::S3::Bucket").values():
            assert b["Properties"]["PublicAccessBlockConfiguration"]["BlockPublicPolicy"] is True


def test_alb_refuses_requests_without_the_cloudfront_header():
    _, app = _templates()
    app.has_resource_properties(
        "AWS::ElasticLoadBalancingV2::Listener",
        {"DefaultActions": [Match.object_like({"Type": "fixed-response"})]},
    )
    app.has_resource_properties(
        "AWS::ElasticLoadBalancingV2::ListenerRule",
        {"Conditions": [Match.object_like({"Field": "http-header"})]},
    )


def test_bedrock_access_is_limited_to_named_models():
    _, app = _templates()
    for p in app.find_resources("AWS::IAM::Policy").values():
        for st in p["Properties"]["PolicyDocument"]["Statement"]:
            if st["Action"] == "bedrock:InvokeModel":
                assert all("foundation-model/" in str(r) for r in st["Resource"])


def test_worker_scales_to_zero():
    _, app = _templates()
    app.has_resource_properties(
        "AWS::ApplicationAutoScaling::ScalableTarget", {"MinCapacity": 0, "MaxCapacity": 2}
    )
