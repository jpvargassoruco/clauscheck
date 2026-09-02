"""Async client for paperless-ngx (HLD §5).

The paperless token/URLs are never exposed to end users. On org creation we
provision a dedicated paperless user + tag + storage path per org so that
documents can be scoped and only that org's paperless user can see them.
If paperless is unreachable at org-creation time we still create the org and
leave the paperless ids null (logged as a warning) so tests don't depend on
paperless being up.
"""

import asyncio
import logging
import uuid

import httpx

from app.config import settings

logger = logging.getLogger("clauscheck.paperless")


class PaperlessError(Exception):
    pass


def _client() -> httpx.AsyncClient:
    headers = {"Authorization": f"Token {settings.PAPERLESS_API_TOKEN}"}
    return httpx.AsyncClient(base_url=settings.PAPERLESS_URL, headers=headers, timeout=30.0)


class PaperlessOrgResources:
    def __init__(
        self,
        user_id: int | None = None,
        tag_id: int | None = None,
        storage_path_id: int | None = None,
    ):
        self.user_id = user_id
        self.tag_id = tag_id
        self.storage_path_id = storage_path_id


async def provision_org(slug: str, org_id: uuid.UUID) -> PaperlessOrgResources:
    """Create the paperless user/tag/storage-path for a new org.

    Returns ids left as None (with a warning logged) if paperless is
    unreachable, so org creation never fails because of paperless.
    """
    try:
        async with _client() as client:
            user_resp = await client.post(
                "/api/users/",
                json={
                    "username": f"org-{slug}",
                    "is_active": True,
                    "password": uuid.uuid4().hex,
                },
            )
            user_resp.raise_for_status()
            user_id = user_resp.json()["id"]

            tag_resp = await client.post("/api/tags/", json={"name": f"org:{org_id}"})
            tag_resp.raise_for_status()
            tag_id = tag_resp.json()["id"]

            sp_resp = await client.post(
                "/api/storage_paths/",
                json={"name": f"orgs/{org_id}", "path": f"orgs/{org_id}/{{title}}"},
            )
            sp_resp.raise_for_status()
            storage_path_id = sp_resp.json()["id"]

        return PaperlessOrgResources(user_id, tag_id, storage_path_id)
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        logger.warning("paperless unreachable/failed while provisioning org %s: %s", slug, exc)
        return PaperlessOrgResources()


async def upload_document(
    filename: str,
    content: bytes,
    title: str,
    tag_ids: list[int] | None = None,
    poll_timeout: float = 60.0,
    poll_interval: float = 2.0,
) -> int | None:
    """Upload a file, poll the task until it resolves, and return the paperless document id."""
    try:
        async with _client() as client:
            files = {"document": (filename, content)}
            data: dict = {"title": title}
            if tag_ids:
                for tag_id in tag_ids:
                    data.setdefault("tags", []).append(tag_id)
            resp = await client.post("/api/documents/post_document/", data=data, files=files)
            resp.raise_for_status()
            task_id = resp.text.strip().strip('"')

            elapsed = 0.0
            while elapsed < poll_timeout:
                task_resp = await client.get("/api/tasks/", params={"task_id": task_id})
                task_resp.raise_for_status()
                tasks = task_resp.json()
                if tasks:
                    task = tasks[0]
                    status = task.get("status")
                    if status == "SUCCESS":
                        return task.get("related_document") or task.get("document_id")
                    if status == "FAILURE":
                        raise PaperlessError(f"paperless task failed: {task.get('result')}")
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
            raise PaperlessError("timeout esperando el procesamiento de paperless")
    except httpx.HTTPError as exc:
        raise PaperlessError(str(exc)) from exc


async def set_owner_permissions(document_id: int, owner_user_id: int) -> None:
    try:
        async with _client() as client:
            resp = await client.patch(
                f"/api/documents/{document_id}/",
                json={
                    "owner": owner_user_id,
                    "permissions": {
                        "view": {"users": [owner_user_id], "groups": []},
                        "change": {"users": [owner_user_id], "groups": []},
                    },
                },
            )
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise PaperlessError(str(exc)) from exc


async def get_content(document_id: int) -> str:
    try:
        async with _client() as client:
            resp = await client.get(f"/api/documents/{document_id}/")
            resp.raise_for_status()
            return resp.json().get("content", "")
    except httpx.HTTPError as exc:
        raise PaperlessError(str(exc)) from exc


async def search(query: str, tag_id: int | None = None) -> list[dict]:
    params: dict = {"query": query}
    if tag_id is not None:
        params["tags__id__all"] = tag_id
    try:
        async with _client() as client:
            resp = await client.get("/api/documents/", params=params)
            resp.raise_for_status()
            return resp.json().get("results", [])
    except httpx.HTTPError as exc:
        raise PaperlessError(str(exc)) from exc
