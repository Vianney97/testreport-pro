from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os

from backend.parser.playwright_parser import parse_playwright
from backend.parser.pytest_parser import parse_pytest
from backend.parser.cucumber_parser import parse_cucumber

app = FastAPI(
    title="TestReport Pro API",
    description="Turn your test results into clear, shareable reports",
    version="0.1.0"
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

@app.post("/upload/playwright")
async def upload_playwright(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="File must be a JSON file")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        result = parse_playwright(tmp_path)
        return {"framework": "playwright", "total": result.total, "passed": result.passed, "failed": result.failed, "skipped": result.skipped, "success_rate": result.success_rate, "duration_ms": result.duration_ms, "tests": [{"name": t.name, "status": t.status, "duration_ms": t.duration_ms, "error_message": t.error_message, "file_path": t.file_path} for t in result.tests]}
    finally:
        os.unlink(tmp_path)

@app.post("/upload/pytest")
async def upload_pytest(file: UploadFile = File(...)):
    if not file.filename.endswith(".xml"):
        raise HTTPException(status_code=400, detail="File must be an XML file")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        result = parse_pytest(tmp_path)
        return {"framework": "pytest", "total": result.total, "passed": result.passed, "failed": result.failed, "skipped": result.skipped, "success_rate": result.success_rate, "duration_ms": result.duration_ms, "tests": [{"name": t.name, "status": t.status, "duration_ms": t.duration_ms, "error_message": t.error_message, "file_path": t.file_path} for t in result.tests]}
    finally:
        os.unlink(tmp_path)

@app.post("/upload/cucumber")
async def upload_cucumber(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="File must be a JSON file")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        result = parse_cucumber(tmp_path)
        return {"framework": "cucumber", "total": result.total, "passed": result.passed, "failed": result.failed, "skipped": result.skipped, "success_rate": result.success_rate, "duration_ms": result.duration_ms, "tests": [{"name": t.name, "status": t.status, "duration_ms": t.duration_ms, "error_message": t.error_message, "file_path": t.file_path} for t in result.tests]}
    finally:
        os.unlink(tmp_path)