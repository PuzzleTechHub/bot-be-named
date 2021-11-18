import discord
import constants
from modules.solved import solved_constants
from typing import List

def create_embed() -> discord.Embed:
    """
    Create an empty discord embed with color.
    :return: (discord.Embed)
    """
    return discord.Embed(color=constants.EMBED_COLOR,description="")

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

# TODO: I'm going to need to rewriter this at some point...
def split_embed(embed: discord.Embed) -> List[discord.Embed]:
    """Splits embeds that are too long (discord character limit)
    Arguments:
        - embed (discord.Embed)
    Returns
        - embed_list (List[discord.Embed]):
    """
    if embed.title == discord.Embed.Empty:
        embed.title = ""
    EMBED_CHARACTER_LIMIT = 2000
    FIELD_CHARACTER_LIMIT = 1024
    embed_list = []
    character_count = len(embed.title) + len(embed.description)
    # If the title + description exceeds the character limit, we must break up the description into smaller parts.
    if character_count > EMBED_CHARACTER_LIMIT:
        print(f"Title and description are too long with {character_count} characters")
        characters_remaining = character_count
        description = embed.description
        while description != "":
            embed_list.append(discord.Embed(title=embed.title + " (continued)" if len(embed_list) > 0 else embed.title,
                                            color=embed.color))
            # Find the point that is closest to the cutoff but with a space.
            cutoff_point = description[:(EMBED_CHARACTER_LIMIT - len(embed.title))].rfind(' ')
            if cutoff_point == -1:
                cutoff_point = EMBED_CHARACTER_LIMIT - len(embed.title) - 1
            embed_list[-1].description = description[:cutoff_point+1]
            description = description[cutoff_point+1:]
            characters_remaining -= cutoff_point
    # If the title + description are small, we can just copy them over
    else:
        embed_list.append(discord.Embed(title=embed.title,
                                        description=embed.description,
                                        color=embed.color))
    character_count = len(embed_list[-1].title) + len(embed_list[-1].description)

    # Iterate over all the proposed fields in the embed
    for field in embed.fields:
        field_description = field.value
        field_character_count = len(field_description)
        # Cut down the proposed fields to the appropriate size
        while field_character_count > FIELD_CHARACTER_LIMIT:
            # If we can add a full-sized field to the embed, do it
            if character_count + len(field.name) + FIELD_CHARACTER_LIMIT <= EMBED_CHARACTER_LIMIT:
                cutoff_point = field_description[:FIELD_CHARACTER_LIMIT].rfind(' ')
                if cutoff_point == -1:
                    cutoff_point = FIELD_CHARACTER_LIMIT-1
                embed_list[-1].add_field(name=field.name,
                                         value=field_description[:cutoff_point+1],
                                         inline=False)
                field_character_count -= cutoff_point
                field_description = field_description[cutoff_point+1:]
            # If we can't add a full field to the embed, add a chopped field and then create a new embed
            else:
                cutoff_point = field_description[:EMBED_CHARACTER_LIMIT - character_count - len(field.name)].rfind(' ')
                if cutoff_point == -1:
                    cutoff_point = EMBED_CHARACTER_LIMIT - character_count - len(field.name) - 1
                embed_list[-1].add_field(name=field.name,
                                         value=field_description[:cutoff_point+1],
                                         inline=False)
                field_character_count -= cutoff_point
                field_description = field_description[cutoff_point+1:]
                # We just filled the entire embed up, so now we need to make a new one
                embed_list.append(discord.Embed(title=embed.title + " (continued)",
                                                color=embed.color))
                character_count = len(embed_list[-1].title)
        # Once we've gotten to here, we know that the remaining field character count is able to fit in one field.
        # Since the field character limit is smaller than the embed character limit, we know we'd only need one split.
        if field_character_count + len(field.name) + character_count > EMBED_CHARACTER_LIMIT:
            cutoff_point = field_description[:EMBED_CHARACTER_LIMIT - character_count - len(field.name)].rfind(' ')
            if cutoff_point == -1:
                cutoff_point = EMBED_CHARACTER_LIMIT - character_count - len(field.name) - 1
            embed_list[-1].add_field(name=field.name,
                                     value=field_description[:cutoff_point+1],
                                     inline=False)
            embed_list.append(discord.Embed(title=embed.title + " (continued)",
                                            color=embed.color))
            field_description = field_description[cutoff_point+1:]
            character_count = len(embed_list[-1].title) + len(field.name)
            embed_list[-1].add_field(name=field.name,
                                     value=field_description,
                                     inline=False)

        # I believe if we run here then we just don't need to split anything.
        else:
            embed_list[-1].add_field(name=field.name,
                                     value=field_description,
                                     inline=field.inline)
    return embed_list

def sort_channels_util(channel_list: list, prefixes: list = [solved_constants.SOLVEDISH_PREFIX,
                                                              solved_constants.BACKSOLVED_PREFIX,
                                                              solved_constants.SOLVED_PREFIX]) -> list:
    """Sort channels according to some prefixes"""
    channel_list_sorted = sorted(channel_list, key=lambda x: x.name)

    channel_list_prefixes = []
    for prefix in prefixes:
        channel_list_prefixes += list(filter(lambda x: x.name.startswith(prefix), channel_list_sorted))

    unsolved = channel_list_sorted
    unsolved = list(filter(lambda x: x not in channel_list_prefixes, unsolved))

    return unsolved + channel_list_prefixes

