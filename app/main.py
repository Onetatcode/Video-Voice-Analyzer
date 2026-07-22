import os
import time
import logging
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

POLL_INTERVAL = 30


def _poll_pending_reports():
    """Background thread that auto-processes pending reports stuck in queue."""
    from app.routes.processing import _get_supabase_client, run_processing_task

    logger.info("Pending report poller started (interval=%ds)", POLL_INTERVAL)
    while True:
        try:
            supabase = _get_supabase_client()
            if supabase:
                result = supabase.table("reports").select("id").eq("status", "pending").execute()
                for row in (result.data or []):
                    report_id = row["id"]
                    logger.info("Poller picked up pending report: %s", report_id)
                    t = threading.Thread(target=run_processing_task, args=(report_id,), daemon=True)
                    t.start()
        except Exception as e:
            logger.error("Poller error: %s", e)
        time.sleep(POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    t = threading.Thread(target=_poll_pending_reports, daemon=True)
    t.start()
    yield


app = FastAPI(title="Body Language and Voice Analyzer API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routes import processing
app.include_router(processing.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "body-language-voice-analyzer"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)