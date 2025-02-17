from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from neo4j import GraphDatabase
import time

from cartography.sync import Sync, TOP_LEVEL_MODULES
from cartography.config import Config

app = FastAPI(title="Cartography Sync API")

class SyncRequest(BaseModel):
    module_name: str
    neo4j_uri: str
    neo4j_user: Optional[str] = None
    neo4j_password: Optional[str] = None
    neo4j_database: Optional[str] = "neo4j"

@app.post("/sync")
async def sync_module(request: SyncRequest):
    if request.module_name not in TOP_LEVEL_MODULES:
        valid_modules = ", ".join(TOP_LEVEL_MODULES.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Invalid module name. Valid modules are: {valid_modules}"
        )
    
    try:
        # Create Neo4j driver
        neo4j_auth = None
        if request.neo4j_user or request.neo4j_password:
            neo4j_auth = (request.neo4j_user, request.neo4j_password)
        
        neo4j_driver = GraphDatabase.driver(
            request.neo4j_uri,
            auth=neo4j_auth
        )

        # Create sync object with only the requested module
        sync = Sync()
        sync.add_stage(request.module_name, TOP_LEVEL_MODULES[request.module_name])

        # Create config
        config = Config(
            neo4j_uri=request.neo4j_uri,
            neo4j_user=request.neo4j_user,
            neo4j_password=request.neo4j_password,
            neo4j_database=request.neo4j_database,
            update_tag=int(time.time())
        )

        # Run sync
        result = sync.run(neo4j_driver, config)
        
        return {"status": "success", "module": request.module_name}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 