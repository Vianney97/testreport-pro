from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os

from backend.parser.universal_parser import universal_parse

app = FastAPI(
    title="TestReport Pro API",
    description="Turn your test results into clear, shareable reports",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "TestReport Pro API is running"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    suffix = ".xml" if file.filename.endswith(".xml") else ".json"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result, framework = universal_parse(tmp_path)
        return {
            "framework": framework,
            "total": result.total,
            "passed": result.passed,
            "failed": result.failed,
            "skipped": result.skipped,
            "success_rate": result.success_rate,
            "duration_ms": result.duration_ms,
            "tests": [
                {
                    "name": t.name,
                    "status": t.status,
                    "duration_ms": t.duration_ms,
                    "error_message": t.error_message,
                    "file_path": t.file_path
                }
                for t in result.tests
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        os.unlink(tmp_path)