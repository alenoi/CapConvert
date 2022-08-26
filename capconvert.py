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
                # ext = item.url.split('.')[len(item.url.split('.')) - 1].lower()
                if 'heic' in item.url.lower():
                    await heic2jpg(files_to_send, files_to_delete, item)
                elif 'hevc' in item.url.lower() or 'mp4' in item.url.lower():
                    await hevc2mp4(files_to_send, files_to_delete, item)

    if len(files_to_send) > 0:
        try:
            await send_files(files_to_send, message)
        except Exception as e:
            print(e)
    if len(files_to_delete) > 0:
        for item in files_to_delete:
            os.remove(item)


async def tiktok_download(files_to_send, files_to_delete, message):
    url = message.content.split('/')[3]
    ogfilename = f'{url}.webm'
    filename = f'{url}_c.webm'
    os.system(f'python3.10 -m tiktok_downloader --url https://vt.tiktok.com/{url} --tiktok --save {ogfilename}')
    clip = moviepy.VideoFileClip(ogfilename)
    clipsize = 8000000 / os.path.getsize(ogfilename)
    if clipsize <= 1:
        # clip = clip.resize(clipsize - 0.01)
        clip.write_videofile(f'{filename}', threads=4, codec='libvpx')
        files_to_send.append(discord.File(f'{filename}'))
        files_to_delete.append(filename)
    else:
        files_to_send.append(discord.File(ogfilename))
    files_to_delete.append(ogfilename)


async def send_files(files_to_send, message):
    CHANNEL = client.get_channel(message.channel.id)
    if message.author.nick:
        embedVar = discord.Embed(title=f"", description=f'{message.content}', color=RGBtoColor('FF8800'))
    else:
        embedVar = discord.Embed(title=f"", description=f'{message.content}', color=RGBtoColor('FF8800'))
    embedVar.set_author(name=message.author.name, icon_url=message.author.avatar)
    await CHANNEL.send(embed=embedVar,
                       files=files_to_send,
                       reference=message
                       )
    await message.delete()


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


def RGBtoColor(xrgb):
    if len(xrgb) < 6:
        xrgb = xrgb + "000000"
    return discord.Color.from_rgb(int(xrgb[0:2], 16),
                                  int(xrgb[2:4], 16),
                                  int(xrgb[4:6], 16))


if TOKEN != "":
    try:
        client.run(TOKEN)
    except:
        print('Error: The connection to the server cannot be established, please check your serverID and Token!')
else:
    print('Error: There is no valid serverID or Token!')
