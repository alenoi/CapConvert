import os
import re

import discord
import moviepy.editor as moviepy
import requests
from PIL import Image
from dotenv import load_dotenv
from pillow_heif import register_heif_opener
from pymediainfo import MediaInfo

intents = discord.Intents(messages=True, message_content=True, guilds=True)
intents.typing = True
intents.reactions = True


client = discord.Client(intents=intents)
register_heif_opener()

TOKEN = ""
SERVER = ""

if os.path.isfile(".env"):
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
else:
    print('Cannot find environment file\n')
    TOKEN = input('Please enter your bot TOKEN!\n')
    saveToken = input('Do you want to save this TOKEN?\n y/n')
    if saveToken.upper() == 'Y':
        f = open(".env", "w")
        f.write(f'DISCORD_TOKEN={TOKEN}')
        f.close()


@client.event
async def on_message(self, message: discord.Message) -> None:
    global SERVER
    SERVER = message.message.guild.id


@client.event
async def on_ready():
    for guild in client.guilds:
        print(f'{client.user.name} has connected to {guild.name}!')


@client.event
async def on_message(message):
    files_to_delete: list[str] = []
    files_to_send: list[discord.File] = []
    if not message.author.bot:
        if 'tiktok.com/' in message.content:
            await tiktok_download(files_to_send, files_to_delete, message)
        if len(message.attachments) > 0:
            for item in message.attachments:
                ext = item.url.split('.')[len(item.url.split('.')) - 1].lower()
                if re.search('heic', ext):
                    await heic2jpg(files_to_send, files_to_delete, item)
                elif re.search('hevc', ext) or re.search('mp4', ext):
                    await hevc2mp4(files_to_send, files_to_delete, item)
    if len(files_to_send) > 0:
        try:
            await send_files(files_to_send, message)
        except:
            print("Could not send the file")
    if len(files_to_delete) > 0:
        for item in files_to_delete:
            os.remove(item)


async def tiktok_download(files_to_send, files_to_delete, message):
    url = message.content.split('/')[3]
    ogfilename = f'{url}.mp4'
    filename = f'{ogfilename}_c.mp4'
    os.system(f'python3.10 -m tiktok_downloader --url https://vt.tiktok.com/{url} --tiktok --save {ogfilename}')
    clip = moviepy.VideoFileClip(ogfilename)
    clipsize = 8000000 / os.path.getsize(ogfilename)
    clip = clip.resize(clipsize-0.02)
    clip.write_videofile(f'{filename}', threads=4)
    files_to_send.append(discord.File(filename))
    files_to_delete.append(filename)
    files_to_delete.append(ogfilename)


async def send_files(files_to_send, message):
    CHANNEL = client.get_channel(message.channel.id)
    if message.author.nick:
        mess = f'Let me convert for you the files {message.author.nick} was unable to'
    else:
        mess = f'Let me convert for you the files {message.author.name} was unable to'
    await CHANNEL.send(files=files_to_send,
                       content=mess,
                       # the message you want to appear next to the images
                       reference=message)


async def heic2jpg(files_to_send, files_to_delete, item):
    urlparts_slash = item.url.split('/')
    ogfilename = urlparts_slash[len(urlparts_slash) - 1]
    open(ogfilename, "wb").write(requests.get(item.url).content)
    filename = ogfilename[:len(ogfilename) - 5] + ".jpg"
    image = Image.open(ogfilename)
    image.save(filename, "jpeg")
    files_to_send.append(discord.File(filename))
    files_to_delete.append(filename)
    files_to_delete.append(ogfilename)


async def hevc2mp4(files_to_send, files_to_delete, item):
    urlparts_slash = item.url.split('/')
    ogfilename = urlparts_slash[len(urlparts_slash) - 1]
    open(ogfilename, "wb").write(requests.get(item.url).content)
    codec = await hevc_check(ogfilename)
    print(codec.upper())
    if codec.upper() == 'HEVC' or codec.upper() == 'AV1':
        filename = f'{ogfilename.split(".")[0]}_c.mp4'
        clip = moviepy.VideoFileClip(ogfilename)
        clip.write_videofile(f'{filename}')
        files_to_send.append(discord.File(filename))
        files_to_delete.append(filename)
        files_to_delete.append(ogfilename)


async def hevc_check(ogfilename):
    info = MediaInfo.parse(ogfilename)
    codec = ""
    for track in info.tracks:
        if track.track_type == "Video":
            codec = "{t.format}".format(t=track)
    return codec


if TOKEN != "":
    try:
        client.run(TOKEN)
    except:
        print('Error: The connection to the server cannot be established, please check your serverID and Token!')
else:
    print('Error: There is no valid serverID or Token!')
