import discord
import requests
import discordBack
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dev_mode = True
BOT_TOKEN = "MTEyNzE5ODMwMDgxMTA1NTE0Ng.GBBFKy.c2qJf9v38nr2_nTp2Pum2wGHCc-9CIxI2xNYNI"

if dev_mode == True:
    ## dev bot token
    BOT_TOKEN = "MTEyNzE5ODMwMDgxMTA1NTE0Ng.GBBFKy.c2qJf9v38nr2_nTp2Pum2wGHCc-9CIxI2xNYNI"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  

class MyBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ready = asyncio.Event()  

    async def on_ready(self):
        logger.info(f"We have logged in as {self.user}")

    async def on_message(self, message):
        logger.info("MESSAGE BY "+str(message.author) + ": " + message.content)
        if message.author == self.user or not message.content:
            return  

        
        data = {"message": message.content, "user_id": str(message.author.id)}
        response = await discordBack.process_message(data)
        
        if response:
            for msg in response:
                await message.channel.send(msg)
        else:
            logger.info("No response generated.")

client = MyBot(intents=intents)

async def start_bot(loop):
    client.loop = loop
    await client.start(BOT_TOKEN)


