import pytest
from httpx import ASGITransport, AsyncClient

from prevenred.main import app


@pytest.mark.asyncio
async def test_upload_valid_image() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("test_photo.jpg", b"\xff\xd8\xff\xe0testimagecontent", "image/jpeg")}
        response = await ac.post("/api/v1/media/upload", files=files)
        assert response.status_code == 201
        data = response.json()
        assert "url" in data
        assert data["filename"].endswith(".jpg")
        assert data["content_type"] == "image/jpeg"
        assert data["size_bytes"] > 0


@pytest.mark.asyncio
async def test_upload_invalid_content_type() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("malicious.exe", b"binarycontent", "application/x-msdownload")}
        response = await ac.post("/api/v1/media/upload", files=files)
        assert response.status_code == 400
        assert "Formato no permitido" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_oversized_file() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        oversized_data = b"0" * (25 * 1024 * 1024 + 1)
        files = {"file": ("huge.mp4", oversized_data, "video/mp4")}
        response = await ac.post("/api/v1/media/upload", files=files)
        assert response.status_code == 413
        assert "tamaño máximo" in response.json()["detail"]
