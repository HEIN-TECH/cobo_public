import base64
import json
from unittest.mock import Mock

import jwt
import pytest
from flask import Flask, g

from app.service import create_token, verify_token
from app.types import Status

TEST_SERVER_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEAzLJd44qbp0N5cXKw0JNxCTQDWtC9X06rYoskRHxf5Tjy0AjW
jOU5NvpwGC4YPoK2U3Ln6YDKVF7W6wyTPePM2ECJE8y8N4B/BXpOx5hWqTmhqtZD
fHR+KRIbkpIAjwTDJD7chINgqY53dC5fJ22F82r4e8g2kwp7C2K6SqgLr5kU/y30
nUDgC5M27O4i1pP84t7qqMeuEAHey9zKJb640PRgUAXAWAZhL+3ylYzkSVK8ODwh
2XJp4J1DDp20Q2M4YK98lbCpxEPncyrgRHIJid3jC0ykTPIGwGJxVXlnD6VvYl0j
0VZ5Kq2DFIPPgmZzecQnLT9Vt5myFr5SqLOSSQIDAQABAoIBAQCpw9BsU1tuaF6D
AVy1T2LzAAk8O1yje6pWKxHkHsalZAq1EG9oIP/HogJve2MuDNhL80N1fBPRz2ot
PJutO417WGKXYjhDS7WNBHfrv2M4LAzxk4wa3r53L4Zgk+gUtR1mpR/cYt07ImXd
nEvcdlAepnv4pP7mCk4sDjB0lFREx5QU5pJFbCuixAVzqXwTfe5fHbLAbbbyclFB
MdWdVJW/t0hTcZdBUtvk1hcpgAJ6Ykl9waSOSKBvAXa9KGqPIY/f328CD7YUbXFg
fucmlN472rsgXn7u0qP3hOox7sNw5JjEULCGg+m+JVqJ/eclDC288fI9lXOXxFTa
38MB1TgFAoGBANyr2EKn97XDVXfGZUOCIAzq1inxkJnJCIOkBlDqwNiSfh3VFK5v
ppy2jGxGYbMdj5tca6L1Yql/DrCmWR+KJOYz3QB56YrG/pe+D2TKnSvPF3jZVQHH
JClHW56v9PqzAbwPbyjTiStZ7oUHQ5eY5vi6ygvnUhybYNDSFAxxoDwLAoGBAO13
z2xMSTPbmmK88UsR9S8NwshJ54a/RQl38IQJ+9TamfX/IuN2mZcs3ixr+CGv/saY
0JMDGp0tCWdoP5ImPsq+OyjJgXXP2tzXaJrQSsCb+N4vywjvMjAmhxcdp3pKcw7F
1NlQdaVV4InEIajbYqtyQhB2GMZyCHyq2qL5jst7AoGAJUmcV1cOklYZYQ3TGp8o
T0Z3PcslxfakS6oxrwab43yNdvkEb51KJ/zoqXsTEzMRiw0I2xZfv4hKsSrKsHul
VIi69VOkVODfMEDbVQqvmDF8I92FcbF2uMrn/l55JMuOpXpuLBXifcLKfQwHLdyW
Wr0lWvGRfGf86gw1ewzQKJUCgYEAolUx7aWksRehTXg+NwRaqMTub77d0CZ2ykc8
mva8OcEKWLkGH5rW2hpo8tMIN/c44ohapPUNP38nG5KPSphsempaxMIjhucFhcyX
jKVxRIQbN8BSOpRRqcrctHeoIpg8WU/x9nDjS5gOO/9gxy7aH7um39vridUwahDe
D2UsMXsCgYEAli9kGIRr/xe7++W4vW3RTCDDvDNIEbH6JZs1X1EVTKxWhGzgCvCO
+lMUQP4gzlJ6DJQd4iZo7Ukj31VSHKH522BIRlKNLT7JhOdDm/Dj7ZP+EF8MO4P+
xJ+W+aPuNbLZmvXdgbKsDSAkIFY5Wweu774/YkPp+ngRhamYoGASHX8=
-----END RSA PRIVATE KEY-----"""

TEST_SERVER_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzLJd44qbp0N5cXKw0JNx
CTQDWtC9X06rYoskRHxf5Tjy0AjWjOU5NvpwGC4YPoK2U3Ln6YDKVF7W6wyTPePM
2ECJE8y8N4B/BXpOx5hWqTmhqtZDfHR+KRIbkpIAjwTDJD7chINgqY53dC5fJ22F
82r4e8g2kwp7C2K6SqgLr5kU/y30nUDgC5M27O4i1pP84t7qqMeuEAHey9zKJb64
0PRgUAXAWAZhL+3ylYzkSVK8ODwh2XJp4J1DDp20Q2M4YK98lbCpxEPncyrgRHIJ
id3jC0ykTPIGwGJxVXlnD6VvYl0j0VZ5Kq2DFIPPgmZzecQnLT9Vt5myFr5SqLOS
SQIDAQAB
-----END PUBLIC KEY-----"""


