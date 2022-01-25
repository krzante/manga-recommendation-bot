import os
from os import getenv
from sys import prefix
from dotenv import load_dotenv
import discord
from discord.ext import tasks, commands
import json

import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import association_rules

load_dotenv()

fpgrowth_dfvar = pd.read_csv('./data/manga_fpgrowth.csv')

# Load prefixes from json file
def get_prefix(client, message):
    with open('prefixes.json', 'r') as f:
        prefix = json.load(f)
    # print (str(message.guild.id))
    # print (prefix)
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
    # global fpgrowth_dfvar = pd.read_csv('./data/manga_fpgrowth.csv')
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
    # prefixvar = thredd_bot.command_prefix
    embed_var = discord.Embed(
        colour = discord.Colour.dark_blue()
    )
    embed_var.set_author(name='Crypto Bot Commands')
    embed_var.add_field(name=':exclamation:  Change Bot Prefix', value='> `changeprefix <NEW PREFIX>`\n> Set the coin to fiat conversion currency. Needs Administrator role.\n \
        > aliases: `changeprefix`, `cp`', inline=False)
    # \u200B is empty https://stackoverflow.com/questions/50373020/line-separator-break-in-discord-embded
    # embed_var.add_field(name='\u200B', value='\u200B', inline=False)
    embed_var.add_field(name='\u200B', value='**----- RECOMMENDATION TYPES ----------------------------**', inline=False)
    embed_var.add_field(name=':one:  Antecedent Support Recommendations', value='> `recbyantedentsup <MANGA>`\n> Recommend mangas based on the initial manga input via antecedent support.\n \
        > aliases: `recbyantecedentsup`, `rbas`, `ras`, `r1`', inline=False)
    embed_var.add_field(name=':two:  Confidence Recommendations', value='> `recbyconfidence <MANGA>`\n> Recommend mangas based on the initial manga input via confidence.\n \
        > aliases: `recbyconfidence`, `rbcf`, `rcf`, `r2`', inline=False)
    embed_var.add_field(name=':three:  Consequent Support Recommendations', value='> `recbyconsequentsup <MANGA>`\n> Recommend mangas based on the initial manga input via consequent support.\n \
        > aliases: `recbyconsequentsup`, `rbcs`, `rcs`, `r3`', inline=False)
    embed_var.add_field(name=':four:  Conviction Recommendations', value='> `recbyconviction <MANGA>`\n> Recommend mangas based on the initial manga input via conviction.\n \
        > aliases: `recbyconviction`, `rbcv`, `rcv`, `r4`', inline=False)
    embed_var.add_field(name=':five:  Leverage Recommendations', value='> `recbyleverage <MANGA>`\n> Recommend mangas based on the initial manga input via leverage.\n \
        > aliases: `recbyleverage`, `rble`, `rle`, `r5`', inline=False)
    embed_var.add_field(name=':six:  Lift Recommendations', value='> `recbylift <MANGA>`\n> Recommend mangas based on the initial manga input via lift.\n \
        > aliases: `recbylift`, `rblift`, `rlift`, `r6`', inline=False)
    embed_var.add_field(name=':seven:  Support Recommendations', value='> `recbysupport <MANGA>`\n> Recommend mangas based on the initial manga input via support.\n \
        > aliases: `recbysupport`, `rbs`, `rs`, `r7`', inline=False)

    await ctx.channel.send(embed=embed_var)


# Simple function to send the recommendations
# Needs to be reworked into embeds
async def send_manga_rec(ctx, results_arg, via_arg):
    antecedent = results_arg[1][1]
    concequents = results_arg[:,2]

    numbers=[':one:', ':two:', ':three:', ':four:', ':five:', 
        ':six:',':seven:', ':eight:', ':nine:', ':keycap_ten:'
    ]

    # Test EMbed
    embed_var = discord.Embed(
        colour = discord.Colour.dark_blue()
    )
    embed_var.set_author(name=antecedent + " recommendations via: " + via_arg)
    i = 0
    for manga in results_arg:
        namevar = numbers[i] +'  '+ manga[2]
        valuevar = '[Checkout ' + manga[2] + '](http://myanimelist.net/manga.php?cat=manga&q=' + manga[2].replace(" ","%20") + ')'
        embed_var.add_field(name=namevar, value=valuevar, inline=False)
        i += 1
    await ctx.channel.send(embed=embed_var)


