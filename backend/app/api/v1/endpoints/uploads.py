"""
File upload endpoints.
"""
import os
import shutil
from pathlib import Path
from typing import Any
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlmodel import Session

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_session
from app.models.upload import Upload
from app.schemas.upload import UploadResponse


router = APIRouter()


@router.post("/", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Upload a file for processing."""

    # Validate file type
    allowed_types = ["application/pdf", "text/plain", "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not supported. Please upload PDF, TXT, or DOC files."
        )

    # Validate file size
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB."
        )

    # Create uploads directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)

    # Generate unique filename
    file_extension = Path(file.filename).suffix
    import uuid
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = upload_dir / unique_filename

    # Save file
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Determine file type for database
    if file.content_type == "application/pdf":
        db_file_type = "pdf"
    elif file.content_type == "text/plain":
        db_file_type = "txt"
    elif file.content_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        db_file_type = "doc"
    else:
        db_file_type = "unknown"

    # Create database record
    upload_record = Upload(
        user_id=current_user.id,
        filename=file.filename,
        filepath=str(file_path),
        file_type=db_file_type,
        file_size=file_size,
        parsing_status="pending"
    )

    session.add(upload_record)
    session.commit()
    session.refresh(upload_record)

    return UploadResponse.from_orm(upload_record)


@router.get("/", response_model=list[UploadResponse])
async def get_user_uploads(
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Get user's uploaded files."""
    from sqlmodel import select

    uploads = session.exec(
        select(Upload)
        .where(Upload.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    ).all()

    return [UploadResponse.from_orm(upload) for upload in uploads]


@router.get("/{upload_id}", response_model=UploadResponse)
async def get_upload(
    upload_id: int,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Get specific upload by ID."""
    upload = session.get(Upload, upload_id)
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )

    # Check ownership
    if upload.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this upload"
        )

    return UploadResponse.from_orm(upload)


@router.delete("/{upload_id}")
async def delete_upload(
    upload_id: int,
    current_user: Any = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """Delete an upload and its associated file."""
    upload = session.get(Upload, upload_id)
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )

    # Check ownership
    if upload.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this upload"
        )

    # Delete physical file
    try:
        if os.path.exists(upload.filepath):
            os.remove(upload.filepath)
    except Exception as e:
        # Log error but don't fail the operation
        print(f"Warning: Could not delete file {upload.filepath}: {e}")

    # Delete database record
    session.delete(upload)
    session.commit()

    return {"message": "Upload deleted successfully"}