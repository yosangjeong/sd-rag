"""claims_of: an ID token of our user pool and app client is accepted; anything else
is refused. Tokens are signed with a local RSA key standing in for Cognito's."""

import time
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from sdrag.api import auth

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
POOL, CLIENT = "ap-southeast-2_TEST", "client-123"
ISS = f"https://cognito-idp.ap-southeast-2.amazonaws.com/{POOL}"


@pytest.fixture(autouse=True)
def pool(monkeypatch):
    monkeypatch.setattr(auth.settings, "cognito_user_pool_id", POOL)
    monkeypatch.setattr(auth.settings, "cognito_client_id", CLIENT)
    monkeypatch.setattr(auth.settings, "aws_region", "ap-southeast-2")
    jwks = SimpleNamespace(get_signing_key_from_jwt=lambda t: SimpleNamespace(key=KEY.public_key()))
    monkeypatch.setattr(auth, "_jwks", lambda: jwks)


def token(**over):
    claims = {"sub": "u-1", "iss": ISS, "aud": CLIENT, "token_use": "id",
              "exp": int(time.time()) + 600} | over  # fmt: skip
    return jwt.encode(claims, KEY, algorithm="RS256")


def test_an_id_token_of_the_pool_is_accepted():
    assert auth.claims_of(token())["sub"] == "u-1"


@pytest.mark.parametrize("over", [
    {"aud": "another-client"},
    {"iss": "https://cognito-idp.ap-southeast-2.amazonaws.com/other-pool"},
    {"token_use": "access"},
    {"exp": int(time.time()) - 10},
])  # fmt: skip
def test_other_tokens_are_refused(over):
    with pytest.raises(jwt.PyJWTError):
        auth.claims_of(token(**over))


def test_a_token_signed_by_another_key_is_refused():
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    forged = jwt.encode({"sub": "u-1", "iss": ISS, "aud": CLIENT, "token_use": "id",
                         "exp": int(time.time()) + 600}, other, algorithm="RS256")  # fmt: skip
    with pytest.raises(jwt.PyJWTError):
        auth.claims_of(forged)
