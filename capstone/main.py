# main.py (Root)
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


from knowledge.api.route import router as knowledge_router
from TA.api.route import router as ta_router
from student.api import router as student_router

from core.api.life_span import lifespan
from core.config import App_settings

config = App_settings()
app = FastAPI(title=config.name, lifespan=lifespan)

# allow the browser frontend to call chat-poll + presigned-upload endpoints directly.
# origins from env; "*" means all (dev only). bearer header auth, so credentials off.
_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(knowledge_router, prefix=config.kg_end)
if config.ta_end:
    app.include_router(ta_router, prefix=config.ta_end)
if config.stu_end:
    app.include_router(student_router, prefix=config.stu_end)

@app.get("/")
def root():
    return {"message": f"{config.name} is Running"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=config.port, 
        reload=True,
        reload_dirs=["core", "knowledge", "TA", "student"]
    )
    
