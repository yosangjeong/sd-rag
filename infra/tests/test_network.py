"""Synth-time checks: catch costly or insecure network changes before deploy."""

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from stacks.network import NetworkStack


def _template() -> Template:
    app = cdk.App()
    stack = NetworkStack(
        app, "Test", env=cdk.Environment(account="111111111111", region="ap-southeast-2")
    )
    return Template.from_stack(stack)


def test_no_nat_gateway():
    _template().resource_count_is("AWS::EC2::NatGateway", 0)


def test_two_azs_public_and_isolated():
    # 2 AZs x (public + isolated) = 4 subnets
    _template().resource_count_is("AWS::EC2::Subnet", 4)


def test_s3_gateway_endpoint():
    _template().has_resource_properties(
        "AWS::EC2::VPCEndpoint", {"VpcEndpointType": "Gateway"}
    )


def test_app_tasks_only_reachable_from_alb():
    # The app SG ingress must reference another SG (the ALB), never a CIDR.
    t = _template()
    rules = t.find_resources(
        "AWS::EC2::SecurityGroupIngress", {"Properties": {"FromPort": 8000}}
    )
    assert len(rules) == 1
    props = next(iter(rules.values()))["Properties"]
    assert "SourceSecurityGroupId" in props and "CidrIp" not in props


def test_opensearch_sg_has_no_cidr_ingress():
    t = _template()
    t.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {"GroupDescription": "OpenSearch domain", "SecurityGroupIngress": Match.absent()},
    )
