import os
import re
import sys

import certifi
import requests
import urllib3
import discord
import moviepy.editor as moviepy
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
fileSizeLimit = 8000000

if os.path.isfile(".env"):
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
else:
    print('Cannot find environment file\n')
    TOKEN = input('Please enter your bot TOKEN!\n')
    saveToken = input('Do you want to save this TOKEN?\n [Y/N] \n')
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
    if not message.author.bot:
        if 'tiktok.com/' in message.content or len(message.attachments) > 0:
            await media_process(message)


class mediaFile:
    url: str
    fileName: str
    convertedFile: str
    type: str


async def media_process(ogmsg):
    mediafiles: list[mediaFile] = []
    if 'tiktok.com' in ogmsg.content:
        url = ogmsg.content.split("tiktok.com")[1]
        if "/video/" in url:
            url = url.split("?")[0]
            url = f"https://tiktok.com{url}"
        else:
            url = url.split("/")[1]
            url = f"https://vm.tiktok.com/{url}"
        mediafiles.append(urlParse(url))
    if len(ogmsg.attachments) > 0:
        for item in ogmsg.attachments:
            if 'hevc' in item.url.lower() or 'heic' in item.url.lower() or 'mp4' in item.url.lower():
                mediafiles.append(urlParse(item.url))

    if len(mediafiles) > 0:
        embedmsg = await send_embed(ogmsg, mediafiles)
        await media_download(mediafiles)
        await media_convert(mediafiles)
        await send_files(mediafiles, embedmsg)
        cleanup(mediafiles)


async def send_embed(ogmsg, mediafiles: list[mediaFile]):
    CHANNEL = ogmsg.channel
    if ogmsg.author.nick:
        embedVar = discord.Embed(title='Message:', description=ogmsg.content, color=0xFF8800)
    else:
        embedVar = discord.Embed(title='Message:', description=ogmsg.content, color=0xFF8800)
    embedVar.set_author(name=ogmsg.author.name, icon_url=ogmsg.author.avatar)
    embedVar.set_footer(text="File processing is in progress",
                        icon_url="https://cdn.discordapp.com/avatars/1006542721990807592/b377f09c6a20f90d9d8378e07fa13682.png?size=1024")
    fileList = ""
    for file in mediafiles:
        fileList += f'\n{file.fileName}'
    embedVar.add_field(name='Attachments:', value=fileList, inline=False)
    message = await CHANNEL.send(embed=embedVar, files=None, reference=ogmsg)
    await ogmsg.delete()
    return message


def urlParse(url):
    mediafile = mediaFile()
    mediafile.url = url
    urlparts_slash = url.split('/')
    mediafile.fileName = urlparts_slash[len(urlparts_slash) - 1].lower()
    if mediafile.fileName == "":
        mediafile.fileName = urlparts_slash[len(urlparts_slash) - 2].lower()
    if "tiktok" in url:
        mediafile.type = "tiktok"
        mediafile.fileName += ".mp4"
    if "discordapp" in url:
        mediafile.type = "discord"
    mediafile.convertedFile = mediafile.fileName
    return mediafile


async def media_download(mediafiles: list[mediaFile]):
    for item in mediafiles:
        if item.type == "tiktok":
            url = await tiktok_download(item.url)
        else:
            url = item.url
        open(item.fileName, "wb").write(requests.get(url).content)


async def tiktok_download(url: str):
    # resp = urllib3.PoolManager(ca_certs=certifi.where()).request("GET", url,  retries=10)

    resp = urllib3.PoolManager(ca_certs=certifi.where()).urlopen(method="GET", url=url)

    data = resp.data.decode('utf-8')
    try:
        data = data.split("playAddr")[1]
        data = data.split("?")[0][3:]
        data = data.replace("u002F", "")
        data = data.replace("\\", "/")
        data = data.replace("//", "/")
        data = data.replace("https:/" , "https://")
        print(data)
        return data
    except:
        print(data)
        raise Exception(f"Response error on {url}\nResponse:\n{data}")


async def send_files(mediafiles: list[mediaFile], message):
    files_to_send: list[discord.File] = []
    embedVar = message.embeds[0]
    for item in mediafiles:
        files_to_send.append(discord.File(item.convertedFile))
    embedVar.set_footer(text="", icon_url="")
    if len(files_to_send) > 0:
        await message.channel.send(embed=embedVar, files=files_to_send, reference=message)
        await message.delete()


def cleanup(mediafiles: list[mediaFile]):
    for item in mediafiles:
        if os.path.isfile(item.fileName):
            os.remove(item.fileName)
        if os.path.isfile(item.convertedFile):
            os.remove(item.convertedFile)
    mediafiles.clear()


async def media_convert(mediafiles: list[mediaFile]):
    for item in mediafiles:
        if 'heic' in item.fileName:
            item.convertedFile = await imageConvert(item.fileName)
        else:
            item.convertedFile = item.fileName
        if 'hevc' in item.fileName or 'mp4' in item.fileName or 'webm' in item.fileName or 'mov' in item.fileName:
            item.convertedFile = await videoConvert(item.fileName)
        else:
            item.convertedFile = item.fileName


async def imageConvert(path):
    cpath = f'{path.split(".")[0]}_c.jpg'
    image = Image.open(path)
    image.save(cpath, "jpeg")
    return cpath


async def videoConvert(path):
    cpath = f'{path.split(".")[0]}_c.webm'
    clip = moviepy.VideoFileClip(path)
    codec = hevc_check(path).lower()
    clipsize = fileSizeLimit / os.path.getsize(path) - 0.01
    if codec == 'hevc' or codec == 'av1' or clipsize <= 1:
        clip.write_videofile(cpath, fps=30, threads=4, codec='libvpx')
        clipsize = fileSizeLimit / os.path.getsize(cpath) - 0.01
        if clipsize <= 1:
            clip.resize(clipsize)
            clip.write_videofile(cpath, threads=4, codec='libvpx')
    else:
        cpath = path
        clip.close()
    return cpath


def hevc_check(ogfilename):
    info = MediaInfo.parse(ogfilename)
    codec = ""
    for track in info.tracks:
        if track.track_type == "Video":
            codec = "{t.format}".format(t=track)
    return codec


try:
    print("CapConvert initialization")
    client.run(TOKEN)
except:
    print('Error: The connection to the server cannot be established, please check your Token!')
