import typing
import nextcord
import aiohttp
import io
import emoji
import constants
from nextcord.ext import commands
from utils import discord_utils, logging_utils, command_predicates

"""
Discord module. Functions and commands related specificially to discord functionality, that does not intersect with any other modules.
For example, pinning/unpinning messages, or getting statistics for a server.
"""


class DiscordCog(commands.Cog, name="Discord"):
    """
    Commands for generic discord things.
    """

    def __init__(self, bot):
        self.bot = bot

    ####################
    # PINNING COMMANDS #
    ####################

    @commands.command(name="pin")
    async def pin(self, ctx, to_delete: str = ""):
        """Pin a message (Either reply to the message, or it auto pins the message above)

        If the message is already pinned, just unpins and repins (brings it to top of pins).

        If you say delete after the command, it deletes original message that called the command.

        Usage: `~pin` (as reply to message)
        Usage: `~pin` (to just pin the last message)
        Usage: `~pin del` (to pin the message and also delete the msg)
        """
        await logging_utils.log_command("pin", ctx.guild, ctx.channel, ctx.author)

        if not ctx.message.reference:
            channel_history = await ctx.message.channel.history(limit=2).flatten()
            message = channel_history[-1]
        else:
            message = await ctx.fetch_message(ctx.message.reference.message_id)

        embed_or_none = await discord_utils.pin_message(message)

        # Error pinning, send error message to user
        if embed_or_none is not None:
            await discord_utils.send_message(ctx, embed_or_none)
        else:
            await message.add_reaction(emoji.emojize(":pushpin:"))
            await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))

        try:
            if to_delete.lower()[0:3] == "del":
                await ctx.message.delete()
        except nextcord.Forbidden:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Unable to delete original message. Do I have `manage_messages` permissions?",
            )
            await discord_utils.send_message(ctx, embed)
            return

    @commands.command(name="pinme")
    async def pinme(self, ctx):
        """Pins the message that called it.

        Usage : `~pinme Message`
        """
        await logging_utils.log_command("pinme", ctx.guild, ctx.channel, ctx.author)

        embed_or_none = await discord_utils.pin_message(ctx.message)
        # Error pinning, send error message to user
        if embed_or_none is not None:
            await discord_utils.send_message(ctx, embed_or_none)
        else:
            await ctx.message.add_reaction(emoji.emojize(":pushpin:"))

    @commands.command(name="unpin")
    async def unpin(self, ctx, num_to_unpin: int = 1):
        """Unpins a specific message from a channel, or a given number of pins

        Usage: `~unpin 2` (unpins latest 2 pins)
        Usage: `~unpin` (as a reply to pinned message)
        """
        await logging_utils.log_command("unpin", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if num_to_unpin < 1 or not isinstance(num_to_unpin, int):
            embed = discord_utils.create_no_argument_embed(
                "number of messages to unpin"
            )
            await discord_utils.send_message(ctx, embed)
            return

        pins = await ctx.message.channel.pins()
        messages_to_unpin = []
        strmsg = ""

        reply = False
        # If unpin is in direct reply to another message, unpin only that message
        if ctx.message.reference:
            reply = True
            orig_msg = ctx.message.reference.resolved
            if not orig_msg.pinned:
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"The linked message [Msg]({orig_msg.jump_url}) has not been pinned, there's nothing to unpin.",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return
            messages_to_unpin.append(orig_msg)
        # Else unpin the last X messages
        else:
            if num_to_unpin < len(pins):
                messages_to_unpin = pins[:num_to_unpin]
            # If too many messages to unpin, just unpin all
            else:
                messages_to_unpin = pins

        i = 1
        for pin in messages_to_unpin:
            try:
                await pin.unpin()
                await pin.remove_reaction(emoji.emojize(":pushpin:"), ctx.me)
                strmsg = strmsg + f"[Msg{i}]({pin.jump_url}) : "
                i = i + 1
            except nextcord.Forbidden:
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"I do not have permissions to unpin that message. Please check my perms and try again?",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return

        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Unpinned {'the most recent' if not reply else ''} {i - 1} {'messages' if i - 1 != 1 else 'message'}\n"
            + f"{strmsg[:-3]}",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
        await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))

    @commands.command(name="lspin", aliases=["lspins", "listpin", "listpins"])
    async def listpin(self, ctx):
        """Lists all the pinned posts in the current channel

        Usage: `~listpins~`
        """

        await logging_utils.log_command("listpin", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        pins = await ctx.message.channel.pins()
        strmsg = ""
        i = 1
        for pin in pins:
            strmsg = strmsg + f"[Msg{i}]({pin.jump_url}) : "
            i += 1

        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"There are {len(pins)} pinned posts on this channel."
            f"\n{strmsg[:-3]}",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)

    #######################
    # STATISTICS COMMANDS #
    #######################

    @command_predicates.is_verified()
    @commands.command(name="stats")
    async def stats(self, ctx):
        """Get server stats

        Permission Category : Verified Roles only.
        Usage: `~stats`
        """
        await logging_utils.log_command("stats", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        guild = ctx.guild

        embed.add_field(name="Members", value=f"{guild.member_count}", inline=False)
        embed.add_field(name="Roles", value=f"{len(guild.roles)}", inline=False)
        embed.add_field(
            name="Emoji (limit)",
            value=f"{len(guild.emojis)} ({guild.emoji_limit})",
            inline=False,
        )
        embed.add_field(
            name="Categories/Channels/VCs (limit)",
            value=f"{len(guild.channels)} (500)",
            inline=False,
        )

        embed.add_field(
            name="Categories", value=f"{len(guild.categories)}", inline=False
        )
        embed.add_field(
            name="Text Channels", value=f"{len(guild.text_channels)}", inline=False
        )
        embed.add_field(
            name="Voice Channels", value=f"{len(guild.voice_channels)}", inline=False
        )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_verified()
    @commands.command(name="catstats")
    async def catstats(self, ctx, cat_name: str = ""):
        """Get category stats

        Permission Category : Verified Roles only.
        Usage: `~catstats` (current category)
        Usage: `~catstats "Cat Name"` (Named category)
        """
        await logging_utils.log_command("catstats", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if cat_name == "":
            cat = ctx.message.channel.category
        else:
            cat = await discord_utils.find_category(ctx, cat_name)

        if cat is None:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"I cannot find category `{cat_name}`. Perhaps check your spelling and try again.",
            )
            await discord_utils.send_message(ctx, embed)
            return

        embed.add_field(name="Category Name", value=f"{cat.name}", inline=False)
        embed.add_field(
            name="Text Channels", value=f"{len(cat.text_channels)}", inline=False
        )
        embed.add_field(
            name="Voice Channels", value=f"{len(cat.voice_channels)}", inline=False
        )
        await discord_utils.send_message(ctx, embed)

    ##################
    # EMOJI COMMANDS #
    ##################

    @commands.command(
        name="listreacts",
        aliases=[
            "lsreacts",
            "listreact",
            "lsreact",
            "listreactions",
            "lsreactions",
            "listreaction",
            "lsreaction",
        ],
    )
    async def listreacts(self, ctx):
        """List all reactions made to a given message

        Usage: `~listreacts` (as a reply to a message)
        """
        await logging_utils.log_command(
            "listreacts", ctx.guild, ctx.channel, ctx.author
        )

        if not ctx.message.reference:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Command `~listreacts` can only be called as a reply to another message.",
            )
            await discord_utils.send_message(ctx, embed)
            return
        else:
            message = await ctx.fetch_message(ctx.message.reference.message_id)

        embed_message = ""
        for reaction in message.reactions:
            embed_message = (
                embed_message
                + "\n"
                + f" {reaction.emoji} - {' : '.join([user.mention for user in await reaction.users().flatten()])}"
            )

        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"Reactions to message = {len(message.reactions)}",
            value=embed_message,
        )
        await discord_utils.send_message(ctx, embed)

    @commands.command(name="listemoji", aliases=["lsemoji", "listemojis", "lsemojis"])
    async def listemoji(self, ctx):
        """List all emojis in a server

        Usage: `~listemojis`
        """
        await logging_utils.log_command("listemoji", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"Emoji in {ctx.guild.name}",
            value=f"{chr(10).join([f'{emoji} - {emoji.name} - {emoji.id}' for emoji in ctx.guild.emojis])}",
        )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_verified()
    @commands.command(name="steal")
    async def steal(
        self, ctx, *emojis: typing.Union[nextcord.Emoji, nextcord.PartialEmoji]
    ):
        """Steals an emote from another server and uploads it to this server with the same name.

        Permission Category : Verified Roles only.
        Usage: `~steal :emote1: :emote2:`
        """
        await logging_utils.log_command("steal", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        for emoji in emojis:
            url = str(emoji.url)
            name = emoji.name
            async with aiohttp.ClientSession() as ses:
                async with ses.get(url) as r:
                    try:
                        img_or_gif = io.BytesIO(await r.read())
                        b_value = img_or_gif.getvalue()
                        try:
                            emoji = await ctx.guild.create_custom_emoji(
                                image=b_value, name=name
                            )

                            embed.add_field(
                                name=f"{constants.SUCCESS}",
                                value=f"Added {emoji} with name {emoji.name}",
                            )
                            await ses.close()
                        except nextcord.Forbidden:
                            embed.add_field(
                                name=f"{constants.FAILED}",
                                value=f"Error adding `:{name}:` to server. Do I have the correct permissions to manage emotes in this server?",
                            )
                            await ses.close()
                        except:
                            embed.add_field(
                                name=f"{constants.FAILED}",
                                value=f"Could not add `:{name}:` to server. Do you have any emote slots left?",
                            )
                            await ses.close()
                    except:
                        embed.add_field(
                            name=f"{constants.FAILED}",
                            value=f"Could not find emote `:{name}:`.",
                        )
        await discord_utils.send_message(ctx, embed)


def setup(bot):
    bot.add_cog(DiscordCog(bot))
