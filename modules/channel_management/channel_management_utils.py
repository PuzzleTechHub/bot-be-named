import constants
import discord
from discord.ext import commands
from utils import discord_utils

async def createchannelgeneric(ctx, name: str = ""):
    """Command to create channel in same category with given name"""
    # log command in console
    print("Received createchannelgeneric")
    embed = discord_utils.create_embed()

    # get guild and category
    guild = ctx.message.guild
    category = ctx.channel.category

    # no argument passed
    if len(name) <= 0:
        embed.add_field(name=f"{constants.FAILED}!", value=f"You must specify a channel name!")
        # reply to user
        await ctx.send(embed=embed)
        return None

    if len(category.channels)>=50:
        embed.add_field(name=f"{constants.FAILED}!", value=f"Category `{category.name}` is already full, max limit is 50 channels.")
        # reply to user
        await ctx.send(embed=embed)
        return None

    try:
        # create channel
        channel = await guild.create_text_channel(name, category=category)
    except discord.Forbidden:
        embed.add_field(name=f"{constants.FAILED}!", value=f"Forbidden! Have you checked if the bot has the required permisisons?")
        # reply to user
        await ctx.send(embed=embed)
        return None

    return channel
