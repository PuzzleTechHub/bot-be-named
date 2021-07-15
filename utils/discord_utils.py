import discord
import constants
from typing import List

def create_embed() -> discord.Embed:
    """
    Create an empty discord embed with color.
    :return: (discord.Embed)
    """
    return discord.Embed(color=constants.EMBED_COLOR)


def create_no_argument_embed(arg_name: str ='argument') -> discord.Embed:
    """
    Create an embed which alerts the user they need to supply an argument
    :param arg_name: (str) The type of argument needed (e.g. channel)
    """
    embed = create_embed()
    embed.add_field(name=f'{constants.FAILED}!', value=f"You need to supply a {arg_name}!")
    return embed


def populate_embed(names: list, values: list, inline: bool = False) -> discord.Embed:
    """Populate an embed with a list of names and values"""
    embed = discord.Embed(color=constants.EMBED_COLOR)
    for idx in range(len(names)):
        embed.add_field(name=names[idx],
                        value=values[idx],
                        inline=inline)
    return embed


def find_channel(bot, channels, channel_name):
    channel = discord.utils.get(channels, name=channel_name)

    if channel is None:
        channel_id = int(channel_name.replace('>', '').replace('<#', ''))
        channel = bot.get_channel(channel_id)
    return channel


def category_is_full(category: discord.CategoryChannel) -> bool:
    """Determines whether a category is full (has 50 channels)"""
    return len(category.channels) >= 50


async def createchannelgeneric(guild, category, name) -> discord.TextChannel:
    """Command to create channel in same category with given name
    Arguments:
        - guild (discord.Guild): the guild the channel is being created in
        - category (discord.CategoryChannel): the category the channel is being created in
        - name (str): the name for the channel
    Returns:
        - channel (discord.TextChannel): The created channel, or none if the bot does not have sufficient perms.
    """
    try:
        # create channel
        channel = await guild.create_text_channel(name, category=category)
    except discord.Forbidden:
        return None

    return channel


def split_embed(embed: discord.Embed) -> List[discord.Embed]:
    """Splits embeds that are too long (discord character limit)
    Arguments:
        - embed (discord.Embed)
    Returns
        - embed_list (List[discord.Embed]):
    """
    if embed.title == discord.Embed.Empty:
        embed.title = ""
    CHARACTER_LIMIT = 2000
    embed_list = []
    character_count = len(embed.title) + len(embed.description)
    # If the title + description exceeds the character limit, we must break up the description into smaller parts.
    if character_count > CHARACTER_LIMIT:
        print(f"Title and description are too long with {character_count} characters")
        characters_remaining = character_count
        while characters_remaining > 0:
            embed_list.append(discord.Embed(title=embed.title + " (continued)" if len(embed_list) > 0 else embed.title,
                                            color=embed.color))
            embed_list[-1].description = embed.description[:(CHARACTER_LIMIT - len(embed.title))]
            characters_remaining -= CHARACTER_LIMIT - len(embed.title)
    # If the title + description are small, we can just copy them over
    else:
        embed_list.append(discord.Embed(title=embed.title,
                                        description=embed.description,
                                        color=embed.color))
    character_count = len(embed_list[-1].title) + len(embed_list[-1].description)
    for field in embed.fields:
        character_count += len(field.name) + len(field.value)
        if character_count > CHARACTER_LIMIT:
            print("Character count too long")
            embed_list.append(discord.Embed(title=embed.title + " (continued)",
                                            color=embed.color))
            character_count = len(embed_list[-1].title) + len(field.name) + len(field.value)
        embed_list[-1].add_field(name=field.name,
                                            value=field.value,
                                            inline=field.inline)
    return embed_list
# [X] Description too long
# [] Too many fields
# [] Field too long? (uhhhh)
# [] Combination of description and field