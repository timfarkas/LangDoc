
import uvicorn
from fastapi import FastAPI
import discordFront
import discordBack
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
 

@app.on_event("startup")
async def startup():
    logger.info("Starting up...")  

    # Start your discordfront.py and discordback.py scripts
    asyncio.ensure_future(discordFront.start_bot())
    asyncio.ensure_future(discordBack.start_bot())


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")
