import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Analysis, AnalysisStatus, Articulo, CuerpoLegal, Document
from app.schemas.api import ArticuloPublicOut, PublicCorpusItem
from app.schemas.dictamen import dictamen_json_schema

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/schema/dictamen")
async def get_dictamen_schema() -> dict:
    return dictamen_json_schema()


@router.get("/corpus", response_model=list[PublicCorpusItem])
async def list_public_corpus(db: AsyncSession = Depends(get_db)) -> list[PublicCorpusItem]:
    result = await db.execute(
        select(Document, Analysis)
        .join(
            Analysis,
            (Analysis.document_id == Document.id) & (Analysis.status == AnalysisStatus.done),
            isouter=True,
        )
        .where(Document.is_public.is_(True))
        .order_by(Document.created_at.desc())
    )

    items: list[PublicCorpusItem] = []
    for document, analysis in result.all():
        dictamen = analysis.dictamen if analysis else None
        items.append(
            PublicCorpusItem(
                id=document.id,
                titulo=document.titulo,
                tipo_contrato=document.tipo_contrato,
                rubro=document.rubro,
                indice_riesgo=dictamen.get("indice_riesgo") if dictamen else None,
                nivel=dictamen.get("nivel") if dictamen else None,
                hallazgos=len(dictamen.get("hallazgos", [])) if dictamen else None,
            )
        )
    return items


@router.get("/corpus/{document_id}")
async def get_public_corpus_item(
    document_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> dict:
    document = await db.get(Document, document_id)
    if document is None or not document.is_public:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Documento no encontrado")

    result = await db.execute(
        select(Analysis)
        .where(Analysis.document_id == document.id, Analysis.status == AnalysisStatus.done)
        .order_by(Analysis.created_at.desc())
    )
    analysis = result.scalars().first()

    return {
        "document": {
            "id": str(document.id),
            "titulo": document.titulo,
            "tipo_contrato": document.tipo_contrato,
            "rubro": document.rubro,
            "ficha": document.ficha,
            "partes": document.partes,
            "clausulas": document.clausulas,
            "texto": document.texto,
        },
        "dictamen": analysis.dictamen if analysis else None,
    }


@router.get("/normativa/articulos/{articulo_id}", response_model=ArticuloPublicOut)
async def get_public_articulo(
    articulo_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> ArticuloPublicOut:
    articulo = await db.get(Articulo, articulo_id)
    if articulo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado")
    cuerpo = await db.get(CuerpoLegal, articulo.cuerpo_id)

    return ArticuloPublicOut(
        id=articulo.id,
        cuerpo=cuerpo.code if cuerpo else "",
        numero=articulo.numero,
        inciso=articulo.inciso,
        titulo=articulo.titulo,
        texto=articulo.texto,
        fuente_url=articulo.fuente_url,
        vigente=articulo.vigente,
    )
