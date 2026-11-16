import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from prevenred.auth.application.ports import TokenPayload
from prevenred.auth.interface.dependencies import get_current_token

from .schemas import MediaUploadResponse

router = APIRouter(prefix="/media", tags=["Media Storage"])

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB max limit
CHUNK_SIZE_BYTES = 1024 * 1024

# Carpeta local donde se guardan los archivos y ruta pública desde la que se sirven
# (main.py la monta con StaticFiles). En producción se reemplaza por un almacenamiento externo.
UPLOAD_DIR = Path("uploads")
PUBLIC_URL_PREFIX = "/static/uploads"

_TOO_LARGE = HTTPException(
    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
    detail="El archivo excede el tamaño máximo permitido de 25 MB.",
)


@router.post("/upload", response_model=MediaUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    _uploader: TokenPayload = Depends(get_current_token),
) -> MediaUploadResponse:
    """Sube una foto o video (exige sesión). Se copia por bloques para no cargar
    el archivo entero en memoria y se corta en cuanto supera el límite."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Formato no permitido ({file.content_type}). "
                "Formatos admitidos: JPEG, PNG, WEBP, MP4."
            ),
        )
    if file.size is not None and file.size > MAX_FILE_SIZE_BYTES:
        raise _TOO_LARGE

    ext = ALLOWED_TYPES[file.content_type]
    filename = f"{uuid.uuid4().hex}{ext}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / filename
    partial_path = file_path.with_name(f"{filename}.part")

    size = 0
    try:
        with open(partial_path, "wb") as f:
            while chunk := await file.read(CHUNK_SIZE_BYTES):
                size += len(chunk)
                if size > MAX_FILE_SIZE_BYTES:
                    raise _TOO_LARGE
                f.write(chunk)
        partial_path.replace(file_path)
    finally:
        partial_path.unlink(missing_ok=True)

    return MediaUploadResponse(
        url=f"{PUBLIC_URL_PREFIX}/{filename}",
        filename=filename,
        content_type=file.content_type,
        size_bytes=size,
    )
