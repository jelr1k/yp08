"""DesignFolio FastAPI entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router
from app.routers.catalog import router as catalog_router
from app.routers.works import router as works_router

app = FastAPI(title="DesignFolio API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(works_router)


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok"}
