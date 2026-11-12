#!/usr/bin/env bash
# Print a Cognito ID token for scripted checks (needs AWS credentials: ADMIN_USER_PASSWORD_AUTH).
#   AWS_PROFILE=<profile> infra/scripts/id_token.sh <email> <password>
set -euo pipefail
cd "$(dirname "$0")/../.."
pool=$(python3 -c "import json;print(json.load(open('data/raw/cdk-outputs.json'))['SdRag-App']['UserPoolId'])")
client=$(aws cognito-idp list-user-pool-clients --region ap-southeast-2 --user-pool-id "$pool" \
         --query 'UserPoolClients[0].ClientId' --output text)
aws cognito-idp admin-initiate-auth --region ap-southeast-2 --user-pool-id "$pool" --client-id "$client" \
  --auth-flow ADMIN_USER_PASSWORD_AUTH --auth-parameters USERNAME="$1",PASSWORD="$2" \
  --query AuthenticationResult.IdToken --output text
