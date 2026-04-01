from fastapi import HTTPException, UploadFile

ALLOWED_TYPES = ["image/jpeg", "image/png"]
MAX_SIZE = 5 * 1024 * 1024  # 5MB


async def validate_image(file: UploadFile):

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG and PNG allowed")

    contents = await file.read()

    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    return contents