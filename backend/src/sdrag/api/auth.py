"""Who is calling: a Cognito user, proven by the ID token the browser sends.

The frontend signs in with the Cognito hosted login page and sends the ID token as
``Authorization: Bearer <jwt>``. The API checks, with PyJWT and the user pool's
public keys (JWKS, fetched once and cached):

- signature (RS256, a key of this user pool), expiry, issuer = this user pool,
  audience = our app client, token_use = "id"

The user id is the token's ``sub``. Nothing else from the request is trusted for
identity, so a user cannot act as another by changing a header or a parameter.

Locally (settings.auth_mode = "dev") the user is taken from the X-Dev-User header
(default "dev-user"); the setting cannot be "dev" in AWS (config.py refuses it).
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


def verify(token: str) -> str:
    """The user id (sub) of a valid ID token; raises jwt.InvalidTokenError otherwise."""
    key = _jwks().get_signing_key_from_jwt(token).key
    issuer = (
        f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{settings.cognito_user_pool_id}"
    )
    claims = jwt.decode(token, key, algorithms=["RS256"], audience=settings.cognito_client_id,
                        issuer=issuer, options={"require": ["exp", "sub", "iss", "aud"]})  # fmt: skip
    if claims.get("token_use") != "id":
        raise jwt.InvalidTokenError("not an ID token")
    return claims["sub"]


def current_user(authorization: str | None = Header(default=None),
                 x_dev_user: str | None = Header(default=None)) -> str:  # fmt: skip
    if settings.auth_mode == "dev":
        return x_dev_user or "dev-user"
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "sign-in required")
    try:
        return verify(authorization.split(" ", 1)[1])
    except jwt.InvalidTokenError as e:
        raise HTTPException(401, "invalid or expired token") from e
