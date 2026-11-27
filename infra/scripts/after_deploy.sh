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
# $1: output key; $2: stack (default SdRag-App)
out() {
  local v
  v=$(aws cloudformation describe-stacks --region $REGION --stack-name "${2:-SdRag-App}" \
      --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text)
  [ -n "$v" ] && [ "$v" != "None" ] || { echo "${2:-SdRag-App} has no output $1" >&2; exit 1; }
  echo "$v"
}
usage() {
  echo "usage: $0 corpus | user <email> [evaluator]" >&2
  exit 2
}

case "${1:-}" in  # ${1:-}: no argument gives the usage, not an unbound-variable error under set -u
corpus)
  # nori is attached to the search domain after `cdk deploy` returns (10-20 min, blue/green);
  # indexing before it is active fails with "Unknown tokenizer"
  # the domain by the Data stack's output; a deployment from before that output: the only
  # domain in the Region (warn if there are several, the first may be another one)
  if ! domain=$(out SearchDomainName SdRag-Data 2>/dev/null); then
    domain=$(aws opensearch list-domain-names --region $REGION --query 'DomainNames[0].DomainName' --output text)
    n=$(aws opensearch list-domain-names --region $REGION --query 'length(DomainNames)' --output text)
    [ "$n" = 1 ] || echo "warning: SdRag-Data has no SearchDomainName output and $n domains exist; using $domain" >&2
  fi
  # an assignment, not a test: an AWS CLI error (expired credentials) stops the script
  # under set -e instead of looping; ASSOCIATION_FAILED and 30 min without ACTIVE fail too
  deadline=$((SECONDS + 1800))
  while :; do
    st=$(aws opensearch list-packages-for-domain --region $REGION --domain-name "$domain" \
         --query 'DomainPackageDetailsList[0].DomainPackageStatus' --output text)
    case "$st" in
    ACTIVE) break ;;
    ASSOCIATION_FAILED) echo "nori association failed on $domain (aws opensearch list-packages-for-domain)" >&2; exit 1 ;;
    esac
    [ $SECONDS -lt $deadline ] || { echo "nori not ACTIVE on $domain after 30 min (status $st)" >&2; exit 1; }
    echo "waiting for nori on $domain ($st) ..."; sleep 30
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
  run=$(aws ecs run-task --region $REGION --cluster "$cluster" --task-definition "$taskdef" --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$subnet],securityGroups=[$sg],assignPublicIp=ENABLED}" \
    --output json)
  # run-task succeeds even when no task started: the reason is in "failures"
  task=$(python3 -c 'import json,sys;d=json.load(sys.stdin);t=d.get("tasks") or [{}];print("" if d.get("failures") else t[0].get("taskArn",""))' <<<"$run")
  [ -n "$task" ] || { echo "ingest task did not start: $run" >&2; exit 1; }
  echo "ingest task $task"
  logs_hint="aws logs tail $(out WorkerLogGroup) --region $REGION --log-stream-name-prefix ingest --since 1h"
  # the ingest takes ~2-3 min; the waiter gives up after 10
  aws ecs wait tasks-stopped --region $REGION --cluster "$cluster" --tasks "$task" \
    || { echo "ingest task still running or unknown after 10 min; logs: $logs_hint" >&2; exit 1; }
  code=$(aws ecs describe-tasks --region $REGION --cluster "$cluster" --tasks "$task" \
         --query 'tasks[0].containers[0].exitCode' --output text)
  if [ "$code" != 0 ]; then
    reason=$(aws ecs describe-tasks --region $REGION --cluster "$cluster" --tasks "$task" \
             --query 'tasks[0].stoppedReason' --output text)
    echo "ingest task failed (exit code $code, $reason); logs: $logs_hint" >&2
    exit 1
  fi
  echo "corpus indexed"
  ;;
user)
  [ $# -ge 2 ] || usage
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
*)
  usage
  ;;
esac
