import discord
import constants

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