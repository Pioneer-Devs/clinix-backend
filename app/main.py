from fastapi import FastAPI

app = FastAPI(
    title="CLINIX API",
    description="API REST for the CLinic Management System",
    version="1.0.0"
)

@app.get("/health")
async def health():
    return {"status": "ok"}