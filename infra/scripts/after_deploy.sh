#!/usr/bin/env bash
# After `cdk deploy`: index the corpus inside the VPC and create accounts.
#   AWS_PROFILE=<profile> infra/scripts/after_deploy.sh corpus      # upload caches + run the ingest task
#   AWS_PROFILE=<profile> infra/scripts/after_deploy.sh user <email> [evaluator]
# Reads the outputs of the deployed SdRag-App stack from CloudFormation, so it works the same
# after a deploy by hand and one by CI/CD (deploy.yml writes no outputs file), and never
# picks up the names of an earlier, deleted deployment.
set -euo pipefail
cd "$(dirname "$0")/../.."
REGION=ap-southeast-2
out() {
  local v
  v=$(aws cloudformation describe-stacks --region $REGION --stack-name SdRag-App \
      --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text)
  [ -n "$v" ] && [ "$v" != "None" ] || { echo "SdRag-App has no output $1" >&2; exit 1; }
  echo "$v"
}

case "$1" in
corpus)
  # nori is attached to the search domain after `cdk deploy` returns (10-20 min, blue/green);
  # indexing before it is active fails with "Unknown tokenizer"
  domain=$(aws opensearch list-domain-names --region $REGION --query 'DomainNames[0].DomainName' --output text)
  until [ "$(aws opensearch list-packages-for-domain --region $REGION --domain-name "$domain" \
            --query 'DomainPackageDetailsList[0].DomainPackageStatus' --output text)" = "ACTIVE" ]; do
    echo "waiting for nori on $domain ..."; sleep 30
  done
  vpc=$(aws opensearch describe-domain --region $REGION --domain-name "$domain" \
        --query 'DomainStatus.VPCOptions.VPCId' --output text)
  bucket=$(out Bucket)
  infra/scripts/upload_corpus.sh "$bucket"
  cluster=$(out ClusterName)
  taskdef=$(out IngestTaskDef)
  # the task runs in a public subnet with a public IP (no NAT), in the app security group
  subnet=$(aws ec2 describe-subnets --region $REGION --filters "Name=vpc-id,Values=$vpc" "Name=tag:aws-cdk:subnet-type,Values=Public" \
           --query 'Subnets[0].SubnetId' --output text)
  sg=$(aws ec2 describe-security-groups --region $REGION \
       --filters "Name=vpc-id,Values=$vpc" "Name=description,Values=ECS tasks (API and worker)" --query 'SecurityGroups[0].GroupId' --output text)
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
