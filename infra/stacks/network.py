"""Network layer: VPC, subnets and security groups.

Assignment-scale design (no NAT gateway, to save ~$43/month):
- PUBLIC subnets: the ALB and the ECS tasks. Tasks get a public IP so they can
  call AWS APIs (Bedrock, ECR, SQS, ...) directly. Their security group only
  accepts traffic from the ALB, so nothing on the internet can reach them.
- ISOLATED subnets: OpenSearch. No route to or from the internet at all.
- S3 gateway endpoint (free): S3 traffic stays on the AWS network.

Production would instead put tasks in private subnets behind NAT or VPC
interface endpoints (see docs/design.md, "Limitations").
"""

from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

API_PORT = 8000


class NetworkStack(Stack):
    @property
    def availability_zones(self) -> list[str]:
        # Fixed AZ list: stops CDK from looking AZs up and caching the result
        # (which includes the account ID) in cdk.context.json.
        return [f"{self.region}a", f"{self.region}b"]

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # An ALB needs subnets in at least two Availability Zones.
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="isolated", subnet_type=ec2.SubnetType.PRIVATE_ISOLATED, cidr_mask=24
                ),
            ],
            gateway_endpoints={
                "S3": ec2.GatewayVpcEndpointOptions(service=ec2.GatewayVpcEndpointAwsService.S3)
            },
        )

        # Security groups are defined here (not in each stack) so the rules
        # between layers are visible in one place:
        #   internet --443/80--> ALB --8000--> app tasks --443--> OpenSearch
        self.alb_sg = ec2.SecurityGroup(
            self, "AlbSg", vpc=self.vpc, description="ALB: public HTTP/HTTPS"
        )
        self.alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "HTTPS from internet")
        self.alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "HTTP (redirect)")

        self.app_sg = ec2.SecurityGroup(
            self, "AppSg", vpc=self.vpc, description="ECS tasks (API and worker)"
        )
        self.app_sg.add_ingress_rule(self.alb_sg, ec2.Port.tcp(API_PORT), "API from ALB only")

        self.search_sg = ec2.SecurityGroup(
            self,
            "SearchSg",
            vpc=self.vpc,
            description="OpenSearch domain",
            allow_all_outbound=False,
        )
        self.search_sg.add_ingress_rule(self.app_sg, ec2.Port.tcp(443), "OpenSearch from app tasks")
