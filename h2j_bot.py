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
    SERVER = int(os.getenv('DISCORD_SERVER'))
else:
    print('Cannot find environment file\n')
    TOKEN = input('Please enter your bot TOKEN!\n')
    SERVER = input('Please enter the ID of your server!\n')


@client.event
async def on_ready():
    print(f'{client.user.name} has connected to {client.get_guild(SERVER).name}!')


@client.event
async def on_message(message):
    files_to_delete: list[str] = []
    files_to_send: list[discord.File] = []
    if not message.author.bot:
        if len(message.attachments) > 0:
            for item in message.attachments:
                filename = await save_and_convert(files_to_send, item)
                files_to_delete.append(filename)
            await send_images(files_to_send, message)
            for item in files_to_delete:
                os.remove(item)


async def send_images(files_to_send, message):
    CHANNEL = client.get_channel(message.channel.id)
    await CHANNEL.send(files=files_to_send,
                       content=message.author.nick + " ezt nem bírta rendesen elküldeni:",
                       # the message you want to appear next to the images
                       reference=message)


async def save_and_convert(files_to_send, item):
    urlparts_dot = item.url.split('.')
    if urlparts_dot[len(urlparts_dot) - 1].lower() == "heic":
        urlparts_slash = item.url.split('/')
        ogfilename = urlparts_slash[len(urlparts_slash) - 1]
        open(ogfilename, "wb").write(requests.get(item.url).content)
        filename = ogfilename[:len(ogfilename) - 5] + ".jpg"
        image = Image.open(ogfilename)
        image.save(filename, "jpeg")
        files_to_send.append(discord.File(filename))
        os.remove(ogfilename)
    return filename


if TOKEN != "" and SERVER != "":
    try:
        client.run(TOKEN)
    except:
        print('Error: The connection to the server cannot be established, please check your serverID and Token!')
else:
    print('Error: There is no valid serverID or Token!')
