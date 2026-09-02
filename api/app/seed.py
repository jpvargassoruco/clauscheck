"""`python -m app.seed` — idempotent bootstrap data.

Creates the base plans, the demo org (`clauscheck-demo`) with its public
corpus, and a superadmin user from `ADMIN_EMAIL`/`ADMIN_PASSWORD`. Then
imports `seed/normativa.json` and `seed/corpus/*.json` if present.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from app.config import settings
from app.db import async_session_maker
from app.models import (
    Analysis,
    AnalysisStatus,
    Articulo,
    CuerpoLegal,
    Document,
    Membership,
    MembershipRole,
    Org,
    Plan,
    User,
)
from app.normativa_import import import_normativa
from app.security import hash_password

logger = logging.getLogger("clauscheck.seed")

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "seed"

PLANS = [
    {"code": "free", "nombre": "Free", "analisis_mes": 5, "docs_max": 10, "precio_bob": 0},
    {"code": "pro", "nombre": "Pro", "analisis_mes": 50, "docs_max": 200, "precio_bob": 150},
    {
        "code": "despacho",
        "nombre": "Despacho",
        "analisis_mes": 500,
        "docs_max": 2000,
        "precio_bob": 800,
    },
]


async def seed_plans(db) -> None:
    for p in PLANS:
        plan = await db.get(Plan, p["code"])
        if plan is None:
            db.add(Plan(**p))
        else:
            for field, value in p.items():
                if field != "code":
                    setattr(plan, field, value)
    await db.commit()


async def seed_demo_org(db) -> Org:
    result = await db.execute(select(Org).where(Org.slug == "clauscheck-demo"))
    org = result.scalars().first()
    if org is None:
        org = Org(slug="clauscheck-demo", nombre="ClausCheck Demo", plan_code="despacho", is_demo=True)
        db.add(org)
        await db.commit()
        await db.refresh(org)
    return org


async def seed_superadmin(db) -> User:
    result = await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
    user = result.scalars().first()
    if user is None:
        user = User(
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            nombre="Superadmin",
            is_superadmin=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif not user.is_superadmin:
        user.is_superadmin = True
        await db.commit()
    return user


async def seed_demo_membership(db, user: User, org: Org) -> None:
    membership = await db.get(Membership, {"user_id": user.id, "org_id": org.id})
    if membership is None:
        db.add(Membership(user_id=user.id, org_id=org.id, role=MembershipRole.owner))
        await db.commit()


async def seed_normativa(db) -> None:
    path = SEED_DIR / "normativa.json"
    if not path.exists():
        logger.info("seed/normativa.json no encontrado, se omite")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    result = await import_normativa(db, data)
    logger.info("normativa importada: %s", result)


async def _resolve_articulo(db, cuerpo_code: str, numero: str, inciso: str | None) -> Articulo | None:
    result = await db.execute(select(CuerpoLegal).where(CuerpoLegal.code == cuerpo_code))
    cuerpo = result.scalars().first()
    if cuerpo is None:
        return None
    result = await db.execute(
        select(Articulo).where(
            Articulo.cuerpo_id == cuerpo.id, Articulo.numero == numero, Articulo.inciso == inciso
        )
    )
    return result.scalars().first()


async def _resolve_dictamen_articulos(db, dictamen: dict) -> dict:
    async def resolve_list(items: list[dict]) -> None:
        for item in items:
            resolved = []
            for ref in item.get("articulos", []):
                articulo = await _resolve_articulo(
                    db, ref.get("cuerpo"), ref.get("numero"), ref.get("inciso")
                )
                if articulo is None:
                    logger.warning("no se pudo resolver articulo %s", ref)
                    continue
                resolved.append(
                    {
                        "articulo_id": str(articulo.id),
                        "cuerpo": ref.get("cuerpo"),
                        "numero": articulo.numero,
                        "inciso": articulo.inciso,
                        "texto": articulo.texto,
                        "fuente_url": articulo.fuente_url,
                    }
                )
            item["articulos"] = resolved

    await resolve_list(dictamen.get("hallazgos", []))
    await resolve_list(dictamen.get("omisiones", []))
    return dictamen


async def seed_corpus(db, org: Org, admin_user: User) -> None:
    corpus_dir = SEED_DIR / "corpus"
    if not corpus_dir.exists():
        logger.info("seed/corpus no encontrado, se omite")
        return

    for path in sorted(corpus_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        doc_data = payload["document"]

        result = await db.execute(
            select(Document).where(Document.org_id == org.id, Document.titulo == doc_data["titulo"])
        )
        document = result.scalars().first()
        if document is None:
            document = Document(
                org_id=org.id,
                titulo=doc_data["titulo"],
                tipo_contrato=doc_data.get("tipo_contrato"),
                rubro=doc_data.get("rubro"),
                ficha=doc_data.get("ficha", {}),
                partes=doc_data.get("partes", []),
                clausulas=doc_data.get("clausulas", []),
                texto=doc_data.get("texto"),
                ocr_status="ready",
                is_public=True,
                created_by=admin_user.id,
            )
            db.add(document)
            await db.flush()

        result = await db.execute(
            select(Analysis).where(
                Analysis.document_id == document.id, Analysis.status == AnalysisStatus.done
            )
        )
        if result.scalars().first() is not None:
            continue

        dictamen = await _resolve_dictamen_articulos(db, payload["dictamen"])
        now = datetime.now(UTC)
        analysis = Analysis(
            org_id=org.id,
            document_id=document.id,
            status=AnalysisStatus.done,
            etapa=7,
            dictamen=dictamen,
            created_by=admin_user.id,
            started_at=now,
            finished_at=now,
        )
        db.add(analysis)
        await db.commit()
        logger.info("corpus importado: %s", path.name)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    async with async_session_maker() as db:
        await seed_plans(db)
        org = await seed_demo_org(db)
        admin_user = await seed_superadmin(db)
        await seed_demo_membership(db, admin_user, org)
        await seed_normativa(db)
        await seed_corpus(db, org, admin_user)
    logger.info("seed completo")


if __name__ == "__main__":
    asyncio.run(main())
