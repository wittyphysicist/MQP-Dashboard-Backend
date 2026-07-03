# ------------------------------------------------------------------------------
# Copyright 2026 Munich Quantum Software Stack Project
#
# Licensed under the Apache License, Version 2.0 with LLVM Exceptions (the
# "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://github.com/Munich-Quantum-Software-Stack/QDMI/blob/develop/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# ------------------------------------------------------------------------------

"""MQP Dashboard Tokens Module"""

import secrets
import string
import json
from importlib.resources import files
from datetime import datetime, timedelta
from http import HTTPStatus
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from eliot import log_call
import bqp_database_access as database

# from bqp_database_access._database import open_database
from bqp_database_access.tokens import (
    TokenExistsError,
    TokenExpirationAfterMaximum,
    TokenExpirationBeforeNow,
    TokenNotFound,
    TooManyTokensError,
)


BLUEPRINT = Blueprint("tokens", __name__)

STATIC_TOKEN_FILE = files("mqp_dashboard_backend").joinpath(
    "static_config/static_token.json"
)
with STATIC_TOKEN_FILE.open("r", encoding="utf-8") as f:
    STATIC_TOKEN_CONFIG = json.load(f)


def _get_static_token_groups() -> list[str]:
    return list(STATIC_TOKEN_CONFIG.key())


def _get_token_from_usergroup(usergroup: str) -> str:
    return STATIC_TOKEN_CONFIG.get(usergroup)


def generate_token() -> str:
    """Generate Access Token"""
    return "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(64)
    )


@BLUEPRINT.post("/tokens/new")
@jwt_required()
@log_call
def create_token() -> tuple[dict, HTTPStatus]:
    """
    Create a token with given token data.

    Query parameters:
        - token_name (string): name of token
        - validity (integer): validity time of token (day)
        - max_nb_jobs (integer): maximum number of jobs for this token
        - max_budget (integer): maximum budget for this token

    Returns:
        token_value: hash value of token
        token_name: remember name of token
        token_expiration: the expiration of token
    """

    request_data = request.get_json()
    user_token = get_jwt_identity()
    remember_name = request_data["token_name"]

    expiration = datetime.combine(
        datetime.now().date() + timedelta(days=int(request_data["validity"])),
        datetime.max.time(),
    )
    # quantum_db = open_database()
    # user = quantum_db.User.get(identity=user_token)  # pylint: disable=no-member
    user = database.users.fetch_user_by_identity(identity=user_token)
    _user_group_names = [user_group.name.upper() for user_group in user.user_groups]
    _static_token_usergroups = _get_static_token_groups()
    try:
        for group in _static_token_usergroups:
            if group in _user_group_names:
                token = _get_token_from_usergroup(group)
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
        token = generate_token()
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

    except TooManyTokensError:
        return {
            "error_message": "Too many tokens alive.",
        }, HTTPStatus.FORBIDDEN

    except TokenExpirationBeforeNow:
        return {
            "error_message": "Token expiration before now.",
        }, HTTPStatus.FORBIDDEN

    except TokenExpirationAfterMaximum:
        return {
            "error_message": "Token expiration beyond user limit.",
        }, HTTPStatus.FORBIDDEN
    except TokenExistsError:
        return {
            "error_message": f"Token {request_data['token_name']} already exists.",
        }, HTTPStatus.FORBIDDEN


@BLUEPRINT.get("/tokens")
@jwt_required()
@log_call
def get_all_tokens() -> tuple[dict, HTTPStatus]:
    """
    Get all tokens that belong to user.
    Returns:
        Token list
    """

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

    sorted_tokens = sorted(
        sanitized_tokens, key=lambda x: x["token_name"], reverse=True
    )

    return {
        "tokens": sorted_tokens,
    }, HTTPStatus.OK


@BLUEPRINT.get("/tokens/user_limits")
@jwt_required()
@log_call
def get_user_token_creation_limits() -> list[dict]:
    """Fetch the user security level limits."""

    identity = get_jwt_identity()

    user = database.users.fetch_user_by_identity(identity)

    security_level = user.security_level

    return {
        "max_lifetime": security_level.token_max_lifetime,
        "max_jobs": security_level.token_max_jobs,
        "max_budget": security_level.token_max_budget,
    }


@BLUEPRINT.delete("/tokens")
@jwt_required()
@log_call
def revoke_token() -> tuple[dict, HTTPStatus]:
    """
    Revoke given token and owner combination.
    Returns:
        HTTPStatus
    """

    request_data = request.get_json()
    identity = get_jwt_identity()

    try:
        database.tokens.revoke_token_by_name_and_identity(
            request_data["token_name"], identity
        )

        return {"message": f"Revoked {request_data['token_name']}."}, HTTPStatus.OK

    except TokenNotFound:
        return {"error_message": "Token not found."}, HTTPStatus.BAD_REQUEST
