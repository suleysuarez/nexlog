from fastapi import FastAPI

app = FastAPI(title="NexLog API")

@app.get("/health")
def health():
    return {"status": "ok", "service": "nexlog-api"}
