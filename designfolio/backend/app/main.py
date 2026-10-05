"""DesignFolio FastAPI entry point."""
from fastapi import FastAPI
from app.routers.auth import router as auth_router

app = FastAPI(title="DesignFolio API", version="0.1.0")
app.include_router(auth_router)

@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok"}
