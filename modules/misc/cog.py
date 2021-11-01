import discord
import os
from discord.ext import commands
from emoji import UNICODE_EMOJI
from typing import Union

import constants
from utils import discord_utils, logging_utils


class MiscCog(commands.Cog, name="Misc"):
    """Get time and timezone of any location"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="emoji")
    async def emoji(self, ctx, emojiname: Union[discord.Emoji, str], to_delete: str = ""):
        """Finds the custom emoji mentioned and uses it. 
        This command works for normal as well as animated emojis, as long as the bot is in one server with that emoji.

        If you say delete after the emoji name, it deletes original message

        Usage : `~emoji snoo_glow delete`
        Usage : `~emoji :snoo_grin:`
        """
        logging_utils.log_command("emoji", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()
        emoji = None

        try:
            if(to_delete.lower()[0:3]=="del"):
                await ctx.message.delete()
        except discord.Forbidden:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Unable to delete original message. Do I have `manage_messages` permissions?")
            await ctx.send(embed=embed)
            return

        # custom emoji
        if isinstance(emojiname, discord.Emoji):
            await ctx.send(emojiname.url)
            return
        # default emoji
        elif isinstance(emojiname, str) and emojiname in UNICODE_EMOJI:
            await ctx.send(emojiname)
            return
        if emojiname[0]==":" and emojiname[-1]==":":
            emojiname = emojiname[1:-1]

        for guild in self.bot.guilds:
            emoji = discord.utils.get(guild.emojis, name=emojiname)
            if emoji is not None:
                break

        if emoji is None:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Emoji named {emojiname} not found",
                            inline=False)
            await ctx.send(embed=embed)
            return

        await ctx.send(emoji.url)


def setup(bot):
    bot.add_cog(MiscCog(bot))