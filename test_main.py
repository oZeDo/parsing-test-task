import httpx
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_search_movies(client):
    response = client.get("/search?query=Мстители&page=1")
    assert response.status_code == 200
    data = response.json()
    assert "total_found" in data
    assert "films" in data


def test_search_movies_no_results(client):
    response = client.get("/search?query=NonExistentMovie&page=1")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "No movies found."


def test_search_movies_http_error(client, mocker):
    # Mocking the httpx.AsyncClient.post method to simulate an HTTP error
    mocker.patch("main.httpx.AsyncClient.post", side_effect=httpx.HTTPError("Mocked HTTP error"))

    response = client.get("/search?query=Avengers&page=1")
    assert response.status_code == 500
    data = response.json()
    assert data["detail"] == "Error communicating with the website."
