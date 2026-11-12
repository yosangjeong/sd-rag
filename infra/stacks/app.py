"""The running service: API and worker on ECS Fargate, the web app on CloudFront.

    browser --HTTPS--> CloudFront --/api/*--> ALB --> API tasks --> OpenSearch, Bedrock,
                           |                                       DynamoDB, S3, SQS
                           +--/*--> S3 (React build)               worker tasks <-- SQS

- One container image (backend/Dockerfile), built by CDK from the repository at deploy
  time; the API and the worker run it with different commands.
- API: 1 task (0.5 vCPU, 1 GB), behind a public ALB that answers only requests
  carrying a header CloudFront adds (X-Origin-Verify), so the ALB cannot be used
  directly. CloudFront gives HTTPS without a domain of our own.
- Worker: scales on the upload queue's depth, 0 tasks when the queue is empty, up to
  2 while files wait: throughput for a 50+ file batch without paying for idle tasks.
- IAM: each task role gets only what it uses (grant_* calls), Bedrock limited to
  invoking models in this Region.
- Logs: both services write JSON lines to CloudWatch Logs (14 days).
- OpenSearch access: the task roles' identity policies (grant_read_write) plus the
  security group; the domain's own policy defers to IAM in this account (data.py).
- The SPA's /config.json (Cognito settings) is written at deploy time.
"""

import os
from pathlib import Path

from aws_cdk import CfnOutput, DockerBuildSecret, Duration, Fn, RemovalPolicy, Stack
from aws_cdk import aws_applicationautoscaling as appscaling
from aws_cdk import aws_cloudfront as cf
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as patterns
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from aws_cdk.aws_ecr_assets import Platform
from constructs import Construct

from stacks.data import DataStack
from stacks.network import API_PORT, NetworkStack

ROOT = Path(__file__).resolve().parents[2]
MODELS = ["amazon.titan-embed-text-v2:0", "zai.glm-4.7", "qwen.qwen3-vl-235b-a22b"]


class AppStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, network: NetworkStack, data: DataStack, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        cluster = ecs.Cluster(
            self, "Cluster", vpc=network.vpc, container_insights_v2=ecs.ContainerInsights.DISABLED
        )
        # SDRAG_BUILD_CA: a CA to trust during the image build only, for a network that
        # re-signs TLS (passed as a BuildKit secret, not copied into the image); unset in CI
        ca = os.environ.get("SDRAG_BUILD_CA")
        secrets = {"extra_ca": DockerBuildSecret.from_src(ca)} if ca else None
        image = ecs.ContainerImage.from_asset(
            str(ROOT / "backend"), platform=Platform.LINUX_AMD64, build_secrets=secrets
        )
        # log groups are kept when the stack is deleted or rolled back: the logs of a
        # failed start are what explain it
        api_logs = logs.LogGroup(
            self,
            "ApiLogs",
            retention=logs.RetentionDays.TWO_WEEKS,
            removal_policy=RemovalPolicy.RETAIN,
        )
        worker_logs = logs.LogGroup(
            self,
            "WorkerLogs",
            retention=logs.RetentionDays.TWO_WEEKS,
            removal_policy=RemovalPolicy.RETAIN,
        )
        # a value only CloudFront and the ALB know: derived from this stack's UUID, which
        # is not in the repository
        origin_secret = Fn.select(2, Fn.split("/", self.stack_id))

        site = s3.Bucket(
            self,
            "Site",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        env = {
            "SDRAG_ENV": "aws",
            "SDRAG_AUTH_MODE": "cognito",
            "SDRAG_OPENSEARCH_URL": f"https://{data.search.domain_endpoint}",
            "SDRAG_TABLE": data.table.table_name,
            "SDRAG_UPLOAD_BUCKET": data.bucket.bucket_name,
            "SDRAG_UPLOAD_QUEUE_URL": data.queue.queue_url,
            "SDRAG_COGNITO_USER_POOL_ID": data.user_pool.user_pool_id,
        }

        # ---- API ----
        # the ALB uses the network stack's security groups, so the rules between layers
        # stay in one place (network.py) and no stack refers back to this one
        lb = elbv2.ApplicationLoadBalancer(
            self,
            "Lb",
            vpc=network.vpc,
            internet_facing=True,
            security_group=network.alb_sg,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )
        api = patterns.ApplicationLoadBalancedFargateService(
            self,
            "Api",
            cluster=cluster,
            load_balancer=lb,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=1,
            assign_public_ip=True,  # public subnets, no NAT gateway (network.py)
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_groups=[network.app_sg],
            task_image_options=patterns.ApplicationLoadBalancedTaskImageOptions(
                image=image,
                container_port=API_PORT,
                command=[
                    "uvicorn",
                    "sdrag.api.main:app",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    str(API_PORT),
                    "--no-access-log",  # requests are logged as JSON by the app (masked)
                ],
                environment=env,
                log_driver=ecs.LogDrivers.aws_logs(stream_prefix="api", log_group=api_logs),
            ),
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
            min_healthy_percent=100,  # one task: start the new one before stopping the old
            open_listener=False,
        )
        api.target_group.configure_health_check(path="/health", healthy_http_codes="200")
        # requests without CloudFront's header get 403
        api.listener.add_action(
            "FromCloudFront",
            priority=1,
            conditions=[elbv2.ListenerCondition.http_header("X-Origin-Verify", [origin_secret])],
            action=elbv2.ListenerAction.forward([api.target_group]),
        )
        cfn_listener = api.listener.node.default_child
        cfn_listener.add_property_override(
            "DefaultActions",
            [
                {
                    "Type": "fixed-response",
                    "FixedResponseConfig": {
                        "StatusCode": "403",
                        "ContentType": "text/plain",
                        "MessageBody": "forbidden",
                    },
                }
            ],
        )

        # ---- worker ----
        worker = patterns.QueueProcessingFargateService(
            self,
            "Worker",
            cluster=cluster,
            cpu=1024,
            memory_limit_mib=4096,  # PDF parsing and page images for OCR
            image=image,
            command=["python", "-m", "sdrag.worker.main"],
            queue=data.queue,
            environment=env,
            min_scaling_capacity=0,
            min_healthy_percent=0,
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
            max_scaling_capacity=2,  # a t3.small search node takes two bulk writers
            scaling_steps=[
                appscaling.ScalingInterval(upper=0, change=-4),
                appscaling.ScalingInterval(lower=1, change=+1),
                appscaling.ScalingInterval(lower=20, change=+1),
            ],
            assign_public_ip=True,
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_groups=[network.app_sg],
            log_driver=ecs.LogDrivers.aws_logs(stream_prefix="worker", log_group=worker_logs),
        )

        # ---- one-off bulk index of the public corpus (ingest/from_s3.py) ----
        # run: aws ecs run-task --cluster <cluster> --task-definition <IngestTask> ...
        self.ingest_task = ecs.FargateTaskDefinition(
            self, "IngestTask", cpu=2048, memory_limit_mib=8192
        )
        self.ingest_task.add_container(
            "ingest",
            image=image,
            command=["python", "-m", "sdrag.ingest.from_s3"],
            environment=env,
            logging=ecs.LogDrivers.aws_logs(stream_prefix="ingest", log_group=worker_logs),
        )
        data.bucket.grant_read_write(self.ingest_task.task_role, "corpus/*")

        # a worker marks itself protected from scale-in while it holds a job (worker/main.py)
        worker.task_definition.task_role.add_to_principal_policy(
            iam.PolicyStatement(
                actions=["ecs:UpdateTaskProtection", "ecs:GetTaskProtection"],
                resources=[
                    f"arn:aws:ecs:{self.region}:{self.account}:task/{cluster.cluster_name}/*"
                ],
            )
        )

        # after an upload the API starts a worker task if there is none (worker/sqs.py)
        api.task_definition.default_container.add_environment(
            "SDRAG_WORKER_CLUSTER", cluster.cluster_name
        )
        api.task_definition.default_container.add_environment(
            "SDRAG_WORKER_SERVICE", worker.service.service_name
        )
        api.task_definition.task_role.add_to_principal_policy(
            iam.PolicyStatement(
                actions=["ecs:DescribeServices", "ecs:UpdateService"],
                resources=[worker.service.service_arn],
            )
        )

        # the log viewer (api/logs_api.py) runs Logs Insights queries on both groups
        api.task_definition.default_container.add_environment(
            "SDRAG_LOG_GROUPS", f"{api_logs.log_group_name},{worker_logs.log_group_name}"
        )
        api.task_definition.task_role.add_to_principal_policy(
            iam.PolicyStatement(
                actions=["logs:StartQuery"],
                resources=[api_logs.log_group_arn, worker_logs.log_group_arn],
            )
        )
        api.task_definition.task_role.add_to_principal_policy(
            iam.PolicyStatement(actions=["logs:GetQueryResults"], resources=["*"])
        )  # takes no resource

        # ---- permissions ----
        bedrock = iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],  # Converse calls are authorized as InvokeModel
            resources=[f"arn:aws:bedrock:{self.region}::foundation-model/{m}" for m in MODELS],
        )
        roles = (
            api.task_definition.task_role,
            worker.task_definition.task_role,
            self.ingest_task.task_role,
        )
        for role in roles:
            role.add_to_principal_policy(bedrock)
            data.table.grant_read_write_data(role)
            data.search.grant_read_write(role)
        data.bucket.grant_put(api.task_definition.task_role, "uploads/*")
        data.queue.grant_send_messages(api.task_definition.task_role)
        data.bucket.grant_read(worker.task_definition.task_role, "uploads/*")

        # ---- web ----
        dist = cf.Distribution(
            self,
            "Web",
            default_root_object="index.html",
            default_behavior=cf.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(site),
                viewer_protocol_policy=cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            additional_behaviors={
                "/api/*": cf.BehaviorOptions(
                    origin=origins.LoadBalancerV2Origin(
                        api.load_balancer,
                        protocol_policy=cf.OriginProtocolPolicy.HTTP_ONLY,
                        custom_headers={"X-Origin-Verify": origin_secret},
                        read_timeout=Duration.seconds(60),
                    ),
                    viewer_protocol_policy=cf.ViewerProtocolPolicy.HTTPS_ONLY,
                    allowed_methods=cf.AllowedMethods.ALLOW_ALL,
                    cache_policy=cf.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cf.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                )
            },
        )
        url = f"https://{dist.distribution_domain_name}"

        client = cognito.UserPoolClient(
            self,
            "WebClient",
            user_pool=data.user_pool,
            generate_secret=False,  # a browser app cannot keep a secret; PKCE instead
            # admin password auth needs AWS credentials (scripted checks: eval/upload_bench.py);
            # the browser signs in on the managed login page
            auth_flows=cognito.AuthFlow(admin_user_password=True, user_srp=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[cognito.OAuthScope.OPENID, cognito.OAuthScope.EMAIL],
                callback_urls=[f"{url}/"],
                logout_urls=[f"{url}/"],
            ),
            id_token_validity=Duration.hours(1),
        )
        cognito.CfnManagedLoginBranding(
            self,
            "LoginBranding",
            user_pool_id=data.user_pool.user_pool_id,
            client_id=client.user_pool_client_id,
            use_cognito_provided_values=True,
        )
        for td in (api.task_definition, worker.task_definition):
            td.default_container.add_environment(
                "SDRAG_COGNITO_CLIENT_ID", client.user_pool_client_id
            )

        s3deploy.BucketDeployment(
            self,
            "SiteFiles",
            destination_bucket=site,
            distribution=dist,
            sources=[
                s3deploy.Source.asset(str(ROOT / "frontend" / "dist")),
                s3deploy.Source.json_data(
                    "config.json",
                    {
                        "authority": f"https://cognito-idp.{self.region}.amazonaws.com/{data.user_pool.user_pool_id}",
                        "clientId": client.user_pool_client_id,
                        "domain": data.login_domain.base_url(),
                    },
                ),
            ],
        )

        CfnOutput(self, "Url", value=url)
        CfnOutput(self, "UserPoolId", value=data.user_pool.user_pool_id)
        CfnOutput(self, "ApiLogGroup", value=api_logs.log_group_name)
        CfnOutput(self, "WorkerLogGroup", value=worker_logs.log_group_name)
        CfnOutput(self, "ClusterName", value=cluster.cluster_name)
        CfnOutput(self, "IngestTaskDef", value=self.ingest_task.task_definition_arn)
        CfnOutput(self, "Bucket", value=data.bucket.bucket_name)
