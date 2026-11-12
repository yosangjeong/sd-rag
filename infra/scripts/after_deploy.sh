#!/usr/bin/env bash
# After `cdk deploy`: index the corpus inside the VPC and create accounts.
#   AWS_PROFILE=<profile> infra/scripts/after_deploy.sh corpus      # upload caches + run the ingest task
#   AWS_PROFILE=<profile> infra/scripts/after_deploy.sh user <email> [evaluator]
# Reads the stack outputs from data/raw/cdk-outputs.json (cdk deploy --outputs-file).
set -euo pipefail
cd "$(dirname "$0")/../.."
out() { python3 -c "import json;print(json.load(open('data/raw/cdk-outputs.json'))['SdRag-App']['$1'])"; }
REGION=ap-southeast-2

case "$1" in
corpus)
  bucket=$(out Bucket)
  infra/scripts/upload_corpus.sh "$bucket"
  cluster=$(out ClusterName)
  taskdef=$(out IngestTaskDef)
  # the task runs in a public subnet with a public IP (no NAT), in the app security group
  subnet=$(aws ec2 describe-subnets --region $REGION --filters "Name=tag:aws-cdk:subnet-type,Values=Public" \
           --query 'Subnets[0].SubnetId' --output text)
  sg=$(aws ec2 describe-security-groups --region $REGION \
       --filters "Name=description,Values=ECS tasks (API and worker)" --query 'SecurityGroups[0].GroupId' --output text)
  aws ecs run-task --region $REGION --cluster "$cluster" --task-definition "$taskdef" --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$subnet],securityGroups=[$sg],assignPublicIp=ENABLED}" \
    --query 'tasks[0].taskArn' --output text
  ;;
user)
  pool=$(out UserPoolId)
  email="$2"
  pw="$(python3 -c 'import secrets,string;a=string.ascii_letters+string.digits;print("Sd-"+"".join(secrets.choice(a) for _ in range(16))+"9!")')"
  aws cognito-idp admin-create-user --region $REGION --user-pool-id "$pool" --username "$email" \
    --user-attributes Name=email,Value="$email" Name=email_verified,Value=true --message-action SUPPRESS >/dev/null
  aws cognito-idp admin-set-user-password --region $REGION --user-pool-id "$pool" --username "$email" \
    --password "$pw" --permanent
  if [ "${3:-}" = "evaluator" ]; then
    aws cognito-idp admin-add-user-to-group --region $REGION --user-pool-id "$pool" --username "$email" \
      --group-name evaluators
  fi
  echo "user $email password $pw"
  ;;
esac
