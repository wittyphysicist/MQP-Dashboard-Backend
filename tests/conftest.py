import os
import datetime
import pytest
from pathlib import Path
from http import HTTPStatus
import bqp_database_access as database_access
from bqp_database_access._database import open_database
from pony.orm import db_session
from werkzeug.datastructures import Headers
from ldap_test import LdapServer


NOW = datetime.datetime.now()


@pytest.fixture(scope="module")
def app():
    create_local_database()
    from mqp_dashboard_backend import create_app

    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )

    server = create_ldap_server()

    yield app

    # clean up / reset resources here

    delete_local_database()
    server.stop()


def create_ldap_server():
    properties = {
        "port": 8888,
        "bind_dn": "cn=ldap_test_user,ou=QuantumComputing,ou=Kennungen,o=example-org,c=de",
        "password": "ldap_test_password",
        "base": {
            "objectclass": ["country"],
            "dn": "c=de",
            "attributes": {"o": "example-org"},
        },
        "entries": [
            {
                "objectclass": ["organization"],
                "dn": "o=example-org,c=de",
                "attributes": {"o": "example-org"},
            },
            {
                "objectclass": ["organizationalunit"],
                "dn": "ou=Kennungen,o=example-org,c=de",
                "attributes": {"ou": "Kennungen"},
            },
            {
                "objectclass": ["organizationalunit"],
                "dn": "ou=Intranet,ou=Kennungen,o=example-org,c=de",
                "attributes": {"ou": "Intranet"},
            },
            {
                "objectclass": ["organizationalunit"],
                "dn": "ou=QuantumComputing,ou=Kennungen,o=example-org,c=de",
                "attributes": {"ou": "QuantumComputing"},
            },
            {
                "objectclass": ["user"],
                "dn": "cn=ldap_test_user,ou=QuantumComputing,ou=Kennungen,o=example-org,c=de",
                "attributes": {"cn": "ldap_test_user"},
            },
        ],
    }
    server = LdapServer(properties, java_delay=0.5)
    server.start()
    return server


