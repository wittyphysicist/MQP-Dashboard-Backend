import json
import logging
import string
import os
import secrets
from http import HTTPStatus
from hashlib import md5
from datetime import datetime, timedelta
from .ldap_auth import ldap_authentication


from flask import current_app, Blueprint, request, json
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity


import bqp_database_access as database
from bqp_database_access.users import UnknownIdentityError
from bqp_database_access.tokens import (
    TooManyTokensError,
    TokenExistsError,
    TokenExpirationBeforeNow,
    TokenNotFound,
    TokenExpirationAfterMaximum,
)


def generate_token() -> str:
    return "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(64)
    )


backend = Blueprint("backend", __name__)


@backend.post("/login")
def login_user():
    request_data = request.get_json()

    identity = request_data["identity"]
    secret = request_data["secret"]

    try:
        # validate identity
        user = database.users.fetch_user_by_identity(identity)
        # logging.warning(user.affiliation)
        if user is None:
            raise RuntimeError("Identity does not exist!")

        if user.affiliation == 'LRZ':
            # Authenticate against LDAP
            auth_user = ldap_authentication(identity, secret)
            # logging.warning(auth_user)
            if auth_user is None:
                raise RuntimeError("Failed to authenticate!")

        elif not database.users.authenticate(identity, secret):
            raise RuntimeError("Failed to authenticate!")

        if user.blocked:
            # TODO handle through actual exception
            raise RuntimeError("user is blocked")

    except Exception as error:
        # TODO log error

        return {
            "error_message": "The identity/password is not valid. Please try again!",
        }, HTTPStatus.UNAUTHORIZED

    else:

        # generate JWT
        access_token = create_access_token(
            identity=identity, expires_delta=timedelta(minutes=15)
        )

        return {
            "access_token": access_token,
            "force_secret_reset": user.force_secret_reset,
        }, HTTPStatus.OK

@backend.post("/tokens")
@jwt_required()
def create_token():
    """Create a token with given token data."""

    request_data = request.get_json()

    user_token = get_jwt_identity()
    remember_name = request_data["token_name"]


    expiration = datetime.combine(
        datetime.now().date() + timedelta(days=int(request_data["validity"])),
        datetime.max.time(),
    )

    token = generate_token()

    try:
        database.tokens.add_new_token(
            remember_name,
            user_token,
            token,
            expiration,
            request_data["max_nb_jobs"],
            request_data["max_budget"],
        )

        return {
            "token_data": {
                "token_value": token,
                "token_name": remember_name,
                "token_expiration": expiration.isoformat(),
            }
        }, HTTPStatus.OK

    except TooManyTokensError as error:
        return {
            "error_message": "Too many tokens alive.",
        }, HTTPStatus.FORBIDDEN

    except TokenExpirationBeforeNow as error:
        return {
            "error_message": "Token expiration before now.",
        }, HTTPStatus.FORBIDDEN

    except TokenExpirationAfterMaximum as error:
        return {
            "error_message": "Token expiration beyond user limit.",
        }, HTTPStatus.FORBIDDEN
    except TokenExistsError as error:
        return {
            "error_message": f"Token {request_data['token_name']} already exists.",
        }


@backend.get("/tokens")
@jwt_required()
def get_all_tokens():
    """Get all tokens that belong to user."""

    identity = get_jwt_identity()
    tokens = database.tokens.fetch_active_tokens_of_identity(identity)

    sanitized_tokens = [
        {
            "token_name": token.remember_name,
            "revoked": token.revoked,
            "revoke_reason": token.revoke_reason,
            "token_expiration": token.expiration.isoformat(),
        }
        for token in tokens
    ]


    # print("tokens: ", sanitized_tokens)


    return {
        "tokens": sanitized_tokens,
    }, HTTPStatus.OK


@backend.get("/tokens/user_limits")
@jwt_required()
def get_user_token_creation_limits():
    """Fetch the user security level limits."""

    identity = get_jwt_identity()

    user = database.users.fetch_user_by_identity(identity)

    security_level = user.security_level

    return {
        "max_lifetime": security_level.token_max_lifetime,
        "max_jobs": security_level.token_max_jobs,
        "max_budget": security_level.token_max_budget,
    }


@backend.delete("/tokens")
@jwt_required()
def revoke_token():
    """Revoke given token and owner combination."""

    request_data = request.get_json()
    identity = get_jwt_identity()

    try:
        database.tokens.revoke_token_by_name_and_identity(
            request_data["token_name"], identity
        )

        return {"message": f"Revoked {request_data['token_name']}."}, HTTPStatus.OK

    except TokenNotFound as error:
        return {"error_message": "Token not found."}, HTTPStatus.BAD_REQUEST


@backend.get("/jobs")
@jwt_required()
def fetch_all_jobs():
    """Fetch all jobs belonging to a user."""

    identity = get_jwt_identity()
    jobs = database.jobs.fetch_by_identity(identity)

    sanitized_jobs = [job.to_dict() for job in jobs]

    return {"jobs": sanitized_jobs}, HTTPStatus.OK


@backend.get("/jobs/<id>")
@jwt_required()
def fetch_job(id = 0):
    """Fetch all jobs belonging to a user."""

    identity = get_jwt_identity()
    jobs = database.jobs.fetch_by_identity(identity)

    sanitized_jobs = [job.to_dict() for job in jobs]

    job = None
    for jobItem in sanitized_jobs:
        if jobItem.get("id") == int(id):
            job = jobItem
    print("Found job: \n", job)

    return {"job": job}, HTTPStatus.OK


@backend.get("/resources")
@jwt_required()
def fetch_all_resources():
    """Fetch all jobs belonging to a user."""

    identity = get_jwt_identity()
    resources = database.resources.fetch_resources_available_to_identity(identity)

    sanitized_resources = [resource.to_dict() for resource in resources]

    return {"resources": sanitized_resources}, HTTPStatus.OK






