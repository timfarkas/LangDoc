from multiprocessing import log_to_stderr
import discord
import requests
import discordBack
import asyncio
import logging
from discord.ext import commands

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("discordFront")

dev_mode = True
BOT_TOKEN = "MTEyNzE5ODMwMDgxMTA1NTE0Ng.GBBFKy.c2qJf9v38nr2_nTp2Pum2wGHCc-9CIxI2xNYNI"

if dev_mode == True:
    ## dev bot token
    BOT_TOKEN = "MTEyNzIzOTQyMzI1MjIzNDM0MA.GNQ7WY.HFRZXogp853gW7uRTz4W4jRsQMNqhEHJEecqcs"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  

class MyBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ready = asyncio.Event()  

    async def on_ready(self):
        logger.info(f"We have logged in as {self.user}")

    async def sendCustomMessages(self, targetChannel, messages):
        if messages and targetChannel:
            for msg in messages:
                   await targetChannel.send(msg)

    async def on_message(self, message):
        logger.info("MESSAGE BY "+str(message.author) + ": " + message.content)
        if message.author == self.user or not message.content:
            return  
        asyncio.create_task(self.process_and_sendMsg(message, logger))
        print("TEST")
        
    async def keep_typing(self, channel, logger = logging.getLogger()):
        return
        #while True:
         #   logger.info("TEST, TSPIGNGNNG")
            #await channel.typing()
            #await asyncio.sleep(5)  # wait for a shorter duration than 10 seconds to ensure the typing indication doesn't expire

    async def process_and_sendMsg(self, message, logger):
        data = {"message": message.content, "user_id": str(message.author.id), "channel": message.channel}
        typing_task = asyncio.create_task(self.keep_typing(data["channel"], logger))
        try:
            response = await discordBack.process_message(self, data)
        finally:
            typing_task.cancel() 
        if response:
            for msg in response:
                await message.channel.send(msg)
        else:
            logger.info("No response generated.")


client = MyBot(intents=intents)

async def start_bot():
    await client.start(BOT_TOKEN)

async def getChannelByName(name):
    channels = client.get_all_channels()
    for channel in channels:
        if channel.name == name:
            return channel
    return None

async def sendCustomMessages(channelName, messages):
    channel = getChannelByName(channelName)
    await client.sendCustomMessages(channel, messages)

