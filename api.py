import prometheus_client
import uvicorn
from fastapi import FastAPI
import asyncio

app = FastAPI()
server = None

@app.get("/")
async def home():
    return {"Hello": "World"}

@app.get("/readyz")
async def readiness():
    return {"status": "OK"}

@app.get("/livez")
async def liveness():
    return await readiness()

async def serve(port):
    metrics = prometheus_client.make_asgi_app()
    app.mount("/metrics", metrics)
    config = uvicorn.Config(app=app, port=port, log_level="info", host="0.0.0.0")
    server = uvicorn.Server(config)
    await server.serve()