# Function to send a manga not found message
# Will be converted to an embed
async def send_manga_not_found(ctx):
    await ctx.channel.send("Manga Not In Database")


# This is the function that the rec commands will initially call.
async def setup_recommendations(ctx, manga_arg, method_arg):
    manga_arg = manga_arg.lower().title()
    # resultsvar = get_recommendations(ctx, manga_arg, method_arg) # fpgrowth_dfvar[fpgrowth_dfvar["antecedents"].apply(lambda x: manga_arg in str(x))].sort_values(ascending=False,by='support').head(10)
    await get_recommendations(ctx, manga_arg, method_arg)
    # await send_manga_rec(ctx, resultsvar, method_arg)
    # if resultsvar != False:
    #     await send_manga_rec(ctx, resultsvar, method_arg)
    # else:
    #     await send_manga_not_found(ctx)


# Function to get the list of mangas to recommend based on the manga_arg
async def get_recommendations(ctx, manga_arg, recommend_by_arg):
    global fpgrowth_dfvar
    resultsvar = fpgrowth_dfvar[fpgrowth_dfvar["antecedents"].apply(lambda x: manga_arg in str(x))].sort_values(ascending=False,by=recommend_by_arg).head(10).reset_index()
    resultsvar = resultsvar.to_numpy()
    # print(resultsvar)
    if not resultsvar.size == 0:
        await send_manga_rec(ctx, resultsvar, recommend_by_arg)
        # return resultsvar
    else:
        print("404")
        await send_manga_not_found(ctx)
        # return False

    # return fpgrowth_dfvar[fpgrowth_dfvar["antecedents"].apply(lambda x: manga_arg in str(x))].sort_values(ascending=False,by=recommend_by_arg).head(10).reset_index()


# Recommend via antecedent support in the FPGrowth
@thredd_bot.command(name='recbyantecedentsup', aliases=['rbas', 'ras', 'r1'])
async def recommend_by_lift_command(ctx, *, manga_arg):
    await setup_recommendations(ctx, manga_arg, 'antecedent support')


# Recommend via Confidence in the FPGrowth
@thredd_bot.command(name='recbyconfidence', aliases=['rbcf', 'rcf', 'r2'])
async def recommend_by_lift_command(ctx, *, manga_arg):
    await setup_recommendations(ctx, manga_arg, 'confidence')


# Recommend via consequent support in the FPGrowth
@thredd_bot.command(name='recbyconsequentsup', aliases=['rbcs', 'rcs', 'r3'])
async def recommend_by_lift_command(ctx, *, manga_arg):
    await setup_recommendations(ctx, manga_arg, 'consequent support')


# Recommend via conviction in the FPGrowth
@thredd_bot.command(name='recbyconviction', aliases=['rbcv', 'rcv', 'r4'])
async def recommend_by_lift_command(ctx, *, manga_arg):
    await setup_recommendations(ctx, manga_arg, 'conviction')


# Recommend via leverage in the FPGrowth
@thredd_bot.command(name='recbyleverage', aliases=['rble', 'rle', 'r5'])
async def recommend_by_lift_command(ctx, *, manga_arg):
    await setup_recommendations(ctx, manga_arg, 'leverage')


# Recommend via Lift Column in the FPGrowth
@thredd_bot.command(name='recbylift', aliases=['rbli', 'rli', 'r6'])
async def recommend_by_lift_command(ctx, *, manga_arg):
    await setup_recommendations(ctx, manga_arg, 'lift')


# Recommend via Support Column in the FPGrowth
@thredd_bot.command(name='recbysupport', aliases=['rbs', 'rs', 'r7'])
async def recommend_by_support_command(ctx, *, manga_arg):
    await setup_recommendations(ctx, manga_arg, 'support')


thredd_bot.run(getenv("BOT_TOKEN"))  # Running/Activating the Bot