
from fastapi import FastAPI

app = FastAPI(
    title="TrustVault",
    description="Secure document sharing with an audit trail",
    version="0.1.0",
)


@app.get("/")
def home():
    return {
        "message": "Welcome to TrustVault",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
