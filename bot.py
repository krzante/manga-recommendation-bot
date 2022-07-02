import os
from os import getenv
from sys import prefix
from dotenv import load_dotenv
import discord
from discord.ext import tasks, commands
import json
from matplotlib.pyplot import text

import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import association_rules

load_dotenv()


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

def get_manga_db():
    with open('./data/manga_db.json', 'r') as f:
        dbvar = json.load(f)
    return dbvar


rec_types_listvar = ['confidence', 'conviction', 'leverage', 'lift']
fpgrowth_dfvar = pd.read_csv('./data/manga_fpgrowth.csv')
manga_dbvar = get_manga_db()


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
    print("Bot has logged in")  # Print to the console when the bot is online


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
    embed_var.set_author(name='Thredd Bot Commands')
    embed_var.add_field(name=':exclamation:  Change Bot Prefix', value='> `changeprefix <NEW PREFIX>`\n> Change the bot\'s prefix. Needs Administrator role.\n \
        > aliases: `changeprefix`, `cp`\n> \n> `Sample:`\n> tr!changeprefix !', inline=False)
    # \u200B is empty https://stackoverflow.com/questions/50373020/line-separator-break-in-discord-embded
    embed_var.add_field(name=':one:  Recommend With Full Manga Title', value='> `recbyfull "<full manga title>" <recommendation type>`\n> aliases: `rf`, `rfull`, `r1`.\n> \n \
        > `Samples:`\n> tr!recbyfull "Slam Dunk" lift\n> tr!r1 "nisekoi" leverage', inline=False)
    embed_var.add_field(name=':two:  Recommend With Partial Manga Title', value='> `recbypartial "<partial manga title>" <recommendation type>`\n> aliases: `rp`, `rpartial`, `r2`.\n> \n \
        > `Samples:`\n> tr!recbypartial "Slam" lift\n> tr!r2 "nise" leverage', inline=False)
    embed_var.add_field(name='**----- RECOMMENDATION TYPES ----------------------------**', value='> `Confidence`\n> `Conviction`\n> `Leverage`\n> `Lift`\n \
        > [Read more](https://michael.hahsler.net/research/recommender/associationrules.html)', inline=False)

    
    embed_var.set_footer(text ='AI Project by Getigan, Mesina, Yumang & Zante', icon_url='https://www.pikpng.com/pngl/b/28-287145_dogok-discord-emoji-ok-hand-discord-emote-clipart.png')

    await ctx.channel.send(embed=embed_var)


# Simple function to send the recommendations
# Needs to be reworked into embeds
async def send_manga_rec(ctx, results_arg, via_arg):
    antecedent = results_arg[0][0]
    # concequents = results_arg[:,2]

    # Test EMbed
    embed_var = discord.Embed(
        colour = discord.Colour.dark_blue(),
    )
    
    # Base manga
    embed_var.add_field(name=':blue_book:  ' + str(antecedent) , \
        value='> `Genres`: ' + str(manga_dbvar[antecedent]['genre']) + '\n \
            > `Synopsis`: ' + str(manga_dbvar[antecedent]['synopsis'][:150]) + \
            ' [...read more](https://myanimelist.net/manga/' + str(manga_dbvar[antecedent]['id']) + ')'
    )
    embed_var.add_field(name='\u200B', value='**----- RECOMMENDATIONS VIA ' + via_arg.upper() + '----------------------------**', inline=False)

    i = 0
    for manga in results_arg:
        if i >= 10:
            break
        namevar = ':arrow_right:  ' + str(manga[1])  #numbers[i] +'  '+ manga[2]
        valuevar = '> `Genres`: ' + str(manga_dbvar[manga[1]]['genre']) +'\n\
            > `Synopsis`: ' + str(manga_dbvar[manga[1]]['synopsis'][:150]) + \
            ' [...read more](https://myanimelist.net/manga/' + str(manga_dbvar[manga[1]]['id']) + ')'
        embed_var.add_field(name=namevar, value=valuevar, inline=False)
        i += 1
    embed_var.set_footer(text ='AI Project by Getigan, Mesina, Yumang & Zante', icon_url='https://www.pikpng.com/pngl/b/28-287145_dogok-discord-emoji-ok-hand-discord-emote-clipart.png')
    await ctx.channel.send(embed=embed_var)


# Function to send a manga not found message
# Will be converted to an embed
async def send_manga_not_found(ctx):
    await ctx.channel.send("Manga Not In Database")


# This is the function that the rec commands will initially call.
async def setup_recommendations(ctx, manga_arg, method_arg, full_title_arg):
    manga_arg = manga_arg.lower() #.title()
    await get_recommendations(ctx, manga_arg, method_arg, full_title_arg)


# Function to get the list of mangas to recommend based on the manga_arg
async def get_recommendations(ctx, manga_arg, recommend_by_arg, full_title_arg):
    global fpgrowth_dfvar
    # print(manga_arg)
    # fpgrowth_dfvar[fpgrowth_dfvar["antecedents"].apply(lambda x: manga_arg in str(x))].groupby(['antecedents', 'consequents'])[['lift']].max().sort_values(ascending=False,by=recommend_by_arg).head(10).reset_index()
    # fpgrowth_dfvar[fpgrowth_dfvar["antecedents"].apply(lambda x: manga_arg in str(x))].sort_values(ascending=False,by=recommend_by_arg).head(10).reset_index()
    resultsvar = fpgrowth_dfvar[fpgrowth_dfvar["antecedents"].str.lower().apply(lambda x: manga_arg in str(x))].groupby(['antecedents', 'consequents'])[[recommend_by_arg]].max().sort_values(ascending=False,by=recommend_by_arg).reset_index()
    
    if full_title_arg:
        resultsvar = resultsvar.loc[resultsvar['antecedents'].str.lower() == manga_arg]
    
    resultsvar = resultsvar.to_numpy()

    if not resultsvar.size == 0:
        await send_manga_rec(ctx, resultsvar, recommend_by_arg)
    else:
        print("404")
        await send_manga_not_found(ctx)


# Function to check if the user's input contains more than 2 arguments
def check_args_num(args):
    if len(args) == 2:
        if args[1] in rec_types_listvar:
            return True
    return False



# Recommend via Confidence in the FPGrowth
@thredd_bot.command(name='recbyfull', aliases=['rf', 'rfull', 'r1'])
async def recommend_by_full_command(ctx, *args):
    args = list(args)
    args = [x.lower() for x in args]
    if (check_args_num(args)):
        await get_recommendations(ctx, args[0], args[1], True)
    else:
        await ctx.send('To many/few arguments passed')
    

@thredd_bot.command(name='recbypartial', aliases=['rp', 'rpartial', 'r2'])
async def recommend_by_full_command(ctx, *args):
    args = list(args)
    args = [x.lower() for x in args] # Converting the list to all lowercase https://www.delftstack.com/howto/python/python-lowercase-list/
    if (check_args_num(args)):
        await get_recommendations(ctx, args[0], args[1], False)
    else:
        await ctx.send('To many/few arguments passed')


# Recommend via Support Column in the FPGrowth
@thredd_bot.command(name='hello', aliases=['ello',])
async def hello_command(ctx, *manga_arg):
    await ctx.send('{} arguments: {}'.format(len(manga_arg), ', '.join(manga_arg)))


thredd_bot.run(getenv("BOT_TOKEN"))  # Running/Activating the Bot