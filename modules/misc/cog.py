import nextcord
import os
from nextcord.ext import commands
from emoji import EMOJI_DATA
from typing import Union
import constants
from utils import discord_utils, logging_utils, command_predicates


class MiscCog(commands.Cog, name="Misc"):
    """A collection of Misc useful/fun commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="emoji")
    async def emoji(
        self, ctx, emojiname: Union[nextcord.Emoji, str], to_delete: str = ""
    ):
        """Finds the custom emoji mentioned and uses it.
        This command works for normal as well as animated emojis, as long as the bot is in one server with that emoji.

        If you say delete after the emoji name, it deletes original message

        If this command is a reply to another message, it'll instead be a react to that message.

        Usage : `~emoji snoo_glow delete`
        Usage : `~emoji :snoo_grin:`
        """
        await logging_utils.log_command("emoji", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        try:
            if to_delete.lower()[0:3] == "del":
                await ctx.message.delete()
        except nextcord.Forbidden:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Unable to delete original message. Do I have `manage_messages` permissions?",
            )
            await ctx.send(embed=embed)
            return

        emoji = None
        hasurl = False

        # custom emoji
        if isinstance(emojiname, nextcord.Emoji):
            emoji = emojiname
            hasurl = True
        # default emoji
        elif isinstance(emojiname, str) and emojiname in EMOJI_DATA:
            emoji = emojiname
            hasurl = False
        elif emojiname[0] == ":" and emojiname[-1] == ":":
            emojiname = emojiname[1:-1]
            for guild in self.bot.guilds:
                emoji = nextcord.utils.get(guild.emojis, name=emojiname)
                if emoji is not None:
                    break
                hasurl = True

        if emoji is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Emoji named {emojiname} not found",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        if ctx.message.reference:
            # If it's replying to a message
            orig_msg = ctx.message.reference.resolved
            await orig_msg.add_reaction(emoji)
            return
        else:
            # Just a normal command
            if hasurl:
                await ctx.send(emoji.url)
            else:
                await ctx.send(emoji)
            return

    @commands.command(name="about", aliases=["aboutthebot", "github"])
    async def about(self, ctx):
        """A quick primer about BBN and what it does

        Usage : `~about`
        """
        await logging_utils.log_command("about", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        owner = await self.bot.fetch_user(os.getenv("BOT_OWNER_DISCORD_ID"))

        embed.add_field(
            name=f"About Me!",
            value=f"Hello!\n"
            f"Bot Be Named is a discord bot that we use while solving Puzzle Hunts.\n"
            f"The bot has a few channel management functions, some puzzle-hunt utility functions, "
            f"as well as Google-Sheets interactivity.\n"
            f"You can make channels as well as tabs on your Sheet, and other similar QoL upgrades to your puzzlehunting setup.\n\n"
            f"[Bot Github link](https://github.com/kevslinger/bot-be-named/)  - [Bot Discord Link](https://discord.gg/x8f2ywHUky)\n\n"
            f"To learn more about the bot or useful functions, use `{constants.DEFAULT_BOT_PREFIX}startup`\n"
            f"Any problems? Let {owner.mention} know.",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(name="startup")
    async def startup(self, ctx):
        """A quick primer about helpful BBN functions

        Usage : `~startup`
        """
        await logging_utils.log_command("startup", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        embed.add_field(
            name=f"Helpful commands!",
            value=f"Some of the useful bot commands are -\n"
            f"- `{ctx.prefix}help` for a list of commands\n"
            f"- `{ctx.prefix}help commandname` for a description of a command (and its limitations). \n **When in doubt, use this command**.\n"
            f"- `{ctx.prefix}chanlion` and `{ctx.prefix}sheetlion` for making Google Sheet tabs for your current hunt\n"
            f"- `{ctx.prefix}solvedlion` etc for marking puzzle channels as solved etc, and `{ctx.prefix}mtalion` for cleaning up the channels. \n"
            f"- `{ctx.prefix}addcustomcommand` etc for making a customised command with reply.\n\n"
            f"Note that most commands are only restricted to certain Permission Categories. The current categories for those are - Verified/Trusted/Solver/Tester. These need to be configured accordingly.\n"
            f"- `{ctx.prefix}addperm` for setting up Permission Categories on your server (see `{ctx.prefix}help addperm` and `{ctx.prefix} permcathelp`for an explanation)\n",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(name="permcathelp")
    async def permcathelp(self, ctx):
        """A quick primer about permissions in BBN, and what they do.

        Usage : `~permcathelp`
        """
        await logging_utils.log_command("permcathelp", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        embed.add_field(
            name=f"Permission Categories!",
            value=f"In BBN, nearly every command is restricted to some Permission Category or the other. This allows server owners and admins to control what commands are available to users.\n"
            f"So you need to use `{ctx.prefix}addperm` before you can do almost anything else.\n"
            f"The Permission Categories available are - Verified, Trusted, Solver, Tester.\n\n"
            f"- Solver - All 'regular' solving and sheet functions\n"
            f"- Verified - All channel management functions + some archive functions\n"
            f"- Trusted - Can edit customcommands, and use any role commands\n"
            f"- Tester - Used internally.\n"
            f"- (admin) - Delete roles, categories and more. Not an actual Permission category, but restricted to server admins.\n\n"
            f"So your first command in any server is probably `{ctx.prefix}addperm Solver @Rolename` or so. See `{ctx.prefix}help addperm` `for more info.\n",
            inline=False,
        )
        await ctx.send(embed=embed)

    ###################
    # BOTSAY COMMANDS #
    ###################

    @command_predicates.is_trusted()
    @commands.command(name="botsay")
    async def botsay(self, ctx, channel_id_or_name: str, *args):
        """Say something in another channel

        Permission Category : Trusted roles only.
        Usage: `~botsay channelname Message`
        Usage: `~botsay #channelmention Longer Message`
        """
        await logging_utils.log_command("botsay", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if len(args) < 1:
            embed = discord_utils.create_no_argument_embed("Message")
            await ctx.send(embed=embed)
            return

        message = " ".join(args)
        guild = ctx.message.guild

        channel = await discord_utils.find_chan_or_thread(ctx, channel_id_or_name)
        if channel is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Error! The channel `{channel_id_or_name}` was not found",
            )
            await ctx.send(embed=embed)
            return

        try:
            await channel.send(message)
        except nextcord.Forbidden:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Forbidden! The bot is unable to speak on {channel.mention}! Have you checked if "
                f"the bot has the required permisisons?",
            )
            await ctx.send(embed=embed)
            return

        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Message sent to {channel.mention}: {message}!",
        )
        # reply to user
        await ctx.send(embed=embed)

    @command_predicates.is_trusted()
    @commands.command(name="botsayembed")
    async def botsayembed(self, ctx, channel_id_or_name: str, *args):
        """Say something in another channel, but as an embed

        Permission Category : Trusted roles only.
        Usage: `~botsayembed channelname Message`
        Usage: `~botsayembed #channelmention Longer Message`
        """
        await logging_utils.log_command("botsayembed", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if len(args) < 1:
            embed = discord_utils.create_no_argument_embed("Message")
            await ctx.send(embed=embed)
            return

        message = " ".join(args)

        channel = await discord_utils.find_chan_or_thread(ctx, channel_id_or_name)
        if channel is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Error! The channel `{channel_id_or_name}` was not found",
            )
            await ctx.send(embed=embed)
            return

        try:
            sent_embed = discord_utils.create_embed()
            sent_embed.description = message
            await channel.send(embed=sent_embed)
        except nextcord.Forbidden:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Forbidden! The bot is unable to speak on {channel.mention}! Have you checked if "
                f"the bot has the required permisisons?",
            )
            await ctx.send(embed=embed)
            return

        # reply to user
        sent_embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Embed sent to {channel.mention}",
            inline=False,
        )
        await ctx.send(embed=sent_embed)


def setup(bot):
    bot.add_cog(MiscCog(bot))
