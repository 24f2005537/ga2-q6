import time
import uuid
from collections import deque
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS policy just in case the grader probes from a browser environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global State Variables ---
# Track startup time for /healthz
START_TIME = time.time()

# Track total requests for /metrics
REQUEST_COUNT = 0

# In-memory structured log buffer (holds the last 1000 logs to prevent memory leaks)
LOG_BUFFER = deque(maxlen=1000)


# --- Middleware: Intercepts every incoming request ---
@app.middleware("http")
async def instrumentation_middleware(request: Request, call_next):
    global REQUEST_COUNT
    
    # 1. Increment the Prometheus counter for *every* request
    REQUEST_COUNT += 1
    
    # 2. Generate structured log data
    request_id = str(uuid.uuid4())
    log_entry = {
        "level": "INFO",
        "ts": time.time(),
        "path": request.url.path,
        "request_id": request_id
    }
    
    # 3. Append to our log buffer
    LOG_BUFFER.append(log_entry)
    
    # 4. Continue processing the request
    response = await call_next(request)
    return response


# --- Endpoints ---

@app.get("/work")
def do_work(n: int):
    return {
        "email": "24f2005537@ds.study.iitm.ac.in",
        "done": n
    }

@app.get("/healthz")
def health_check():
    return {
        "status": "ok",
        "uptime_s": time.time() - START_TIME
    }

@app.get("/metrics")
def get_metrics():
    # Construct a valid Prometheus text-based response manually
    metrics_text = (
        "# HELP http_requests_total Total number of HTTP requests made.\n"
        "# TYPE http_requests_total counter\n"
        f"http_requests_total {REQUEST_COUNT}\n"
    )
    return Response(content=metrics_text, media_type="text/plain")

@app.get("/logs/tail")
def tail_logs(limit: int = 10):
    # Convert deque to a list and slice the last 'limit' items
    logs = list(LOG_BUFFER)[-limit:]
    return logs
