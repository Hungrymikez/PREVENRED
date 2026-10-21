import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from .schemas import MediaUploadResponse

router = APIRouter(prefix="/media", tags=["Media Storage"])

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB max limit


@router.post("/upload", response_model=MediaUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)) -> MediaUploadResponse:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Formato no permitido ({file.content_type}). "
                "Formatos admitidos: JPEG, PNG, WEBP, MP4."
            ),
        )

    content = await file.read()
    size = len(content)
    if size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="El archivo excede el tamaño máximo permitido de 25 MB.",
        )

    ext = ALLOWED_TYPES[file.content_type]
    filename = f"{uuid.uuid4().hex}{ext}"

    # Guardar localmente simulando almacenamiento seguro
    upload_dir = Path("uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / filename
    with open(file_path, "wb") as f:
        f.write(content)

    public_url = f"/static/uploads/{filename}"
    return MediaUploadResponse(
        url=public_url,
        filename=filename,
        content_type=file.content_type,
        size_bytes=size,
    )
