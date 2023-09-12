from http import HTTPStatus


def test_fetch_all_jobs(active_client) -> None:
    """Test if all jobs are fetched associated with a user."""

    response = active_client.get("/jobs", headers=active_client.headers)

    assert response.status_code == HTTPStatus.OK and not response.json["jobs"]
