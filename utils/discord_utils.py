import nextcord
from nextcord.ext import commands
from nextcord.ext.commands.errors import ChannelNotFound
from typing import List, Tuple, Union
import constants
from modules.solved import solved_constants


def category_is_full(category: nextcord.CategoryChannel) -> bool:
    """Determines whether a category is full (has 50 channels)
    Arguments:
        - category (nextcord.CategoryChannel)
    Returns:
        - bool"""
    return len(category.channels) >= 50


async def createchannelgeneric(
    guild: nextcord.Guild, category: nextcord.CategoryChannel, name: str
) -> nextcord.TextChannel:
    """Command to create channel in same category with given name
    Arguments:
        - guild (nextcord.Guild): the guild the channel is being created in
        - category (nextcord.CategoryChannel): the category the channel is being created in
        - name (str): the name for the channel
    Returns:
        - channel (nextcord.TextChannel): The created channel, or none if the bot does not have sufficient perms.
    """
    try:
        # create channel
        channel = await guild.create_text_channel(name, category=category)
    except nextcord.Forbidden:
        return None

    return channel


async def createvoicechannelgeneric(
    guild: nextcord.Guild, category: nextcord.CategoryChannel, name: str
) -> nextcord.TextChannel:
    """Command to create channel in same category with given name
    Arguments:
        - guild (nextcord.Guild): the guild the channel is being created in
        - category (nextcord.CategoryChannel): the category the channel is being created in
        - name (str): the name for the channel
    Returns:
        - channel (nextcord.TextChannel): The created channel, or none if the bot does not have sufficient perms.
    """
    try:
        # create channel
        channel = await guild.create_voice_channel(name, category=category)
    except nextcord.Forbidden:
        return None

    return channel


def create_embed() -> nextcord.Embed:
    """
    Create an empty discord embed with color.
    :return: (nextcord.Embed)
    """
    return nextcord.Embed(description="", color=constants.EMBED_COLOR)


def create_no_argument_embed(arg_name: str = "argument") -> nextcord.Embed:
    """
    Create an embed which alerts the user they need to supply an argument
    :param arg_name: (str) The type of argument needed (e.g. channel)
    """
    embed = create_embed()
    embed.add_field(
        name=f"{constants.FAILED}!", value=f"You need to supply a {arg_name}!"
    )
    return embed


async def find_guild(
    ctx: commands.Context, guild_name: Union[nextcord.Guild, str]
) -> nextcord.Guild:
    """Uses nextcord.py's GuildConverter to convert the name to a discord Guild
    Arguments:
        - ctx (nextcord.ext.commands.Context): The command's context
        - guild_name (str): The name of the guild
    Returns:
        - guild (nextcord.Guild): the guild or None if not found"""
    if (isinstance(guild_name, nextcord.Guild)) or guild_name is None:
        return guild_name
    guild = None
    try:
        guilds = ctx.bot.guilds
        for currguild in guilds:
            if guild_name == currguild.name:
                guild = currguild
                break
    except Exception as e:
        pass
    return guild


async def find_category(
    ctx: commands.Context, category_name: Union[nextcord.CategoryChannel, str]
) -> nextcord.CategoryChannel:
    """Uses nextcord.py's CategoryChannelConverter to convert the name to a discord CategoryChannel
    Arguments:
        - ctx (nextcord.ext.commands.Context): The command's context
        - category_name (str): The name of the category
    Returns:
        - category (nextcord.CategoryChannel): the category or None if not found"""
    if (isinstance(category_name, nextcord.CategoryChannel)) or category_name is None:
        return category_name
    try:
        category = await commands.CategoryChannelConverter().convert(ctx, category_name)
    except ChannelNotFound:
        # Discord category finding is case specific, but the GUI displays all caps
        # Try to search with uppercase, first word capitalized, each word capitalized, and lowercase
        try:
            # Uppercase
            category = await commands.CategoryChannelConverter().convert(
                ctx, category_name.upper()
            )
        except ChannelNotFound:
            try:
                # Capitalize each word
                category = await commands.CategoryChannelConverter().convert(
                    ctx, category_name.title()
                )
            except ChannelNotFound:
                try:
                    # Capitalize first word
                    category = await commands.CategoryChannelConverter().convert(
                        ctx, category_name.capitalize()
                    )
                except ChannelNotFound:
                    try:
                        # Lowercase
                        category = await commands.CategoryChannelConverter().convert(
                            ctx, category_name.lower()
                        )
                    except ChannelNotFound:
                        category = None
    return category


async def pin_message(message: nextcord.Message) -> nextcord.Embed:
    """Pin a message. Catches Forbidden, HTTPSError (too many pins in channel)
    Arguments:
        - message (nextcord.Message): The message to pin
    Return:
        - embed (nextcord.Embed): We create an embed if any issue occurs in pinning.
    """
    # Channels can't have more than 50 pinned messages
    pins = await message.channel.pins()
    if len(pins) >= 50:
        embed = create_embed()
        embed.add_field(
            name=f"{constants.FAILED} to pin!",
            value="This channel already has max. number of pins (50)!",
        )
        return embed

    try:
        await message.unpin()
        await message.pin()
        async for pinmsg in message.channel.history(limit=5):
            if pinmsg.type == nextcord.MessageType.pins_add:
                await pinmsg.delete()
    except nextcord.Forbidden:
        embed = create_embed()
        embed.add_field(
            name=f"{constants.FAILED} to pin!",
            value=f"I don't have permissions to pin a message in {message.channel.mention}. Please check "
            "my permissions and try again.",
        )
        return embed
    except nextcord.HTTPException:
        embed = create_embed()
        embed.add_field(
            name=f"{constants.FAILED} to pin!",
            value=f"Cannot pin system messages (e.g. **Bot-Be-Named** pinned **a message** to this channel.)",
        )
        return embed

    return None


