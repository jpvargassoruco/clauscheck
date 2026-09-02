"""Stage 1 — normalizar: resolve `documents.texto` (HLD §5).

If the document already has `texto` (created via the JSON path, or a prior
run), it is used as-is. Otherwise, if it has a `paperless_id` (file upload
path), poll paperless for OCR `content` until it is non-empty or
`POLL_TIMEOUT` elapses — in which case the stage fails with a clear Spanish
error and marks `document.ocr_status = failed`.

`POLL_TIMEOUT`/`POLL_INTERVAL` are module-level (not `app.config.settings`)
so tests can shrink them via monkeypatch without touching global config.
"""

import asyncio

from app.models import Document, OcrStatus
from app.paperless import PaperlessError, get_content

POLL_TIMEOUT = 300.0  # ~5 min, per HLD §5
POLL_INTERVAL = 5.0


class NormalizarError(Exception):
    """Raised when stage 1 cannot resolve a non-empty document text."""


async def normalizar(document: Document) -> str:
    if document.texto and document.texto.strip():
        return document.texto

    if not document.paperless_id:
        raise NormalizarError(
            "El documento no tiene texto y no está asociado a un archivo en paperless."
        )

    elapsed = 0.0
    while True:
        try:
            content = await get_content(document.paperless_id)
        except PaperlessError as exc:
            raise NormalizarError(f"Error consultando el OCR de paperless: {exc}") from exc

        if content and content.strip():
            document.texto = content
            document.ocr_status = OcrStatus.ready
            return content

        if elapsed >= POLL_TIMEOUT:
            document.ocr_status = OcrStatus.failed
            raise NormalizarError(
                "Tiempo de espera agotado esperando el OCR de paperless (más de 5 minutos)."
            )

        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
