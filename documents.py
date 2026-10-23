import uuid
from pathlib import Path

from fastapi import (
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import AuditLog, Document, Permission, User
from authorization import can_read_document, get_current_user

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = Path("uploads").resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg",
}

ALLOWED_CONTENT_TYPES = {
    ".pdf": {"application/pdf"},
    ".txt": {"text/plain"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
}


@router.post("/", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(default="General"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    original_name = Path(file.filename or "").name.strip()
    extension = Path(original_name).suffix.lower()

    if not original_name or extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file extension",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES[extension]:
        raise HTTPException(
            status_code=400,
            detail="File type does not match the allowed type",
        )

    stored_filename = f"{uuid.uuid4().hex}{extension}"
    destination = (UPLOAD_DIR / stored_filename).resolve()

    if destination.parent != UPLOAD_DIR:
        raise HTTPException(status_code=400, detail="Invalid file path")

    total_size = 0

    try:
        with destination.open("xb") as output:
            while True:
                chunk = await file.read(64 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File exceeds the 5 MB limit",
                    )

                output.write(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty files are not allowed",
            )

        document = Document(
            name=original_name,
            stored_filename=stored_filename,
            owner_id=current_user.id,
            category=category.strip()[:100] or "General",
        )
        
        db.add(document)
        db.flush()  # Assigns the document ID without committing yet

        audit_event = AuditLog(
            actor_id=current_user.id,
            action="upload",
            document_id=document.id,
            details=f"Uploaded document: {document.name}",
        )

        db.add(audit_event)
        db.commit()
        db.refresh(document)

        return {
            "id": document.id,
            "name": document.name,
            "category": document.category,
            "owner_id": document.owner_id,
        }

    except Exception:
        db.rollback()
        if destination.exists():
            destination.unlink()
        raise

    finally:
        await file.close()





@router.get("/")
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = select(Document).where(
        Document.owner_id == current_user.id
    )

    documents = db.scalars(statement).all()

    return [
        {
            "id": document.id,
            "name": document.name,
            "category": document.category,
            "owner_id": document.owner_id,
            "created_at": document.created_at,
        }
        for document in documents
    ]
@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    permission = db.scalar(
        select(Permission).where(
            Permission.document_id == document.id,
            Permission.user_id == current_user.id,
        )
    )

    if not can_read_document(current_user, document, permission):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to download this document",
        )

    file_path = (UPLOAD_DIR / document.stored_filename).resolve()

    if file_path.parent != UPLOAD_DIR or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Document file not found",
        )

    audit_event = AuditLog(
        actor_id=current_user.id,
        action="download",
        document_id=document.id,
        details=f"Downloaded document: {document.name}",
    )

    try:
        db.add(audit_event)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not record the download audit event",
        )

    return FileResponse(
        path=file_path,
        filename=document.name,
        media_type="application/octet-stream",
    )
    