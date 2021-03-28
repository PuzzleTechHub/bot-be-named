import discord
import constants

def create_embed() -> discord.Embed:
    """
    Create an empty discord embed with color.
    :return: (discord.Embed)
    """
    return discord.Embed(color=constants.EMBED_COLOR)


def create_no_argument_embed(arg_name='argument') -> discord.Embed:
    """
    Create an embed which alerts the user they need to supply an argument
    :param arg_name: (str) The type of argument needed (e.g. channel)
    """
    embed = create_embed()
    embed.add_field(name=f'{constants.FAILED}!', value=f"You need to supply a {arg_name}!")
    return embed