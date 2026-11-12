"""Stateful resources, in a stack of their own so app changes never replace them.

- OpenSearch 3.7 domain (nori is built in on AWS OpenSearch Service), one
  t3.medium.search node in an isolated subnet, reached only from the app security
  group, over HTTPS with IAM (SigV4) auth: no passwords anywhere
- DynamoDB table for per-user records (conversations, upload status), on-demand
- S3 bucket for uploads and for the corpus files / caches used by the bulk ingest
- SQS queue for upload jobs, with a dead-letter queue after 3 failed attempts
- Cognito user pool (admin-created users only: evaluator accounts) and an app client
  for the managed login page (authorization code + PKCE)

Assignment scale: single node, no replicas, no dedicated masters; production would
use 3 AZs and replicas (docs/design.md, limitations).
"""

from aws_cdk import Duration, Fn, RemovalPolicy, Stack
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_dynamodb as ddb
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_opensearchservice as os_
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_sqs as sqs
from constructs import Construct

from stacks.network import NetworkStack

OPENSEARCH_VERSION = os_.EngineVersion.open_search("3.7")  # the version run locally
JOB_TIMEOUT = Duration.minutes(30)  # the longest file (a large scan) must fit


class DataStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, network: NetworkStack, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.search = os_.Domain(
            self,
            "Search",
            version=OPENSEARCH_VERSION,
            vpc=network.vpc,
            vpc_subnets=[ec2.SubnetSelection(subnets=[network.vpc.isolated_subnets[0]])],
            security_groups=[network.search_sg],
            capacity=os_.CapacityConfig(
                data_nodes=1,
                data_node_instance_type="t3.medium.search",
                multi_az_with_standby_enabled=False,
            ),
            ebs=os_.EbsOptions(volume_size=20, volume_type=ec2.EbsDeviceVolumeType.GP3),
            zone_awareness=os_.ZoneAwarenessConfig(enabled=False),
            enforce_https=True,
            node_to_node_encryption=True,
            encryption_at_rest=os_.EncryptionAtRestOptions(enabled=True),
            removal_policy=RemovalPolicy.DESTROY,  # an index can be rebuilt from S3 in minutes
        )

        self.table = ddb.TableV2(
            self,
            "Records",
            partition_key=ddb.Attribute(name="pk", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="sk", type=ddb.AttributeType.STRING),
            billing=ddb.Billing.on_demand(),
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.bucket = s3.Bucket(
            self,
            "Files",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            lifecycle_rules=[s3.LifecycleRule(prefix="uploads/", expiration=Duration.days(30))],
        )

        dlq = sqs.Queue(self, "UploadsDlq", retention_period=Duration.days(14), enforce_ssl=True)
        self.queue = sqs.Queue(
            self,
            "Uploads",
            visibility_timeout=JOB_TIMEOUT,
            enforce_ssl=True,
            dead_letter_queue=sqs.DeadLetterQueue(queue=dlq, max_receive_count=3),
        )

        self.user_pool = cognito.UserPool(
            self,
            "Users",
            self_sign_up_enabled=False,  # evaluator accounts are created by the admin
            sign_in_aliases=cognito.SignInAliases(email=True),
            password_policy=cognito.PasswordPolicy(min_length=12),
            account_recovery=cognito.AccountRecovery.NONE,
            removal_policy=RemovalPolicy.DESTROY,
        )
        # the prefix must be unique across AWS; the account id would be, but the login URL
        # is public, so a piece of this stack's UUID is used instead
        stack_uuid = Fn.select(2, Fn.split("/", self.stack_id))
        self.login_domain = self.user_pool.add_domain(
            "Login",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=Fn.join("-", ["sdrag", Fn.select(0, Fn.split("-", stack_uuid))])
            ),
            managed_login_version=cognito.ManagedLoginVersion.NEWER_MANAGED_LOGIN,
        )
