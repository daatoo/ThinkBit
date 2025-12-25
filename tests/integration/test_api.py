import io
import pytest
from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_stats():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_media" in data
    assert "total_segments" in data
    assert "by_status" in data
    assert "by_type" in data


def test_media_list():
    response = client.get("/media")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_media_list_pagination():
    response = client.get("/media?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 0
    assert data["limit"] == 10


def test_media_not_found():
    response = client.get("/media/99999")
    assert response.status_code == 404


def test_download_not_found():
    response = client.get("/download/99999")
    assert response.status_code == 404


def test_delete_not_found():
    response = client.delete("/media/99999")
    assert response.status_code == 404


def test_process_no_file():
    response = client.post("/process")
    assert response.status_code == 422


def test_process_invalid_extension():
    file_content = b"fake content"
    response = client.post(
        "/process",
        files={"file": ("test.exe", io.BytesIO(file_content), "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]


def test_process_invalid_mimetype():
    file_content = b"fake content"
    response = client.post(
        "/process",
        files={"file": ("test.mp4", io.BytesIO(file_content), "text/plain")},
    )
    assert response.status_code == 400
    assert "Invalid content type" in response.json()["detail"]

