import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "amazon"
REPORT_DIR = BASE_DIR / "reports" / "amazon"

app = FastAPI()
templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))


def get_latest_json() -> Path | None:
    files = sorted(DATA_DIR.glob("*-products.json"))
    return files[-1] if files else None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    latest = get_latest_json()
    products = []
    if latest and latest.exists():
        products = json.loads(latest.read_text(encoding="utf-8"))
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "products": products},
    )


@app.get("/files", response_class=HTMLResponse)
async def files_view(request: Request) -> HTMLResponse:
    json_files = sorted(DATA_DIR.glob("*.json"))
    csv_files = sorted(REPORT_DIR.glob("*.csv"))
    return templates.TemplateResponse(
        "files.html",
        {
            "request": request,
            "json_files": json_files,
            "csv_files": csv_files,
        },
    )


@app.get("/download")
async def download(path: str):
    file_path = Path(path)
    if not file_path.exists():
        return JSONResponse({"error": "file not found"}, status_code=404)
    return FileResponse(file_path)


@app.post("/api/run/amazon")
async def run_amazon():
    """Amazonスクレイピングジョブを別プロセスで実行."""
    # 既存の CLI 実行と同じコマンドをサブプロセスとして起動する
    result = subprocess.run(
        [sys.executable, "-m", "jobs.daily_amazon"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
    )
    return {
        "status": "ok" if result.returncode == 0 else "error",
        "run_at": datetime.now().isoformat(),
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

