from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import admin, analyses, auth, documents, health, orgs, public, usage

app = FastAPI(title="ClausCheck API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(orgs.router, prefix=API_PREFIX)
app.include_router(documents.router, prefix=API_PREFIX)
app.include_router(analyses.router, prefix=API_PREFIX)
app.include_router(usage.router, prefix=API_PREFIX)
app.include_router(public.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)


@app.get("/")
async def root() -> dict:
    return {"service": "clauscheck-api", "docs": "/docs"}
