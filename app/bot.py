import os
import discord
from discord import guild_only
import logging
from dotenv import load_dotenv
import sheet
from sheet import Point

load_dotenv() # load all the variables from the env file

# Configure logging
LOG_LEVEL = logging.INFO
logger = logging.getLogger('discord')

log_format = '[%(asctime)s] [%(levelname)s] - %(message)s'
logging.basicConfig(level=LOG_LEVEL, format=log_format) # change this to come from .env

# Configure intents
intents = discord.Intents.default()
intents.members = True

bot = discord.Bot(intents=intents, debug_guilds=[71774361593315328])

# class ParticipationChannelOnly(discord.ext.commands.CheckFailure):
#     pass

# @bot.check
# async def participation_only(ctx):
#     if ctx.channel != participation:
#         raise ParticipationChannelOnly('This command can only be run in the #participation channel')
#     return True

# @participation_only.error
# async def participation_only_error(ctx, error):
#     if isinstance(error, ParticipationChannelOnly):
#         await ctx.send(error)

EVENTNAME_LOOKUP = {
    'pvp': 'PvP',
    'fractals': 'Fractals',
    'Guild Events': 'Guild Events'
}

### New Functions
# returns list[discord.VoiceChannel] that contain the channel_name search term
def get_matched_channels(ctx: discord.context, channel_name: str):
    channels = ctx.guild.voice_channels
    return [c for c in channels if channel_name.lower() in c.name.lower()]

# returns list[discord.Member] currently in provided voice channels
def get_channel_members(channels: list[discord.VoiceChannel]):
    members = []
    for channel in channels:
        members.extend(channel.members)
    logger.info(members)
    return members

# builds list[str] of preferred user name from list[discord.Member]
def build_name_list(member_list: list[discord.Member]):
    names = []
    for m in member_list:
        name = m.nick if m.nick != None else m.name
        names.append(name)
    return names

# return discord.Member from the provided list[discord.Member] whose name/nick contains the search term
def get_member_named_like(user: str, members: list[discord.Member]):
    # allow this to return multiple users and figure out how to handle that
    user = user.lower()
    for member in members:
        if(user in member.name.lower() or (member.nick != None and user in member.nick.lower())):
            # logger.info(member)
            return member
    return None

# returns an object with a list of found and missing users
def find_members(ctx: discord.context, members: list[str]):
    memberObj  = {
        "found": [],
        "missing": []
    }
    print('memberObj:', memberObj)
    server_members = None
    # how to handle if users aren't found?
    for member in members:
        # direct member lookup (either name or nick)
        m = ctx.guild.get_member_named(member)
        if m:
            logger.info(f'direct match ({member}): {m}')
            memberObj['found'].append(m)
        else:
            # attempt fuzzy search for user (either name or nick)
            if server_members is None:
                server_members = ctx.guild.members
            user = get_member_named_like(member, server_members)
            logger.info(f'fuzzy match ({member}): {user}')
            if user:
                memberObj['found'].append(user)
            else:
                memberObj['missing'].append(member)

        logger.info(memberObj['found'])
        logger.info(memberObj['missing'])
    return memberObj

# handle response for event commands
async def build_event_response(event_name: str, members: list[discord.Member]):
    if members:
        msg = "{} participation recorded\n{}".format(EVENTNAME_LOOKUP[event_name], '\n'.join(build_name_list(members)))
        return msg
    else:
        return "No members found in the requested channels."

### Old Functions
def send_members_reply(ctx: discord.context, event_msg: str, members: list[discord.Member]):
    return None

@bot.event
async def on_ready():
    logger.info(f"{bot.user} is ready and online!")

@bot.slash_command(name = 'fractals')
async def fractals(ctx: discord.context):
    await event(ctx, channel = 'fractals')

@bot.slash_command(name = 'pvp')
async def pvp(ctx: discord.context):
    await event(ctx, channel = 'pvp')

@bot.slash_command(name = 'event')
async def event(ctx: discord.context, *, channel:str = 'Guild Events'):
    # get channels
    logger.info("channel query:", channel)
    channels = get_matched_channels(ctx, channel)
    logger.info("channels:", *channels, sep="\n")

    # get members from these channels
    members = get_channel_members(channels)

    # update spreadsheet

    # event response handler
    msg = build_event_response(channel, members)
    await ctx.respond(msg)

@bot.slash_command(name = 'participation')
async def participation(ctx: discord.context, members):
    members = members.split(',')
    members = [m.strip() for m in members]
    member_search = find_members(ctx, members)

    updateParticipation(member_search['found'], Point.EVENT)

    msg = ""
    if len(member_search['found']) > 0:
        msg += "+++ Participation recorded for: +++\n"+"\n".join(build_name_list(member_search['found']))+"\n\n"
    if len(member_search['missing']) > 0:
        msg += "--- Could not find user matches for: ---\n"+'\n'.join((member_search['missing']))
    await ctx.respond(msg)

@bot.slash_command(name = 'lead')
async def lead(ctx: discord.context, *, members: str):
    members = members.split(',')
    members = [m.strip() for m in members]
    member_search = find_members(ctx, members)

    updateParticipation(member_search['found'], Point.LEAD)

    msg = ""
    if len(member_search['found']) > 0:
        msg += "+++ Leadership recorded for: +++\n"+"\n".join(build_name_list(member_search['found']))+"\n\n"
    if len(member_search['missing']) > 0:
        msg += "--- Could not find user matches for: ---\n"+'\n'.join((member_search['missing']))
    await ctx.respond(msg)


def updateParticipation(members: list[discord.Member], point: Point):
    for member in members:
        print("member:",member)
        sheet.update(member.id, point)

@bot.slash_command(name = 'test')
async def test(ctx: discord.context):
    logger.info(ctx.channel)
    logger.info(ctx.channel_id)
    members = ctx.guild.members
    # text_channel = ctx.guild.get_channel(71774361593315328)
    # members = ctx.guild.fetch_members()
    # members = await ctx.guild.query_members(query=user)
    logger.info(members)
    logger.info(len(members))

    print(ctx)

    await ctx.respond(build_name_list(members))

bot.run(os.getenv('DISCORD_TOKEN')) # run the bot with the token