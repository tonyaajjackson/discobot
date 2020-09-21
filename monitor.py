#!/usr/bin/python3

# Get messages from discord

import os

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} is connected')

@client.event 
async def on_message(message):
    if message.author != client.user:
        await message.channel.send("Message received")


client.run(TOKEN)