def populate_embed(names: list, values: list, inline: bool = False) -> nextcord.Embed:
    """Populate an embed with a list of names and values"""
    assert len(names) == len(
        values
    ), "Tried to populate an embed with uneven numbers of names and values"
    embed = nextcord.Embed(color=constants.EMBED_COLOR)
    for idx in range(len(names)):
        embed.add_field(name=names[idx], value=values[idx], inline=inline)
    return embed


def sort_channels_util(
    channel_list: list,
    prefixes: list = [
        solved_constants.SOLVEDISH_PREFIX,
        solved_constants.BACKSOLVED_PREFIX,
        solved_constants.SOLVED_PREFIX,
    ],
) -> list:
    """Sort channels according to some prefixes"""
    channel_list_sorted = sorted(channel_list, key=lambda x: x.name)

    channel_list_prefixes = []
    for prefix in prefixes:
        channel_list_prefixes += list(
            filter(lambda x: x.name.startswith(prefix), channel_list_sorted)
        )

    unsolved = channel_list_sorted
    unsolved = list(filter(lambda x: x not in channel_list_prefixes, unsolved))

    return unsolved + channel_list_prefixes

def split_embed(embed: nextcord.Embed) -> List[nextcord.Embed]:
    """Splits embeds that are too long (discord character limit)
    Arguments:
        - embed (nextcord.Embed)
    Returns
        - embed_list (List[nextcord.Embed]):
    """
    if embed.title == nextcord.Embed.Empty:
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
            embed_list.append(
                nextcord.Embed(
                    title=embed.title + " (continued)"
                    if len(embed_list) > 0
                    else embed.title,
                    color=embed.color,
                )
            )
            # Find the point that is closest to the cutoff but with a space.
            cutoff_point = description[
                : (EMBED_CHARACTER_LIMIT - len(embed.title))
            ].rfind(" ")
            if cutoff_point == -1:
                cutoff_point = EMBED_CHARACTER_LIMIT - len(embed.title) - 1
            embed_list[-1].description = description[: cutoff_point + 1]
            description = description[cutoff_point + 1 :]
            characters_remaining -= cutoff_point
    # If the title + description are small, we can just copy them over
    else:
        embed_list.append(
            nextcord.Embed(
                title=embed.title, description=embed.description, color=embed.color
            )
        )
    character_count = len(embed_list[-1].title) + len(embed_list[-1].description)

    # Iterate over all the proposed fields in the embed
    for field in embed.fields:
        field_description = field.value
        field_character_count = len(field_description)
        # Cut down the proposed fields to the appropriate size
        while field_character_count > FIELD_CHARACTER_LIMIT:
            # If we can add a full-sized field to the embed, do it
            if (
                character_count + len(field.name) + FIELD_CHARACTER_LIMIT
                <= EMBED_CHARACTER_LIMIT
            ):
                cutoff_point = field_description[:FIELD_CHARACTER_LIMIT].rfind(" ")
                if cutoff_point == -1:
                    cutoff_point = FIELD_CHARACTER_LIMIT - 1
                embed_list[-1].add_field(
                    name=field.name,
                    value=field_description[: cutoff_point + 1],
                    inline=False,
                )
                field_character_count -= cutoff_point
                field_description = field_description[cutoff_point + 1 :]
            # If we can't add a full field to the embed, add a chopped field and then create a new embed
            else:
                cutoff_point = field_description[
                    : EMBED_CHARACTER_LIMIT - character_count - len(field.name)
                ].rfind(" ")
                if cutoff_point == -1:
                    cutoff_point = (
                        EMBED_CHARACTER_LIMIT - character_count - len(field.name) - 1
                    )
                embed_list[-1].add_field(
                    name=field.name,
                    value=field_description[: cutoff_point + 1],
                    inline=False,
                )
                field_character_count -= cutoff_point
                field_description = field_description[cutoff_point + 1 :]
                # We just filled the entire embed up, so now we need to make a new one
                embed_list.append(
                    nextcord.Embed(title=embed.title + " (continued)", color=embed.color)
                )
                character_count = len(embed_list[-1].title)
        # Once we've gotten to here, we know that the remaining field character count is able to fit in one field.
        # Since the field character limit is smaller than the embed character limit, we know we'd only need one split.
        if (
            field_character_count + len(field.name) + character_count
            > EMBED_CHARACTER_LIMIT
        ):
            cutoff_point = field_description[
                : EMBED_CHARACTER_LIMIT - character_count - len(field.name)
            ].rfind(" ")
            if cutoff_point == -1:
                cutoff_point = (
                    EMBED_CHARACTER_LIMIT - character_count - len(field.name) - 1
                )
            embed_list[-1].add_field(
                name=field.name,
                value=field_description[: cutoff_point + 1],
                inline=False,
            )
            embed_list.append(
                nextcord.Embed(title=embed.title + " (continued)", color=embed.color)
            )
            field_description = field_description[cutoff_point + 1 :]
            character_count = len(embed_list[-1].title) + len(field.name)
            embed_list[-1].add_field(
                name=field.name, value=field_description, inline=False
            )

        # I believe if we run here then we just don't need to split anything.
        else:
            embed_list[-1].add_field(
                name=field.name, value=field_description, inline=field.inline
            )
    return embed_list
