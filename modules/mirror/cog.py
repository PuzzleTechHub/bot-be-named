import nextcord
import sqlalchemy
import database
from typing import Optional
from nextcord.ext import commands
from sqlalchemy.orm import Session
from utils import discord_utils, command_predicates

"""
Channel Mirror module. Copies messages heard from one channel and puts them in another.
e.g., all messages in #mod-mails gets sent to #vets-chat.
"""


class ChannelMirrorCog(commands.Cog, name="Channel Mirror"):
    """For copying messages from one channel into another."""

    def __init__(self, bot):
        self.bot = bot

    @command_predicates.is_bot_owner_or_admin()
    @commands.command(name="mirrorchan", aliases=["mirrorchannel"])
    async def mirrorchan(
        self,
        ctx: commands.Context,
        source: nextcord.TextChannel,
        target: Optional[nextcord.TextChannel] = None,
    ):
        """Mirrors every new message from a source channel into a target channel.
        Messages before this command was called, edits, and deletes will not be mirrored.
        Only messages from people are mirrored, not bots or webhooks.

        See also `~unmirrorchan` and `~listmirrorchan`.

        Permission Category : Server Moderators only.
        Usage: `~mirrorchan #mod-mails` (copies #mod-mails into the current channel)
        Usage: `~mirrorchan #mod-mails #vets-chat` (copies #mod-mails into #vets-chat)
        """
        embed = discord_utils.create_embed()

        if ctx.guild is None:
            embed.add_field(
                name="Failed",
                value="This command must be used in a server.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        if target is None:
            if not isinstance(ctx.channel, nextcord.TextChannel):
                embed.add_field(
                    name="Failed",
                    value=f"I can only mirror messages into a text channel, not `{ctx.channel}`.",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return
            target = ctx.channel

        if source == target:
            embed.add_field(
                name="Failed",
                value="A channel cannot mirror itself.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        with Session(database.DATABASE_ENGINE) as session:
            existed = (
                session.query(database.ChannelMirrors)
                .filter_by(source_channel_id=source.id, target_channel_id=target.id)
                .first()
            )
            if existed is None:
                stmt = sqlalchemy.insert(database.ChannelMirrors).values(
                    server_id=ctx.guild.id,
                    server_name=ctx.guild.name,
                    source_channel_id=source.id,
                    source_channel_name=source.name,
                    target_channel_id=target.id,
                    target_channel_name=target.name,
                )
                session.execute(stmt)
                session.commit()

        if source.id not in database.CHANNEL_MIRRORS:
            database.CHANNEL_MIRRORS[source.id] = set()
        database.CHANNEL_MIRRORS[source.id].add(target.id)

        if existed:
            value = f"Messages in {source.mention} are already being mirrored to {target.mention}."
        else:
            value = f"New messages in {source.mention} will be mirrored to {target.mention}."
        embed.add_field(name="Success", value=value, inline=False)
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_bot_owner_or_admin()
    @commands.command(
        name="unmirrorchan",
        aliases=["unmirrorchannel", "rmmirrorchan"],
    )
    async def unmirrorchan(
        self,
        ctx: commands.Context,
        source: nextcord.TextChannel,
        target: Optional[nextcord.TextChannel] = None,
    ):
        """Stops all mirroring of messages from a channel into a current channel (or given channels).

        See also `~mirrorchan` and `~listmirrorchan`.

        Permission Category : Server Moderators only.
        Usage: `~unmirrorchan #mod-mails` (stops mirroring #mod-mails into current channel)
        Usage: `~unmirrorchan #mod-mails #vets-chat` (stops mirroring #mod-mails into #vets-chat)
        """
        embed = discord_utils.create_embed()

        if target is None:
            if not isinstance(ctx.channel, nextcord.TextChannel):
                embed.add_field(
                    name="Failed",
                    value="Mirrors only exist in server text channels.",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return
            target = ctx.channel

        with Session(database.DATABASE_ENGINE) as session:
            deleted = (
                session.query(database.ChannelMirrors)
                .filter_by(source_channel_id=source.id, target_channel_id=target.id)
                .delete()
            )
            session.commit()

        if source.id in database.CHANNEL_MIRRORS:
            database.CHANNEL_MIRRORS[source.id].discard(target.id)

        if deleted:
            embed.add_field(
                name="Success",
                value=f"Messages in {source.mention} will no longer be mirrored to {target.mention}.",
                inline=False,
            )
        else:
            embed.add_field(
                name="Failed",
                value=f"No mirroring exists from {source.mention} to {target.mention}.",
                inline=False,
            )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_bot_owner_or_admin()
    @commands.command(name="listmirrorchan")
    async def listmirrorchan(self, ctx: commands.Context):
        """Lists every channel being copied into another channel on this server.

        See also `~mirrorchan` and `~unmirrorchan`.

        Permission Category : Server Moderators only.
        Usage: `~listmirrorchan`
        """
        if ctx.guild is None:
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value="This command must be used in a server.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        with Session(database.DATABASE_ENGINE) as session:
            result = (
                session.query(database.ChannelMirrors)
                .filter_by(server_id=ctx.guild.id)
                .all()
            )
            lines = [
                f"<#{row.source_channel_id}> -> <#{row.target_channel_id}>"
                for row in result
            ]

        embed = discord_utils.create_embed()
        if lines:
            embed.add_field(
                name="Channel mirrors", value="\n".join(lines), inline=False
            )
        else:
            embed.add_field(
                name="Channel mirrors",
                value=f"No channels are being mirrored on this server. Why not add one with `{ctx.prefix}mirrorchan`?",
                inline=False,
            )
        await discord_utils.send_message(ctx, embed)


def setup(bot):
    bot.add_cog(ChannelMirrorCog(bot))
