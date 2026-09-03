import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.deps import get_current_org, get_current_user
from app.llm.base import LLMError
from app.llm.registry import get_default_provider
from app.models import Document, OcrStatus, Org, Plan, Usage, User
from app.paperless import PaperlessError, get_content, set_owner_permissions, upload_document
from app.periodo import current_periodo
from app.pipeline.pricing import estimate_cost_usd, estimate_tokens_from_palabras
from app.pipeline.words import contar_palabras
from app.schemas.api import (
    DocumentCreateJSON,
    DocumentDetailOut,
    DocumentEstimateOut,
    DocumentOut,
    DocumentStatusOut,
)

router = APIRouter(prefix="/documents", tags=["documents"])

_MAX_MB = settings.MAX_UPLOAD_BYTES // (1024 * 1024)


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def create_document(
    request: Request,
    org: Org = Depends(get_current_org),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Document:
    titulo: str | None = None
    texto: str | None = None
    file: UploadFile | None = None

    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Cuerpo JSON inválido")
        titulo = payload.get("titulo")
        texto = payload.get("texto")
    else:
        form = await request.form()
        raw_titulo = form.get("titulo")
        raw_texto = form.get("texto")
        titulo = raw_titulo if isinstance(raw_titulo, str) else None
        texto = raw_texto if isinstance(raw_texto, str) else None
        raw_file = form.get("file")
        # starlette returns its own UploadFile (fastapi.UploadFile is a subclass, so isinstance fails)
        if raw_file is not None and not isinstance(raw_file, str) and hasattr(raw_file, "read"):
            file = raw_file  # type: ignore[assignment]

    # Hard input caps (item 2 of the plan): independent of plan/quota,
    # protect against abuse regardless of which plan the org is on.
    if texto and len(texto) > settings.MAX_TEXTO_CHARS:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"El texto pegado supera el límite de {settings.MAX_TEXTO_CHARS:,} "
                "caracteres. Divídalo en partes más pequeñas."
            ),
        )

    if file is not None:
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_BYTES:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"El archivo supera el límite de {_MAX_MB} MB.",
            )

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
        palabras=contar_palabras(payload.texto),
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
    document = await _get_org_document(db, org, document_id)
    # Sync OCR result from paperless while the document is still pending.
    if document.ocr_status == OcrStatus.pending and document.paperless_id:
        try:
            content = await get_content(document.paperless_id)
        except PaperlessError:
            content = ""
        if content and content.strip():
            document.texto = content
            document.palabras = contar_palabras(content)
            document.ocr_status = OcrStatus.ready
            await db.commit()
            await db.refresh(document)
    return document


@router.get("/{document_id}/estimate", response_model=DocumentEstimateOut)
async def estimate_document(
    document_id: uuid.UUID,
    org: Org = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> DocumentEstimateOut:
    document = await _get_org_document(db, org, document_id)
    palabras = document.palabras or contar_palabras(document.texto)

    plan = await db.get(Plan, org.plan_code)
    periodo = current_periodo()
    usage = await db.get(Usage, {"org_id": org.id, "periodo": periodo})
    used_analisis = usage.analisis_count if usage else 0
    used_palabras = usage.palabras_count if usage else 0

    motivos: list[str] = []
    if plan is None:
        motivos.append("El plan de la organización no existe.")
    else:
        if palabras > plan.palabras_max_doc:
            motivos.append(
                f"El documento tiene {palabras:,} palabras y el plan permite "
                f"{plan.palabras_max_doc:,} por documento."
            )
        if used_analisis >= plan.analisis_mes:
            motivos.append("La organización ya usó todos los análisis del mes.")
        if used_palabras + palabras > plan.palabras_mes:
            restantes = max(plan.palabras_mes - used_palabras, 0)
            motivos.append(
                f"Quedan {restantes:,} palabras disponibles este mes y el documento "
                f"tiene {palabras:,}."
            )

    try:
        provider = await get_default_provider(db)
        provider_code, model = provider.code, provider.model
    except LLMError:
        provider_code, model = "deepseek", "deepseek-chat"

    return DocumentEstimateOut(
        palabras=palabras,
        tokens_estimados=estimate_tokens_from_palabras(palabras),
        costo_estimado_usd=estimate_cost_usd(provider_code, model, palabras),
        dentro_del_plan=not motivos,
        motivo=" ".join(motivos),
    )
