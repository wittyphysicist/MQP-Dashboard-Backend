from http import HTTPStatus

import os


def test_correct_login(inactive_client) -> None:
    """Test whether a normal login works."""

    user_data = {"identity": "test_user", "secret": "test_password"}

    response = inactive_client.post("/login", json=user_data)

    assert (
        response.status_code == HTTPStatus.OK
        and response.json["access_token"] is not None
        and response.json["force_secret_reset"] is not None
    )


def test_login_with_non_existing_user(inactive_client) -> None:
    """Test whether login with a non-existing user correctly fails."""

    user_data = {"identity": "non_existing_user", "secret": "test_password"}

    response = inactive_client.post("/login", json=user_data)

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_login_with_wrong_password(inactive_client) -> None:
    """Test whether login with a wrong password correctly fails."""

    user_data = {"identity": "test_user", "secret": "wrong_password"}

    response = inactive_client.post("/login", json=user_data)

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_login_with_blocked_user(inactive_client) -> None:
    """Test whether login with a blocked user correctly fails."""

    user_data = {"identity": "blocked_test_user", "secret": "test_password"}

    response = inactive_client.post("/login", json=user_data)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