def create_local_database():
    delete_local_database()

    db = open_database(create_tables=True)
    db.disconnect()

    # Helper phase: helpers require db_session.
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
            "test_user",
            "test_password",
            "BASIC",
            "test@test.mail",
            "TEST_HPC_CENTER",
            "QUANTUM",
        )

        database_access.users.create_new_user_with_secret(
            "test_user2",
            "test_password",
            "BASIC",
            "test@test.mail",
            "TEST_HPC_CENTER",
            "QUANTUM",
        )

        database_access.users.create_new_user_with_secret(
            "portal_test_user",
            "test_password",
            "BASIC",
            "portal_test@test.mail",
            "TEST_HPC_CENTER",
            "QUANTUM",
        )

        database_access.users.create_new_user_with_secret(
            "test_eqe_user",
            "test_password",
            "BASIC",
            "test@test.mail",
            "TEST_HPC_CENTER",
            "QUANTUM",
        )

        database_access.users.create_new_user_with_secret(
            "blocked_test_user",
            "test_password",
            "BASIC",
            "test@lrz.de",
            "LRZ",
            "LDAP",
        )

    quantum_db = open_database()

    with db_session:
        basic_level = quantum_db.UserSecurityLevel["BASIC"]

        quantum_db.User(
            identity="ldap_test_user",
            email="ldap_test@test.mail",
            affiliation="TEST_HPC_CENTER",
            association="LDAP",
            security_level=basic_level,
            force_secret_reset=False,
        )

        test_user = quantum_db.User["test_user"]
        test_user2 = quantum_db.User["test_user2"]
        portal_test_user = quantum_db.User["portal_test_user"]
        eqe_user = quantum_db.User["test_eqe_user"]

        temp_budget = quantum_db.Budget(
            name="temp_budget",
            note=" ",
            owner=test_user,
            credits=1000,
        )

        test_group = quantum_db.UserGroup(
            name="TEST_USER_GROUP",
            note="Group granting test_user access to temp_budget",
            owner=test_user,
            cost_modifier=1.0,
        )

        eqe_group = quantum_db.UserGroup(
            name="EQE",
            note="Group granting eqe_user access to temp_budget",
            owner=test_user,
            cost_modifier=1.0,
        )

        mqp_edu_group = quantum_db.UserGroup(
            name="MQP_EDU",
            note="MQP_EDU group for testing purposes",
            owner=portal_test_user,
            cost_modifier=1.0,
        )

        test_user.user_groups.add(test_group)
        test_user2.user_groups.add(test_group)
        temp_budget.user_groups.add(test_group)

        eqe_user.user_groups.add(eqe_group)
        portal_test_user.user_groups.add(mqp_edu_group)

        quantum_db.insert(
            "resource_security_level",
            name="BASIC",
            note=" ",
            job_min_interval=10,
            budget_max_per_job=10,
            unique_token_required=False,
            token_max_lifetime=10,
        )

        quantum_db.insert(
            "resource",
            name="TEST_QPU_1",
            note=" ",
            maintenance=False,
            qubits=5,
            connectivity=" ",
            instructions=" ",
            quantum_technology=" ",
            num_queued_jobs=1,
            resource_cost_modifier=1,
            security_level="BASIC",
        )

        quantum_db.insert(
            "resource",
            name="TEST_QPU_2",
            note=" ",
            maintenance=True,
            qubits=5,
            connectivity=" ",
            instructions=" ",
            quantum_technology=" ",
            num_queued_jobs=1,
            resource_cost_modifier=1,
            security_level="BASIC",
        )

        quantum_db.insert(
            "target_specification",
            name="TS_TEST_QPU_1",
            note=" ",
            specification_type=" ",
            minimum_qubits="1",
            quantum_technology=" ",
            resource_name="TEST_QPU_1",
        )

        quantum_db.insert(
            "target_specification",
            name="TS_TEST_QPU_2",
            note=" ",
            specification_type=" ",
            minimum_qubits="1",
            quantum_technology=" ",
            resource_name="TEST_QPU_2",
        )

        quantum_db.insert(
            "circuit_job",
            id=201,
            note="JOB_PENDING_QUEUED_TEST_QPU_1",
            status="PENDING",
            shots=1,
            circuit="OPENQASM 2.0;",
            circuit_format="qasm",
            no_modify=True,
            timestamp_submitted=NOW,
            timestamp_scheduled=None,
            timestamp_completed=None,
            cost=0,
            result='{"10": 76, "11": 425, "01": 91, "00": 408}',
            owner="test_user2",
            budget="temp_budget",
            executed_resource="TEST_QPU_1",
            target_specification="TS_TEST_QPU_1",
            executed_circuit="OPENQASM 2.0;",
            queued=True,
        )

        quantum_db.insert(
            "circuit_job",
            id=202,
            note="JOB_PENDING_QUEUED_TEST_QPU_2",
            status="PENDING",
            shots=1,
            circuit="OPENQASM 2.0;",
            circuit_format="qasm",
            no_modify=True,
            timestamp_submitted=NOW,
            timestamp_scheduled=None,
            timestamp_completed=None,
            cost=0,
            result='{"10": 76, "11": 425, "01": 91, "00": 408}',
            owner="test_user2",
            budget="temp_budget",
            executed_resource="TEST_QPU_2",
            target_specification="TS_TEST_QPU_2",
            executed_circuit="OPENQASM 2.0;",
            queued=True,
        )

        for job_id, status, queued in [
            (111, "PENDING", False),
            (112, "CANCELLED", True),
            (113, "COMPLETED", True),
        ]:
            quantum_db.insert(
                "circuit_job",
                id=job_id,
                note=" ",
                status=status,
                shots=200,
                circuit="OPENQASM 2.0;",
                circuit_format="qasm",
                no_modify=True,
                timestamp_submitted=NOW,
                timestamp_scheduled=None,
                timestamp_completed="2024-07-17 11:17:32.397618",
                cost=0,
                result='{"10": 76, "11": 425, "01": 91, "00": 408}',
                owner="test_user",
                budget="temp_budget",
                executed_resource="TEST_QPU_1",
                target_specification="TS_TEST_QPU_1",
                executed_circuit="OPENQASM 2.0;",
                queued=queued,
            )

        quantum_db.commit()

    quantum_db.disconnect()


def delete_local_database() -> None:
    sqlite_path = Path(os.getenv("QUANTUM_DB_FILENAME", "test_db.sqlite"))

    if sqlite_path.exists():
        sqlite_path.unlink()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def inactive_client(app):
    return app.test_client()


@pytest.fixture(scope="module")
def active_client(app):
    client = app.test_client()

    user_data = {"identity": "test_user", "secret": "test_password"}
    login_response = client.post("/login", json=user_data)

    assert (
        login_response.status_code == HTTPStatus.OK
        and login_response.json["access_token"] is not None
    )

    client.headers = Headers()
    client.headers.add("Content-Type", "application/json")
    client.headers.add("Authorization", "Bearer " + login_response.json["access_token"])

    return client


@pytest.fixture(scope="module")
def active_client_mqp_edu(app):
    client = app.test_client()

    user_data = {"identity": "portal_test_user", "secret": "test_password"}
    login_response = client.post("/login", json=user_data)

    assert (
        login_response.status_code == HTTPStatus.OK
        and login_response.json["access_token"] is not None
    )

    client.headers = Headers()
    client.headers.add("Content-Type", "application/json")
    client.headers.add("Authorization", "Bearer " + login_response.json["access_token"])

    return client


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
