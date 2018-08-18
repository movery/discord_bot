import asyncio
import discord
import youtube_dl
from time import sleep
from discord.ext import commands

TOKEN  = 'REDACTED'

# Client Setup Stuff
client = commands.Bot(command_prefix='!')

client.remove_command('help')
@client.command(pass_context = True)
async def help(ctx):
    author = ctx.message.author

    embed = discord.Embed(
        colour = discord.Colour.orange()
    )

    embed.set_author(name='Help Menu')
    embed.add_field(name='!join',   value='Joins your current channel', inline=False)
    embed.add_field(name='!leave',  value='Leaves your current channel', inline=False)
    embed.add_field(name='!play',   value='Attempts to load a video and play it. If a video is playing already, adds this video to a queue', inline=False)
    embed.add_field(name='!pause',  value='Pauses currently playing video', inline=False)
    embed.add_field(name='!resume', value='Resumes a paused video', inline=False)
    embed.add_field(name='!skip',   value='Stops playing the currently playing video, plays the next one in the queue', inline=False)
    embed.add_field(name='!clear',  value='Cleares the queue and stops the currently playing song', inline=False)
    embed.add_field(name='!reload', value='Leaves and Joins your current channel, reseting defaults in the process', inline=False)
    embed.add_field(name='!horn',   value='MLG Horn', inline=False)
    embed.add_field(name='!myman',  value='Do I need to explain this one?', inline=False)

    await client.send_message(author, embed=embed)

# Sounds
horn_url = 'https://www.youtube.com/watch?v=3Wlqj2pl3Zk'
myman_url = 'https://www.youtube.com/watch?v=KpcmfjFN8OI'

# Server Id => Active Player
currently_playing = {}

# Server Id => List of Players
playlist = {}

# Context (For non-command related events)
context = None

# Timer Thread for Airhorns (Non command event)
# async def timer_thread():
#     from datetime import datetime

#     next_hour = (datetime.now().hour + 1) % 24
#     while True:
#         await asyncio.sleep(2)
#         if context:
#             curr_hour = datetime.now().hour
#             if curr_hour == next_hour:
#                 await _play_sound_effect(context, horn_url)
#                 next_hour = (next_hour + 1) % 24

@client.event
async def on_ready():
    client.loop.create_task(timer_thread())
    print('Bot Online')

async def _join(ctx):
    global context, currently_playing

    if context: await _leave(context)
    
    # Join
    channel = ctx.message.author.voice.voice_channel
    await client.join_voice_channel(channel)

    currently_playing[ctx.message.server.id] = None
    playlist[ctx.message.server.id] = []
    
    context = ctx
    
@client.command(pass_context=True)
async def join(ctx):
    await _join(ctx)

async def _leave(ctx):
    global context, currently_playing, playlist
    
    # Leave
    server       = ctx.message.server
    voice_client = client.voice_client_in(server)
    await voice_client.disconnect()

    context = None

    if currently_playing[ctx.message.server.id]:
        playlist[ctx.message.server.id] = []
        currently_playing[ctx.message.server.id].stop()
        currently_playing[ctx.message.server.id] = None

@client.command(pass_context=True)
async def leave(ctx):
    await _leave(ctx)

def _play_next(server_id):
    global currently_playing, playlist

    if playlist[server_id]:
        currently_playing[server_id] = playlist[server_id].pop(0)
        currently_playing[server_id].start()
    else:
        currently_playing[server_id] = None

async def _play(ctx, url):
    global currently_playing, playlist

    server       = ctx.message.server
    voice_client = client.voice_client_in(server)

    try:
        player = await voice_client.create_ytdl_player(url, after=lambda: _play_next(server.id))
    except:
        await client.send_message(ctx.message.channel, 'Could not load video for whatever reason')
        return
    
    if not currently_playing[server.id]:
        currently_playing[server.id] = player
        currently_playing[server.id].start()
    else:
        playlist[server.id].append(player)
        
@client.command(pass_context=True)
async def play(ctx, url):
    await _play(ctx, url)

playing_sound_effect = False
def _done_sound_effect(ctx):
    global playing_sound_effect

    playing_sound_effect = False
    _resume(ctx)
    
async def _play_sound_effect(ctx, url):
    global playing_sound_effect

    if playing_sound_effect: return

    playing_sound_effect = True

    server       = ctx.message.server
    voice_client = client.voice_client_in(server)
    player = await voice_client.create_ytdl_player(url, after=lambda: _done_sound_effect(ctx))

    if currently_playing[server.id]:
        _pause(ctx)
        player.start()
    else:
        player.start()
    
@client.command(pass_context=True)
async def horn(ctx):
    await _play_sound_effect(ctx, horn_url)
    
@client.command(pass_context=True)
async def myman(ctx):
    await _play_sound_effect(ctx, myman_url)

def _pause(ctx):
    currently_playing[ctx.message.server.id].pause()
    
@client.command(pass_context=True)
async def pause(ctx):
    _pause(ctx)

def _resume(ctx):
    currently_playing[ctx.message.server.id].resume()
    
@client.command(pass_context=True)
async def resume(ctx):
    _resume(ctx)
    
@client.command(pass_context=True)
async def skip(ctx):
    currently_playing[ctx.message.server.id].stop()

@client.command(pass_context=True)
async def clear(ctx):
    global currently_playing, playlist

    if currently_playing[ctx.message.server.id]:
        playlist[ctx.message.server.id] = []
        currently_playing[ctx.message.server.id].stop()
        currently_playing[ctx.message.server.id] = None

@client.command(pass_context=True)
async def reload(ctx):
    await _leave(ctx)
    await _join(ctx)
        
def main():
    client.run(TOKEN)

main()
