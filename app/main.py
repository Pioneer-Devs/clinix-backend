from fastapi import FastAPI

from app.api.v1 import api_router

app = FastAPI(
    title="CLINIX API",
    description="API REST for the Clinic Management System",
    version="1.0.0",
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok"}