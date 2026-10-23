
from sqlalchemy import select

from database import SessionLocal
from models import AuditLog

with SessionLocal() as db:
    events = db.scalars(
        select(AuditLog).order_by(AuditLog.id.desc())
    ).all()

    if not events:
        print("No audit events found yet.")

    for event in events:
        print(
            f"ID: {event.id} | "
            f"Actor: {event.actor_id} | "
            f"Action: {event.action} | "
            f"Document: {event.document_id} | "
            f"Time: {event.timestamp}"
        )
