import os
from os import getenv
from dotenv import load_dotenv
import discord
from discord.ext import tasks, commands
import json

load_dotenv()


# Load prefixes from json file
def get_prefix(client, message):
    with open('prefixes.json', 'r') as f:
        prefix = json.load(f)
    print (str(message.guild.id))
    print (prefix)
    return prefix[str(message.guild.id)]


# Function to return a single field embed
def get_embed(name_arg, value_arg, inline_arg):
    embed = discord.Embed(
            colour = discord.Colour.dark_blue()
    )
    embed.add_field(name=name_arg, value=value_arg, inline=inline_arg)
    return embed


# || Start of the bot commands using the bots commands framework ||
thredd_bot = commands.Bot(command_prefix = get_prefix) # Instancing a bot using the commands framework
thredd_bot.remove_command('help') # Removed the dafault help command since we will use our custom embeded help command


@thredd_bot.event
async def on_guild_join(guild):
    with open('prefixes.json', 'r') as f:
        prefix = json.load(f)

    prefix[str(guild.id)] = 'tr!'

    with open('prefixes.json', 'w') as f:
        json.dump(prefix,f)


@thredd_bot.event   # Take note that the "thredd" variable is the actual bot
async def on_ready():
    await thredd_bot.change_presence(status=discord.Status.online, \
                        activity = discord.Game(f'tr!help | Learn more' ))
    print("bot has logged in")  # Print to the console when the bot is online


@thredd_bot.command(name='changeprefix', aliases=['cp'])
@commands.has_permissions(administrator = True)
async def change_prefix_command(ctx, prefix_arg):
    with open('prefixes.json', 'r') as f:
        prefix_json_var = json.load(f)

    prefix_json_var[str(ctx.guild.id)] = prefix_arg

    with open('prefixes.json', 'w') as f:
        json.dump(prefix_json_var,f)
    
    await ctx.channel.send(embed=get_embed(\
            'PREFIX CHANGED',\
            f'Prefix was changed to {prefix_arg}', \
            False))


@thredd_bot.command(name='help', aliases=['h'])
async def help_command(ctx):
    embed_var = discord.Embed(
        colour = discord.Colour.dark_blue()
    )
    embed_var.set_author(name='Crypto Bot Commands')
    embed_var.add_field(name='changeprefix <NEW PREFIX>', value='> Set the coin to fiat conversion currency. Needs Administrator role.\n \
        > aliases: `changeprefix`, `cp`', inline=False)
    embed_var.add_field(name='recommend <INITAL MANGA>', value='> Recommend mangas based on the initial manga input.\n \
        > aliases: `recommend`, `rec`, `r`', inline=False)

    await ctx.channel.send(embed=embed_var)


@thredd_bot.command(name='hello')
async def hello_command(ctx):
    await ctx.channel.send(embed=get_embed(\
            'HELLO',\
            f'Good day to recommend mangas', \
            False))


thredd_bot.run(getenv("BOT_TOKEN"))  # Running/Activating the Bot