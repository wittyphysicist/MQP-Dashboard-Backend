from http import HTTPStatus


def test_secret_change(active_client) -> None:
    """Tests whether a user can change their secret."""

    user_data = {
        "user_token": "test_secret_change_user",
        "current_secret": "test_old_password",
        "new_secret": "test_new_password",
        "new_secret_confirm": "test_new_password",
    }

    response = active_client.post("/reset", json=user_data)

    assert response.json["status"] == HTTPStatus.OK
