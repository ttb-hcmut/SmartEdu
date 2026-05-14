# main.py (Root)
from fastapi import FastAPI
import uvicorn


from knowledge.api.route import router as knowledge_router
from TA.api.route import router as ta_router
from student.api import router as student_router

from core.api.life_span import lifespan
from core.config import App_settings

config = App_settings()
app = FastAPI(title=config.name, lifespan=lifespan)

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
        reload_dirs=["core", "knowledge", "TA", "nosql", "graph"]
    )
    
