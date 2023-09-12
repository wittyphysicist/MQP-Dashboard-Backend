import pytest
import os
from bqp_dashboard_backend import create_app
from bqp_database_access._database import open_database
import bqp_database_access as database_access
from pony.orm import db_session
from pony.orm import count
from pony.orm import TransactionError
from pony.orm import select
from datetime import datetime
from http import HTTPStatus
from werkzeug.datastructures import Headers


@pytest.fixture(scope="module")
def app():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )

    # other setup can go here
    create_local_database()

    yield app

    # clean up / reset resources here

    delete_local_database()


def create_local_database():
    db = open_database(create_tables=True)
    db.disconnect()

    try:
        with db_session:
            database_access.users.create_new_security_level(
                "BASIC",
                token_max_live_count=1,
                token_max_lifetime=30,
                token_min_creation_interval=1,
                token_max_jobs=100,
                token_max_budget=100,
                token_max_rate=1,
                login_max_interval=365,
            )
            database_access.users.create_new_user_with_secret(
                "test_user", "test_password", "BASIC", "test@lrz.de", "LRZ", "quantum"
            )

            database_access.users.create_new_user_with_secret(
                "test_secret_change_user",
                "test_old_password",
                "BASIC",
                "test@lrz.de",
                "LRZ",
                "quantum",
            )

            database_access.users.create_new_user_with_secret(
                "blocked_test_user",
                "test_password",
                "BASIC",
                "test@lrz.de",
                "LRZ",
                "quantum",
            )

            quantum_db = open_database()

            user = quantum_db.User["blocked_test_user"]
            user.blocked = True
            user.block_reason = f"testing dashboard behaviour: {str(datetime.now())}"

            quantum_db.commit()

    except TransactionError as error:
        pass


def delete_local_database() -> None:
    db = open_database()
    path = db.provider.pool.filename
    db.disconnect()
    os.remove(path)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def inactive_client(app):
    return app.test_client()


def create_header(response) -> Headers:
    header = Headers()

    header.add("Content-Type", "application/json")
    header.add("Authorization", "Bearer " + response.json["access_token"])

    return header


@pytest.fixture(scope="module")
def active_client(app):
    client = app.test_client()

    user_data = {"identity": "test_user", "secret": "test_password"}
    login_response = client.post("/login", json=user_data)

    assert (
        login_response.status_code == HTTPStatus.OK
        and login_response.json["access_token"] is not None
    )

    client.headers = create_header(login_response)

    return client


@pytest.fixture(scope="module")
def active_client_for_secret_change(app):
    client = app.test_client()

    user_data = {"identity": "test_secret_change_user", "secret": "test_old_password"}
    login_response = client.post("/login", json=user_data)

    assert (
        login_response.status_code == HTTPStatus.OK
        and login_response.json["access_token"] is not None
    )

    client.headers = create_header(login_response)

    return client


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
