import pytest
from httpx import ASGITransport, AsyncClient

from prevenred.auth.application.ports import TokenPayload
from prevenred.auth.domain.role import Role
from prevenred.auth.interface.dependencies import get_current_token
from prevenred.main import create_app
from prevenred.media.interface import router as media_router
from prevenred.shared.domain.ids import new_id


@pytest.fixture
def upload_dir(tmp_path, monkeypatch):
    """Guarda los archivos de cada prueba en una carpeta temporal."""
    monkeypatch.setattr(media_router, "UPLOAD_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def app(upload_dir):
    application = create_app()
    application.dependency_overrides[get_current_token] = lambda: TokenPayload(
        user_id=new_id(), role=Role.CIUDADANO
    )
    return application


def _client(app) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_upload_requires_auth(app, upload_dir) -> None:
    app.dependency_overrides.clear()
    async with _client(app) as ac:
        files = {"file": ("test_photo.jpg", b"\xff\xd8\xff\xe0testimagecontent", "image/jpeg")}
        response = await ac.post("/api/v1/media/upload", files=files)
    assert response.status_code == 401
    assert list(upload_dir.iterdir()) == []


@pytest.mark.asyncio
async def test_upload_valid_image(app, upload_dir) -> None:
    content = b"\xff\xd8\xff\xe0testimagecontent"
    async with _client(app) as ac:
        files = {"file": ("test_photo.jpg", content, "image/jpeg")}
        response = await ac.post("/api/v1/media/upload", files=files)
        assert response.status_code == 201
        data = response.json()
        assert data["filename"].endswith(".jpg")
        assert data["content_type"] == "image/jpeg"
        assert data["size_bytes"] == len(content)
        assert (upload_dir / data["filename"]).read_bytes() == content
        assert data["url"] == f"/static/uploads/{data['filename']}"


@pytest.mark.asyncio
async def test_uploaded_file_is_served_at_its_url(upload_dir) -> None:
    """Regresión: la URL devuelta daba 404 porque nadie servía /static/uploads."""
    (upload_dir / "foto.jpg").write_bytes(b"\xff\xd8\xff\xe0abc")
    app = create_app()  # monta StaticFiles sobre la carpeta temporal
    async with _client(app) as ac:
        response = await ac.get("/static/uploads/foto.jpg")
    assert response.status_code == 200
    assert response.content == b"\xff\xd8\xff\xe0abc"


@pytest.mark.asyncio
async def test_upload_invalid_content_type(app) -> None:
    async with _client(app) as ac:
        files = {"file": ("malicious.exe", b"binarycontent", "application/x-msdownload")}
        response = await ac.post("/api/v1/media/upload", files=files)
        assert response.status_code == 400
        assert "Formato no permitido" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_oversized_file(app, upload_dir) -> None:
    async with _client(app) as ac:
        oversized_data = b"0" * (25 * 1024 * 1024 + 1)
        files = {"file": ("huge.mp4", oversized_data, "video/mp4")}
        response = await ac.post("/api/v1/media/upload", files=files)
        assert response.status_code == 413
        assert "tamaño máximo" in response.json()["detail"]
    assert list(upload_dir.iterdir()) == []  # no deja archivos a medias


@pytest.mark.asyncio
async def test_oversized_file_without_declared_size_is_cut_while_copying(
    upload_dir, monkeypatch
) -> None:
    """Si el tamaño no viene declarado, el corte ocurre al copiar por bloques."""
    monkeypatch.setattr(media_router, "MAX_FILE_SIZE_BYTES", 10)

    class FakeUpload:
        content_type = "image/png"
        size = None

        def __init__(self) -> None:
            self._chunks = [b"\x89PNG", b"0123456789"]

        async def read(self, _n: int) -> bytes:
            return self._chunks.pop(0) if self._chunks else b""

    with pytest.raises(Exception) as exc:
        await media_router.upload_file(FakeUpload(), TokenPayload(new_id(), Role.CIUDADANO))
    assert getattr(exc.value, "status_code", None) == 413
    assert list(upload_dir.iterdir()) == []
