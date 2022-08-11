import os

import discord
import requests
from PIL import Image
from dotenv import load_dotenv
from pillow_heif import register_heif_opener

client = discord.Client()
register_heif_opener()

TOKEN = ""
SERVER = ""

if os.path.isfile(".env"):
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
else:
    print('Cannot find environment file\n')
    TOKEN = input('Please enter your bot TOKEN!\n')


@client.event
async def on_message(self, message: discord.Message) -> None:
    global SERVER
    SERVER = message.message.guild.id


@client.event
async def on_ready():
    print(f'{client.user.name} has connected to {client.guilds[0].name}!')


@client.event
async def on_message(message):
    files_to_delete: list[str] = []
    files_to_send: list[discord.File] = []
    isheic = False
    if not message.author.bot and len(message.attachments) > 0:
        for item in message.attachments:
            urlparts_dot = item.url.split('.')
            if urlparts_dot[len(urlparts_dot) - 1].lower() == "heic":
                isheic = True
                await save_and_convert(files_to_send, files_to_delete, item)
        if isheic:
            await send_images(files_to_send, message)
            for item in files_to_delete:
                os.remove(item)


async def send_images(files_to_send, message):
    CHANNEL = client.get_channel(message.channel.id)
    await CHANNEL.send(files=files_to_send,
                       content=message.author.nick + " ezt nem bírta rendesen elküldeni:",
                       # the message you want to appear next to the images
                       reference=message)


async def save_and_convert(files_to_send, files_to_delete, item):
    urlparts_slash = item.url.split('/')
    ogfilename = urlparts_slash[len(urlparts_slash) - 1]
    open(ogfilename, "wb").write(requests.get(item.url).content)
    filename = ogfilename[:len(ogfilename) - 5] + ".jpg"
    image = Image.open(ogfilename)
    image.save(filename, "jpeg")
    files_to_send.append(discord.File(filename))
    files_to_delete.append(filename)
    os.remove(ogfilename)


if TOKEN != "":
    try:
        client.run(TOKEN)
    except:
        print('Error: The connection to the server cannot be established, please check your serverID and Token!')
else:
    print('Error: There is no valid serverID or Token!')
