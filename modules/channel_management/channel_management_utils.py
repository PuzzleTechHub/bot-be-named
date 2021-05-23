import constants
import discord
from utils import discord_utils


async def createchannelgeneric(guild, category, name):
    """Command to create channel in same category with given name
    Arguments:
        - guild (discord.Guild): the guild the channel is being created in
        - category (discord.CategoryChannel): the category the channel is being created in
        - name (str): the name for the channel"""
    # log command in console
    print("Received createchannelgeneric")
    embed = discord_utils.create_embed()

    # Category channel limit
    if len(category.channels) >= 50:
        embed.add_field(name=f"{constants.FAILED}!",
                        value=f"Category `{category.name}` is already full, max limit is 50 channels.")
        return None, embed

    try:
        # create channel
        channel = await guild.create_text_channel(name, category=category)
    except discord.Forbidden:
        embed.add_field(name=f"{constants.FAILED}!",
                        value=f"Forbidden! Have you checked if the bot has the required permisisons?")
        return None, embed

    embed.add_field(name=f"{constants.SUCCESS}",
                    value=f"Created channel {channel.mention} in `{channel.category.name}`!")
    return channel, embed
