from http import HTTPStatus
from types import SimpleNamespace

import ldap
import pytest

import mqp_dashboard_backend.login as login_module


def test_ldap_access(app) -> None:
    """Test whether the LDAP server is reachable."""

    user_dn = "cn=ldap_test_user,ou=QuantumComputing,ou=Kennungen,o=lrz-muenchen,c=de"
    secret = "ldap_test_password"

    connection = ldap.initialize("ldap://localhost:8888")
    connection.protocol_version = ldap.VERSION3
    connection.set_option(ldap.OPT_REFERRALS, 0)

    auth_user = connection.simple_bind_s(user_dn, secret)

    assert auth_user

    connection.unbind_s()


def test_login_with_blocked_user(inactive_client) -> None:
    """Test whether login with a blocked user correctly fails."""

    user_data = {"identity": "blocked_test_user", "secret": "test_password"}

    response = inactive_client.post("/login", json=user_data)

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_ldap_login_user(inactive_client):
    """Test whether a LDAP marked user can log in."""

    user_data = {"identity": "ldap_test_user", "secret": "ldap_test_password"}

    response = inactive_client.post("/login", json=user_data)
    assert (
        response.status_code == HTTPStatus.OK
        and response.json["access_token"] is not None
        and response.json["force_secret_reset"] is not None
    )


class _FakeLdapConnection:
    def __init__(self, bind_result=True, search_result=None, bind_error=None):
        self.bind_result = bind_result
        self.search_result = ["user"] if search_result is None else search_result
        self.bind_error = bind_error
        self.unbound = False
        self.protocol_version = None

    def set_option(self, _option, _value):
        return None

    def simple_bind_s(self, _user_dn, _secret):
        if self.bind_error is not None:
            raise self.bind_error
        return self.bind_result

    def search_s(self, _user_dn, _scope, _search_filter):
        return self.search_result

    def unbind_s(self):
        self.unbound = True


def test_authenticate_user_by_ldap_rejects_empty_bind(monkeypatch):
    """Test whether LDAP authentication rejects an empty bind response."""

    connection = _FakeLdapConnection(bind_result=None)
    monkeypatch.setenv("LDAP_USER_DN", "ou=QuantumComputing,o=example-org,c=de")
    monkeypatch.setenv("QUANTUM_DS_HOST", "ldap://example.test")
    monkeypatch.setattr(login_module.ldap, "initialize", lambda _host: connection)

    with pytest.raises(login_module.UnknownIdentityError):
        login_module.authenticate_user_by_ldap("ldap_test_user", "secret")

    assert connection.unbound


def test_authenticate_user_by_ldap_rejects_user_without_search_match(monkeypatch):
    """Test whether LDAP authentication rejects users missing from LDAP search."""

    connection = _FakeLdapConnection(search_result=[])
    monkeypatch.setenv("LDAP_USER_DN", "ou=QuantumComputing,o=example-org,c=de")
    monkeypatch.setenv("QUANTUM_DS_HOST", "ldap://example.test")
    monkeypatch.setattr(login_module.ldap, "initialize", lambda _host: connection)

    with pytest.raises(login_module.UnauthorizedUser):
        login_module.authenticate_user_by_ldap("ldap_test_user", "secret")

    assert connection.unbound


def test_authenticate_user_by_ldap_maps_invalid_credentials(monkeypatch):
    """Test whether LDAP invalid credentials become incorrect-secret errors."""

    connection = _FakeLdapConnection(bind_error=ldap.INVALID_CREDENTIALS())
    monkeypatch.setenv("LDAP_USER_DN", "ou=QuantumComputing,o=example-org,c=de")
    monkeypatch.setenv("QUANTUM_DS_HOST", "ldap://example.test")
    monkeypatch.setattr(login_module.ldap, "initialize", lambda _host: connection)

    with pytest.raises(login_module.IncorrectSecretError):
        login_module.authenticate_user_by_ldap("ldap_test_user", "secret")

    assert connection.unbound


def test_login_with_blocked_user_from_database(inactive_client, monkeypatch) -> None:
    """Test whether a database-blocked user is rejected before authentication."""

    user = SimpleNamespace(blocked=True, association="QUANTUM", force_secret_reset=False)
    monkeypatch.setattr(
        login_module.database.users, "fetch_user_by_identity", lambda _identity: user
    )

    response = inactive_client.post(
        "/login", json={"identity": "blocked_user", "secret": "secret"}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_login_with_unknown_authentication_mechanism(inactive_client, monkeypatch) -> None:
    """Test whether users with unknown associations are rejected."""

    user = SimpleNamespace(blocked=False, association="UNKNOWN", force_secret_reset=False)
    monkeypatch.setattr(
        login_module.database.users, "fetch_user_by_identity", lambda _identity: user
    )

    with pytest.raises(login_module.AuthenticationMechanismUnknownError):
        inactive_client.post(
            "/login", json={"identity": "unknown_user", "secret": "secret"}
        )
