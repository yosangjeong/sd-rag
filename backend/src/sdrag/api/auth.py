"""Who is calling: a Cognito user, proven by the ID token the browser sends.

The frontend signs in with the Cognito hosted login page and sends the ID token as
``Authorization: Bearer <jwt>``. The API checks, with PyJWT and the user pool's
public keys (JWKS, fetched once and cached):

- signature (RS256, a key of this user pool), expiry, issuer = this user pool,
  audience = our app client, token_use = "id"

The user id is the token's ``sub``. Nothing else from the request is trusted for
identity, so a user cannot act as another by changing a header or a parameter.

Group membership comes from the same token (``cognito:groups``): members of
"evaluators" may also read the service logs (logs_api.py).

Locally (settings.auth_mode = "dev") the user is taken from the X-Dev-User header
(default "dev-user") and groups from X-Dev-Groups; the setting cannot be "dev" in AWS
(config.py refuses it).
"""

from functools import lru_cache

import jwt
from fastapi import Header, HTTPException

from sdrag.common.config import settings


@lru_cache(maxsize=1)
def _jwks() -> jwt.PyJWKClient:
    url = (f"https://cognito-idp.{settings.aws_region}.amazonaws.com/"
           f"{settings.cognito_user_pool_id}/.well-known/jwks.json")  # fmt: skip
    return jwt.PyJWKClient(url, cache_keys=True)


def claims_of(token: str) -> dict:
    """The claims of a valid ID token; raises jwt.InvalidTokenError otherwise."""
    key = _jwks().get_signing_key_from_jwt(token).key
    issuer = (
        f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{settings.cognito_user_pool_id}"
    )
    claims = jwt.decode(token, key, algorithms=["RS256"], audience=settings.cognito_client_id,
                        issuer=issuer, options={"require": ["exp", "sub", "iss", "aud"]})  # fmt: skip
    if claims.get("token_use") != "id":
        raise jwt.InvalidTokenError("not an ID token")
    return claims


def _claims(authorization: str | None, x_dev_user: str | None, x_dev_groups: str | None) -> dict:
    if settings.auth_mode == "dev":
        groups = [g for g in (x_dev_groups or "").split(",") if g]
        return {"sub": x_dev_user or "dev-user", "cognito:groups": groups}
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "sign-in required")
    try:
        return claims_of(authorization.split(" ", 1)[1])
    except jwt.InvalidTokenError as e:
        raise HTTPException(401, "invalid or expired token") from e


def current_user(authorization: str | None = Header(default=None),
                 x_dev_user: str | None = Header(default=None),
                 x_dev_groups: str | None = Header(default=None)) -> str:  # fmt: skip
    return _claims(authorization, x_dev_user, x_dev_groups)["sub"]


EVALUATORS = "evaluators"  # Cognito group of the evaluator accounts: may read the logs


def current_evaluator(authorization: str | None = Header(default=None),
                      x_dev_user: str | None = Header(default=None),
                      x_dev_groups: str | None = Header(default=None)) -> str:  # fmt: skip
    """A signed-in member of the evaluators group (403 for anyone else)."""
    claims = _claims(authorization, x_dev_user, x_dev_groups)
    if EVALUATORS not in claims.get("cognito:groups", []):
        raise HTTPException(403, "evaluators only")
    return claims["sub"]
