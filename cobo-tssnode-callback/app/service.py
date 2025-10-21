import base64
import json
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request

from app.types import PackageDataClaim, Status
from app.utils import load_keys
from app.verify import TssVerifier

import cobo_waas2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_app(server, config):
    """Initialize the Flask application"""
    server.config.update(
        SERVICE_NAME=config.service_name,
        ENDPOINT=config.endpoint,
        TOKEN_EXPIRE_MINUTES=config.token_expire_minutes,
        ENABLE_DEBUG=config.enable_debug,
    )

    # Load keys
    try:
        client_public_key, service_private_key = load_keys(
            config.client_public_key_path, config.service_private_key_path
        )
        server.config["CLIENT_PUBLIC_KEY"] = client_public_key
        server.config["SERVICE_PRIVATE_KEY"] = service_private_key

        logger.info(f"Init server: {server.config['SERVICE_NAME']}")
    except Exception as e:
        logger.error(f"Failed to initialize service: {str(e)}")
        raise

    # Register routes
    @server.route("/ping", methods=["GET"])
    def ping():
        """Health check endpoint"""
        response = {
            "server": server.config["SERVICE_NAME"],
            "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
        }
        return jsonify(response)

    @server.route("/v2/check", methods=["POST"])
    @jwt_required
    def risk_control():
        """Risk control endpoint with JWT verification"""
        try:
            # Get raw request from JWT payload
            raw_request = get_raw_request()
            if not raw_request:
                response = cobo_waas2.TSSCallbackResponse(
                    status=Status.INVALID_REQUEST, error="Invalid request data"
                )
                return create_response(server, response, 200)

            # Process the request
            response = process_request(raw_request)
            if not response:
                response = cobo_waas2.TSSCallbackResponse(
                    status=Status.INTERNAL_ERROR, error="Failed to process request"
                )
                return create_response(server, response, 400)

            return create_response(server, response, 200)

        except Exception as e:
            logger.error(f"Risk control error: {str(e)}")
            response = cobo_waas2.TSSCallbackResponse(status=Status.INVALID_REQUEST, error=str(e))
            return create_response(server, response, 200)


def get_raw_request():
    """Get raw request data from JWT payload"""
    try:
        if not hasattr(g, "request_data"):
            return None

        request_data = g.request_data
        if isinstance(request_data, str):
            request_data = json.loads(request_data)

        req = cobo_waas2.TSSCallbackRequest(
            request_id=request_data.get("request_id"),
            request_type=request_data.get("request_type"),
            request_detail=request_data.get("request_detail"),
            extra_info=request_data.get("extra_info"),
        )
        return req
    except Exception as e:
        logger.error(f"Failed to parse request data: {str(e)}")
        return None


def process_request(req: cobo_waas2.TSSCallbackRequest) -> cobo_waas2.TSSCallbackResponse:
    """Process request with TSS verifier"""
    verifier = TssVerifier.new()

    err = verifier.verify(req)
    if err:
        return cobo_waas2.TSSCallbackResponse(
            status=Status.INTERNAL_ERROR,
            request_id=req.request_id,
            action=cobo_waas2.TSSCallbackActionType.REJECT,
            error=err,
        )

    return cobo_waas2.TSSCallbackResponse(status=Status.OK, request_id=req.request_id, action=cobo_waas2.TSSCallbackActionType.APPROVE)


def create_token(server, data):
    """Create a JWT token with the given data"""
    try:
        with server.app_context():
            expiration_time = datetime.now(timezone.utc) + timedelta(
                minutes=server.config["TOKEN_EXPIRE_MINUTES"]
            )
            claim = PackageDataClaim(
                package_data=base64.b64encode(data.encode()).decode(),
                exp=int(expiration_time.timestamp()),
                iss=server.config["SERVICE_NAME"],
            )

            token = jwt.encode(
                claim.to_dict(), server.config["SERVICE_PRIVATE_KEY"], algorithm="RS256"
            )
            return token
    except Exception as e:
        logger.error(f"Failed to create token: {str(e)}")
        raise


def verify_token(server):
    """Verify JWT token from request"""
    token = request.form.get("TSS_JWT_MSG", "").strip()
    if not token:
        raise jwt.InvalidTokenError("Token not found")

    try:
        payload = jwt.decode(
            token, server.config["CLIENT_PUBLIC_KEY"], algorithms=["RS256"]
        )
        package_data = base64.b64decode(payload.get("package_data", "")).decode()
        g.request_data = package_data
        return payload
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")
    except Exception as e:
        raise jwt.InvalidTokenError(f"Token verification failed: {str(e)}")


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_token(current_app)
        except jwt.InvalidTokenError as e:
            response = cobo_waas2.TSSCallbackResponse(status=Status.INVALID_TOKEN, error=str(e))
            return create_response(current_app, response)
        return f(*args, **kwargs)

    return decorated


def create_response(server, response: cobo_waas2.TSSCallbackResponse, http_status=200):
    """Create HTTP response with JWT token"""
    try:
        response_data = json.dumps(response.to_dict())
        token = create_token(server, response_data)
        return token, http_status
    except Exception as e:
        logger.error(f"Failed to create response: {str(e)}")
        return jsonify({"error": str(e)}), 500
