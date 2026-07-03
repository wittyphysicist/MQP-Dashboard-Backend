"""
Test the behaviour of the /tokens endpoint.
The sequence of tests in this module is important.
"""

from http import HTTPStatus
from datetime import datetime, timedelta

from mqp_dashboard_backend import tokens


def test_token_endpoint_inactive(inactive_client) -> None:
    """Test if the /tokens endpoint checks for a JWT."""

    response = inactive_client.get("/tokens")

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_token_creation(active_client) -> None:
    """Test if token creation is working."""

    expected_expiration = datetime.combine(
        datetime.now() + timedelta(days=7), datetime.max.time()
    ).isoformat()

    token_data = {
        "token_name": "test_remember_name_1",
        "validity": 7,
        "max_nb_jobs": 5,
        "max_budget": 1000,
    }

    response = active_client.post(
        "/tokens/new", json=token_data, headers=active_client.headers
    )
    assert (
        response.status_code == HTTPStatus.OK
        and response.json["token_data"]["token_value"] is not None
        and response.json["token_data"]["token_name"] == "test_remember_name_1"
        and response.json["token_data"]["token_expiration"] == expected_expiration
    )


def test_mqp_edu_token_creation(active_client_mqp_edu) -> None:
    """Test if token creation for MQP_EDU user is working."""

    expected_expiration = datetime.combine(
        datetime.now() + timedelta(days=7), datetime.max.time()
    ).isoformat()

    token_data = {
        "token_name": "test_remember_name_2",
        "validity": 7,
        "max_nb_jobs": 5,
        "max_budget": 1000,
    }

    response = active_client_mqp_edu.post(
        "/tokens/new", json=token_data, headers=active_client_mqp_edu.headers
    )

    assert (
        response.status_code == HTTPStatus.OK
        and response.json["token_data"]["token_value"]
        == "ThisIsAnEducationalTokenItCannotBeUsedToSubmitJobsThisIsAnEducat"
        and response.json["token_data"]["token_name"] == "test_remember_name_2"
        and response.json["token_data"]["token_expiration"] == expected_expiration
    )


def test_token_creation_with_existing_name(active_client, monkeypatch) -> None:
    """Test if token creation correctly fails when the token name already exists."""

    def raise_token_exists(*args, **kwargs):
        raise tokens.TokenExistsError("test_remember_name_1")

    monkeypatch.setattr(tokens.database.tokens, "add_new_token", raise_token_exists)

    token_data = {
        "token_name": "test_remember_name_1",
        "validity": 7,
        "max_nb_jobs": 5,
        "max_budget": 1000,
    }

    response = active_client.post(
        "/tokens/new", json=token_data, headers=active_client.headers
    )

    assert (
        response.status_code == HTTPStatus.FORBIDDEN
        and response.json["error_message"]
        == "Token test_remember_name_1 already exists."
    )


def test_token_creation_with_too_many_alive(active_client) -> None:
    """Test if token creation correctly fails if too many are live."""

    token_data = {
        "token_name": "test_remember_name_2",
        "validity": 7,
        "max_nb_jobs": 5,
        "max_budget": 1000,
    }

    response = active_client.post(
        "/tokens/new", json=token_data, headers=active_client.headers
    )
    assert (
        response.status_code == HTTPStatus.FORBIDDEN
        and response.json["error_message"] == "Too many tokens alive."
    )


def test_token_creation_after_valid_range(active_client) -> None:
    token_data = {
        "token_name": "test_remember_name_1",
        "validity": 365,
        "max_nb_jobs": 5,
        "max_budget": 1000,
    }

    response = active_client.post(
        "/tokens/new", json=token_data, headers=active_client.headers
    )

    assert (
        response.status_code == HTTPStatus.FORBIDDEN
        and response.json["error_message"] == "Token expiration beyond user limit."
    )


def test_token_creation_with_expiration_before_now(active_client) -> None:
    token_data = {
        "token_name": "test_remember_name_1",
        "validity": -1,
        "max_nb_jobs": 5,
        "max_budget": 1000,
    }

    response = active_client.post(
        "/tokens/new", json=token_data, headers=active_client.headers
    )

    assert (
        response.status_code == HTTPStatus.FORBIDDEN
        and response.json["error_message"] == "Token expiration before now."
    )


def test_fetch_all_tokens(active_client) -> None:
    """Tests to check if fetching all tokens is possible."""

    response = active_client.get("/tokens", headers=active_client.headers)

    expected_expiration = datetime.combine(
        datetime.now() + timedelta(days=7), datetime.max.time()
    ).isoformat()

    assert (
        response.status_code == HTTPStatus.OK
        and response.json["tokens"][0]["token_name"] == "test_remember_name_1"
        and response.json["tokens"][0]["token_expiration"] == expected_expiration
    )


def test_revoking_existing_token(active_client) -> None:
    """Test whether revoking a token is possible."""

    token_data = {"token_owner": "test_user", "token_name": "test_remember_name_1"}

    response = active_client.delete(
        "/tokens", json=token_data, headers=active_client.headers
    )

    assert response.status_code == HTTPStatus.OK


def test_revoking_non_existing_token(active_client) -> None:
    """Test whether revoking a token is possible."""

    token_data = {"token_name": "test_non_existing_name"}

    response = active_client.delete(
        "/tokens", json=token_data, headers=active_client.headers
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_fetching_limits(active_client) -> None:
    """Test if we can fetch a users user_security_level limits for token creation."""

    response = active_client.get("/tokens/user_limits", headers=active_client.headers)

    assert (
        response.status_code == HTTPStatus.OK
        and response.json["max_lifetime"] == 30
        and response.json["max_jobs"] == 100
        and response.json["max_budget"] == 100
    )
