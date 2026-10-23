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
from pydantic import BaseModel, Field

from authorization import (
    can_manage_sharing,
    can_read_document,
    get_current_user,
)

router = APIRouter(prefix="/documents", tags=["Documents"])

class ShareDocumentInput(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    can_read: bool = True
    can_edit: bool = False

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
    owned_documents = db.scalars(
        select(Document).where(Document.owner_id == current_user.id)
    ).all()

    shared_documents = db.scalars(
        select(Document)
        .join(Permission, Permission.document_id == Document.id)
        .where(
            Permission.user_id == current_user.id,
            (Permission.can_read == True) | (Permission.can_edit == True),
        )
    ).all()

    all_documents = {
        doc.id: doc
        for doc in owned_documents + shared_documents
    }

    return [
        {
            "id": doc.id,
            "name": doc.name,
            "category": doc.category,
            "owner_id": doc.owner_id,
            "is_owner": doc.owner_id == current_user.id,
        }
        for doc in all_documents.values()
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

@router.post("/{document_id}/share")
def share_document(
    document_id: int,
    data: ShareDocumentInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if not can_manage_sharing(current_user, document):
        raise HTTPException(
            status_code=403,
            detail="Only the document owner can manage sharing",
        )

    username = data.username.strip().lower()
    target_user = db.scalar(
        select(User).where(User.username == username)
    )

    if target_user is None or not target_user.is_active:
        raise HTTPException(status_code=404, detail="Active user not found")

    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You already own this document",
        )

    permission = db.scalar(
        select(Permission).where(
            Permission.document_id == document.id,
            Permission.user_id == target_user.id,
        )
    )

    if permission is None:
        permission = Permission(
            document_id=document.id,
            user_id=target_user.id,
        )
        db.add(permission)

    permission.can_read = data.can_read or data.can_edit
    permission.can_edit = data.can_edit

    db.add(
        AuditLog(
            actor_id=current_user.id,
            action="share",
            document_id=document.id,
            details=f"Shared with {target_user.username}; read={permission.can_read}; edit={permission.can_edit}",
        )
    )

    db.commit()

    return {
        "message": "Document permissions updated",
        "document_id": document.id,
        "username": target_user.username,
        "can_read": permission.can_read,
        "can_edit": permission.can_edit,
    }
@router.delete("/{document_id}/share/{username}")
def revoke_document_access(
    document_id: int,
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if not can_manage_sharing(current_user, document):
        raise HTTPException(
            status_code=403,
            detail="Only the document owner can manage sharing",
        )

    target_user = db.scalar(
        select(User).where(User.username == username.strip().lower())
    )

    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    permission = db.scalar(
        select(Permission).where(
            Permission.document_id == document.id,
            Permission.user_id == target_user.id,
        )
    )

    if permission is None:
        raise HTTPException(
            status_code=404,
            detail="Sharing permission not found",
        )

    db.delete(permission)
    db.add(
        AuditLog(
            actor_id=current_user.id,
            action="revoke_share",
            document_id=document.id,
            details=f"Revoked access for {target_user.username}",
        )
    )
    db.commit()

    return {
        "message": "Document access revoked",
        "document_id": document.id,
        "username": target_user.username,
    }