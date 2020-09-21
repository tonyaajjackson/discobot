#!/usr/bin/python3

import os
import re

import discord
from dotenv import load_dotenv

# Environment setup
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

spotify_regex=re.compile("https:\/\/open.spotify.com\/(.+)\/(.+)\?")

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} is connected')

@client.event 
async def on_message(message):
    if message.author == client.user: return

    await message.channel.send("Received a message!")

    if link := spotify_regex.search(message.content):
        link_type = link.group(1)
        link_id = link.group(2)
        await message.channel.send("Spotify link type: " + link_type + " id: " + link_id)


client.run(TOKEN)