@pytest.fixture
def app():
    _app = Flask(__name__)
    _app.config.update(
        SERVICE_NAME="test-service",
        TOKEN_EXPIRE_MINUTES=30,
        SERVICE_PRIVATE_KEY=TEST_SERVER_PRIVATE_KEY,
        CLIENT_PUBLIC_KEY=TEST_SERVER_PUBLIC_KEY,
    )
    return _app


@pytest.fixture
def mock_request():
    request = Mock()
    request.form = {}
    return request


def test_create_token(app):
    test_data = {"status": Status.OK, "request_id": "test-123", "action": "APPROVE"}

    token = create_token(app, json.dumps(test_data))
    decoded = jwt.decode(token, TEST_SERVER_PUBLIC_KEY, algorithms=["RS256"])

    assert decoded["iss"] == "test-service"
    assert base64.b64decode(decoded["package_data"]).decode() == json.dumps(test_data)
    assert "exp" in decoded


def test_verify_token(app, mock_request, monkeypatch):
    test_data = {"status": Status.OK, "request_id": "test-123", "action": "APPROVE"}
    token = create_token(app, json.dumps(test_data))

    mock_request.form["TSS_JWT_MSG"] = token
    monkeypatch.setattr("app.service.request", mock_request)

    with app.app_context():
        payload = verify_token(app)
        assert payload["iss"] == "test-service"
        assert base64.b64decode(payload["package_data"]).decode() == json.dumps(
            test_data
        )
        assert hasattr(g, "request_data")
        assert g.request_data == json.dumps(test_data)


def test_verify_token_invalid(app, mock_request, monkeypatch):
    mock_request.form["TSS_JWT_MSG"] = "invalid_token"
    monkeypatch.setattr("app.service.request", mock_request)

    with app.app_context():
        with pytest.raises(jwt.InvalidTokenError):
            verify_token(app)


def test_verify_token_expired(app, mock_request, monkeypatch):
    test_data = {"status": Status.OK, "request_id": "test-123", "action": "APPROVE"}

    app.config["TOKEN_EXPIRE_MINUTES"] = -1

    token = create_token(app, json.dumps(test_data))

    mock_request.form["TSS_JWT_MSG"] = token
    monkeypatch.setattr("app.service.request", mock_request)

    with app.app_context():
        with pytest.raises(jwt.InvalidTokenError) as exc:
            verify_token(app)
        assert "Token has expired" in str(exc.value)


def test_verify_token_missing(app, mock_request, monkeypatch):
    monkeypatch.setattr("app.service.request", mock_request)

    with app.app_context():
        with pytest.raises(jwt.InvalidTokenError) as exc:
            verify_token(app)
        assert "Token not found" in str(exc.value)
