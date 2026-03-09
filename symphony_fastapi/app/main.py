from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.database import Base, engine
from app.api.routers import projects, settings, webhooks, tasks
import os

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Symphony Adaptation",
    description="Orchestrational AI Agent API",
    version="1.0.0",
    docs_url="/api-docs" # Changed docs endpoint as requested
)

app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}

# Ensure static folder exists
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", include_in_schema=False)
def root():
    return FileResponse("app/static/index.html")
