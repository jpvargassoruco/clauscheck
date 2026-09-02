import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_org, get_current_user
from app.models import Document, OcrStatus, Org, User
from app.paperless import PaperlessError, set_owner_permissions, upload_document
from app.schemas.api import DocumentCreateJSON, DocumentDetailOut, DocumentOut, DocumentStatusOut

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def create_document(
    titulo: str | None = Form(default=None),
    texto: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    org: Org = Depends(get_current_org),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Document:
    if file is not None:
        content = await file.read()
        document = Document(
            org_id=org.id,
            titulo=titulo or file.filename or "documento",
            ocr_status=OcrStatus.pending,
            created_by=user.id,
        )
        db.add(document)
        await db.flush()

        try:
            paperless_id = await upload_document(
                filename=file.filename or "documento",
                content=content,
                title=document.titulo,
                tag_ids=[org.paperless_tag_id] if org.paperless_tag_id else None,
            )
            document.paperless_id = paperless_id
            if paperless_id and org.paperless_user_id:
                await set_owner_permissions(paperless_id, org.paperless_user_id)
        except PaperlessError:
            # Document row still exists; ocr_status stays pending and can be
            # retried/polled later via GET /documents/{id}/status.
            pass

        await db.commit()
        await db.refresh(document)
        return document

    if not texto:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Se requiere 'file' o {titulo, texto}"
        )

    payload = DocumentCreateJSON(titulo=titulo or "documento", texto=texto)
    document = Document(
        org_id=org.id,
        titulo=payload.titulo,
        texto=payload.texto,
        ocr_status=OcrStatus.ready,
        created_by=user.id,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    limit: int = 20,
    offset: int = 0,
    org: Org = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> list[Document]:
    result = await db.execute(
        select(Document)
        .where(Document.org_id == org.id)
        .order_by(Document.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def _get_org_document(db: AsyncSession, org: Org, document_id: uuid.UUID) -> Document:
    document = await db.get(Document, document_id)
    if document is None or document.org_id != org.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Documento no encontrado")
    return document


@router.get("/{document_id}", response_model=DocumentDetailOut)
async def get_document(
    document_id: uuid.UUID, org: Org = Depends(get_current_org), db: AsyncSession = Depends(get_db)
) -> Document:
    return await _get_org_document(db, org, document_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID, org: Org = Depends(get_current_org), db: AsyncSession = Depends(get_db)
) -> None:
    document = await _get_org_document(db, org, document_id)
    await db.delete(document)
    await db.commit()


@router.get("/{document_id}/status", response_model=DocumentStatusOut)
async def get_document_status(
    document_id: uuid.UUID, org: Org = Depends(get_current_org), db: AsyncSession = Depends(get_db)
) -> Document:
    return await _get_org_document(db, org, document_id)
