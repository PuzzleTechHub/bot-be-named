import geopy
import os
import discord
from discord.ext import commands
from utils import discord_utils
from datetime import datetime

class DiscordCog(commands.Cog, name="Discord"):
    """Discord Utility Commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pin")
    async def pin(self, ctx):
        """Pin a message (Either a reply or the one above ~pin"""
        print("Received pin")
        if not ctx.message.reference:
            channel_history = await ctx.message.channel.history(limit=2).flatten()
            msg = channel_history[-1]
        else:
            msg = await ctx.fetch_message(ctx.message.reference.message_id)
        try:
            await msg.unpin()
            await msg.pin()
        except discord.HTTPException:
            embed = discord_utils.create_embed()
            embed.add_field(name="Error!",
                            value=f"Cannot pin system messages (e.g. **{self.bot.user.name}** pinned **a message** to this channel.)",
                            inline=False)
            await ctx.send(embed=embed)

    @commands.command(name="pinme")
    async def pinme(self, ctx):
        """Pins the message"""
        print("Received pinme")
        try:
            await ctx.message.pin()
        except discord.HTTPException:
            embed = discord_utils.create_embed()
            embed.add_field(name="Error!",
                            value=f"Issue pinning message. Perhaps I don't have permissions to pin?",
                            inline=False)
            await ctx.send(embed=embed)

    @commands.command(name="unpin")
    async def unpin(self, ctx, num_to_unpin: int = 1):
        """Unpin <num_to_unpin> messages, or all if num if 0"""
        print("Received unpin")
        if num_to_unpin < 1 or not isinstance(num_to_unpin, int):
            embed = discord_utils.create_no_argument_embed("number of messages to unpin")
            await ctx.send(embed=embed)
            return

        embed = discord_utils.create_embed()
        pins = await ctx.message.channel.pins()
        if num_to_unpin < len(pins):
            pins = pins[:num_to_unpin]
        else:
            num_to_unpin = len(pins)
        for pin in pins:
            try:
                await pin.unpin()
            except discord.HTTPException:
                embed.add_field(name="Error!",
                                value="I do not have permissions to unpin that message "
                                      "(or some other error, but probably perms)",
                                inline=False)
                await ctx.send(embed=embed)
                return

        embed.add_field(name="Success!",
                        value=f"Unpinned the most recent {num_to_unpin} " + ("messages" if num_to_unpin != 1 else "message"),
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="stats")
    async def stats(self, ctx):
        """Get server stats"""
        print("Received stats")
        guild = ctx.guild
        embed = discord_utils.create_embed()
        embed.add_field(name="Members",
                        value=f"{guild.member_count}")
        embed.add_field(name="Roles",
                        value=f"{len(guild.roles)}")
        embed.add_field(name="Emoji (limit)",
                        value=f"{len(guild.emojis)} ({guild.emoji_limit})")
        embed.add_field(name="Categories",
                        value=f"{len(guild.categories)}")
        embed.add_field(name="Text Channels",
                        value=f"{len(guild.text_channels)}")
        embed.add_field(name="Voice Channels",
                        value=f"{len(guild.voice_channels)}")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(DiscordCog(bot))