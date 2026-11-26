from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles



from traffic_manager import TrafficManager

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

manager = TrafficManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    manager.stop(timeout=10)


app = FastAPI(
    title="AI Based Smart Traffic Management System",
    description="AI-powered traffic monitoring and management API",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
@app.get("/index.html")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/traffic-analytics.html")
def analytics():
    return FileResponse(FRONTEND_DIR / "traffic-analytics.html")


@app.post("/api/start-monitoring")
def start_monitoring():
    try:
        return manager.start()
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error))


@app.post("/api/stop-monitoring")
def stop_monitoring():
    stopped = manager.stop(timeout=10)

    if not stopped:
        raise HTTPException(
            status_code=504,
            detail="Traffic monitoring is still stopping."
        )

    return manager.get_status()


@app.get("/api/status")
def get_status():
    return manager.get_status()


@app.get("/api/analytics")
def get_analytics():
    return manager.get_analytics()


@app.get("/api/video-feed")
def video_feed():
    status = manager.get_status()

    if status["status"] in ["stopped", "error"]:
        raise HTTPException(
            status_code=409,
            detail="Traffic monitoring is not active."
        )

    return StreamingResponse(
        manager.generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


app.mount(
    "/css",
    StaticFiles(directory=FRONTEND_DIR / "css"),
    name="css"
)

app.mount(
    "/js",
    StaticFiles(directory=FRONTEND_DIR / "js"),
    name="js"
)

app.mount(
    "/assets",
    StaticFiles(directory=FRONTEND_DIR / "assets"),
    name="assets"
)