# main.py (Root)
from fastapi import FastAPI
import uvicorn


from knowledge.api.route import router as knowledge_router
#from TA.api.route import router as ta_router

from core.api.life_span import lifespan
from core.config import App_settings

config = App_settings()
app = FastAPI(title=config.name, lifespan=lifespan)

app.include_router(knowledge_router, prefix=config.endpoint)

#app.include_router(ta_router, prefix="/api/v1/ta")

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
    
