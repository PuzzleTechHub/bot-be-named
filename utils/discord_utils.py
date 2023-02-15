import nextcord
from nextcord.ext import commands
from nextcord.ext.commands.errors import ChannelNotFound, ThreadNotFound
from typing import List, Tuple, Union
import constants


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
        - category (nextcord.TextChannel): the category the channel is being created in
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


async def createthreadgeneric(
    message: nextcord.Message,
    chan_or_forum: Union[nextcord.TextChannel, nextcord.ForumChannel],
    name: str,
) -> nextcord.Thread:
    """Command to create thread in same channel with given name
    Arguments:
        - guild (nextcord.Guild): the guild the channel is being created in
        - category_or_forum (nextcord.CategoryChannel or nextcord.ForumChannel): the category or forum the channel is being created in
        - name (str): the name for the channel
    Returns:
        - thread (nextcord.Thread): The created thread, or none if the bot does not have sufficient perms.
    """
    try:
        # create channel
        thread = await chan_or_forum.create_thread(name=name, message=message)
    except nextcord.Forbidden:
        return None

    return thread


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


async def find_chan_or_thread(
    ctx: commands.Context, chan_name: Union[nextcord.TextChannel, nextcord.Thread, str]
) -> Union[nextcord.TextChannel, nextcord.Thread]:
    """Convert the name to a nextcord Channel/Thread
    Arguments:
        - ctx (nextcord.ext.commands.Context): The command's context
        - chan_name (str): The name of the role
    Returns:
        - chan_or_thread (nextcord.TextChannel): the channel or thread or None if not found"""

    if (
        isinstance(chan_name, nextcord.TextChannel)
        or isinstance(chan_name, nextcord.Thread)
        or chan_name is None
    ):
        return chan_name
    try:
        chan_or_thread = await commands.TextChannelConverter().convert(ctx, chan_name)
        return chan_or_thread
    except ChannelNotFound:
        try:
            chan_or_thread = await commands.ThreadConverter().convert(ctx, chan_name)
            return chan_or_thread
        except ThreadNotFound:
            return None


async def find_role(
    ctx: commands.Context, role_name: Union[nextcord.Role, str]
) -> nextcord.Role:
    """Convert the name to a nextcord Role
    Arguments:
        - ctx (nextcord.ext.commands.Context): The command's context
        - role_name (str): The name of the role
    Returns:
        - role (nextcord.Role): the role or None if not found"""

    if (isinstance(role_name, nextcord.Role)) or role_name is None:
        return role_name
    for role in ctx.guild.roles:
        if role.name.lower() == role_name.lower():
            return role
    return None


async def find_user(
    ctx: commands.Context, user_name: Union[nextcord.Member, str]
) -> nextcord.Role:
    """Convert the name to a nextcord Member
    Arguments:
        - ctx (nextcord.ext.commands.Context): The command's context
        - user_name (str): The name of the user
    Returns:
        - user (nextcord.Member): the user or None if not found"""

    if (isinstance(user_name, nextcord.Member)) or user_name is None:
        return user_name
    guild_users = ctx.guild.members
    for user in guild_users:
        if user.name.lower() == user_name.lower():
            return user
    return None


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


def split_embed(embed: nextcord.Embed) -> List[nextcord.Embed]:
    """Splits embeds that are too long (discord character limit)
    Arguments:
        - embed (nextcord.Embed)
    Returns
        - embed_list (List[nextcord.Embed]):
    """
    if embed.title is None:
        embed_title = ""
    else:
        embed_title = embed.title

    EMBED_CHARACTER_LIMIT = 2000  # Actual limit is 2000.
    FIELD_CHARACTER_LIMIT = 1000  # Actual limit is 1000.
    embed_list = []

    character_count = len(embed_title) + (
        0 if (embed.description == None) else len(embed.description)
    )
    # If the title + description exceeds the character limit, we must break up the description into smaller parts.
    if character_count > EMBED_CHARACTER_LIMIT:
        print(f"Title and description are too long with {character_count} characters")
        characters_remaining = character_count
        description = embed.description
        while description != "":
            embed_list.append(
                nextcord.Embed(
                    title=embed_title + " (continued)"
                    if len(embed_title) > 0
                    else embed_title,
                    color=embed.color,
                )
            )
            # Find the point that is closest to the cutoff but with a space.
            cutoff_point = description[
                : (EMBED_CHARACTER_LIMIT - len(embed_title))
            ].rfind(" ")
            if cutoff_point == -1:
                cutoff_point = EMBED_CHARACTER_LIMIT - len(embed_title) - 1
            embed_list[-1].description = description[: cutoff_point + 1]
            description = description[cutoff_point + 1 :]
            characters_remaining -= cutoff_point
    # If the title + description are small, we can just copy them over
    else:
        embed_list.append(
            nextcord.Embed(
                title=embed_title, description=embed.description, color=embed.color
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
                    nextcord.Embed(
                        title=embed_title + " (continued)", color=embed.color
                    )
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
                nextcord.Embed(title=embed_title + " (continued)", color=embed.color)
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
