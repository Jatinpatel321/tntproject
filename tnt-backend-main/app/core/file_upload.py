import os
import uuid

from fastapi import HTTPException, UploadFile

UPLOAD_DIR = "uploads/menu"


def save_menu_image(file: UploadFile) -> str:
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid image format")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    return f"/uploads/menu/{filename}"
