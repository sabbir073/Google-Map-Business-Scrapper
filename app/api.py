from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import subprocess, uuid, shlex, pathlib, os, asyncio
from dotenv import load_dotenv

# ───── Load environment variables ─────
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

# ───── FastAPI Setup ─────
app = FastAPI(title="Maps Scraper API")
JOBS = {}  # job_id -> {status, log}

# ───── Allow CORS ─────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.smartscrap.site",
        "https://gmap.smartscrap.site",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# ───── Script Command Template ─────
SCRIPT = "python -m app.main --max {max_rows} --log INFO"

# ───── Security Setup ─────
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )

# ───── Scraper Runner ─────
def _run(job_id: str, max_rows: int):
    try:
        cmd = SCRIPT.format(max_rows=max_rows)
        full_cmd = f"cd {str(pathlib.Path(__file__).parents[1])} && {cmd}"
        JOBS[job_id] = {
            "status": "starting",
            "log": f"🟡 Running Command:\n{full_cmd}\n\n"
        }

        proc = subprocess.Popen(
            full_cmd,
            shell=True,
            cwd=str(pathlib.Path(__file__).parents[1]),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        log_lines = ""
        for line in iter(proc.stdout.readline, ''):
            log_lines += line
            JOBS[job_id]["log"] = log_lines

        proc.stdout.close()
        proc.wait()

        JOBS[job_id]["status"] = "done" if proc.returncode == 0 else "error"
        JOBS[job_id]["log"] += f"\n[Exit code: {proc.returncode}]"

    except Exception as e:
        JOBS[job_id] = {
            "status": "error",
            "log": f"💥 Exception: {str(e)}"
        }

# ───── API Endpoints ─────

@app.options("/run")
async def options_run():
    response = JSONResponse(content={"message": "ok"})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
    return response

@app.post("/run")
def run(background_tasks: BackgroundTasks, max_rows: int = 150, creds: HTTPAuthorizationCredentials = Depends(verify_token)):
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "running", "log": ""}
    background_tasks.add_task(_run, job_id, max_rows)
    return {"job_id": job_id}

@app.get("/status/{job_id}")
def status(job_id: str, creds: HTTPAuthorizationCredentials = Depends(verify_token)):
    return JOBS.get(job_id, {"error": "not found"})

@app.options("/run-direct")
async def options_run_direct():
    response = JSONResponse(content={"message": "ok"})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
    return response

@app.post("/run-direct")
def run_direct(max_rows: int = 150, creds: HTTPAuthorizationCredentials = Depends(verify_token)):
    _run("debug-run", max_rows)
    return {"message": "Run finished – check console or /status/debug-run"}

# ───── WebSocket Log Stream ─────
@app.websocket("/ws/logs/{job_id}")
async def log_stream(websocket: WebSocket, job_id: str):
    await websocket.accept()
    last_log = ""
    heartbeat_interval = 5  # seconds
    heartbeat_count = 0

    try:
        while True:
            await asyncio.sleep(1)
            heartbeat_count += 1

            job = JOBS.get(job_id)
            if not job:
                await websocket.send_text("❌ Job not found.")
                break

            current_log = job["log"]
            if current_log != last_log:
                await websocket.send_text(current_log)
                last_log = current_log

            if heartbeat_count >= heartbeat_interval:
                await websocket.send_text("💓 heartbeat")
                heartbeat_count = 0

            if job["status"] in ("done", "error"):
                break

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {job_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass
