from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import subprocess, uuid, shlex, pathlib, os
from dotenv import load_dotenv

# ───── Load environment variables ─────
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

# ───── FastAPI Setup ─────
app = FastAPI(title="Maps Scraper API")
JOBS = {}   # job_id -> {status, log}

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
        # Build command
        cmd = SCRIPT.format(max_rows=max_rows)
        full_cmd = f"cd {str(pathlib.Path(__file__).parents[1])} && {cmd}"
        JOBS[job_id] = {
            "status": "starting",
            "log": f"🟡 Running Command:\n{full_cmd}\n\n"
        }

        # Run subprocess with shell=True (Windows GUI)
        proc = subprocess.Popen(
            full_cmd,
            shell=True,  # ⚠️ Needed on Windows for cmd launching
            cwd=str(pathlib.Path(__file__).parents[1]),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        out, _ = proc.communicate()

        JOBS[job_id] = {
            "status": "done" if proc.returncode == 0 else "error",
            "log": f"[Exit code: {proc.returncode}]\n\n{out}"
        }

    except Exception as e:
        JOBS[job_id] = {
            "status": "error",
            "log": f"💥 Exception: {str(e)}"
        }


# ───── Background Job Endpoint ─────
@app.post("/run")
def run(background_tasks: BackgroundTasks, max_rows: int = 150, creds: HTTPAuthorizationCredentials = Depends(verify_token)):
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "running", "log": ""}
    background_tasks.add_task(_run, job_id, max_rows)
    return {"job_id": job_id}

# ───── Job Status Endpoint ─────
@app.get("/status/{job_id}")
def status(job_id: str, creds: HTTPAuthorizationCredentials = Depends(verify_token)):
    return JOBS.get(job_id, {"error": "not found"})

# ───── Direct Trigger (Debugging Only) ─────
@app.post("/run-direct")
def run_direct(max_rows: int = 150, creds: HTTPAuthorizationCredentials = Depends(verify_token)):
    _run("debug-run", max_rows)
    return {"message": "Run finished – check console or /status/debug-run"}
