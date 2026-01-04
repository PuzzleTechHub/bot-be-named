import nextcord
import os
import constants
from nextcord.ext import commands
from emoji import EMOJI_DATA
import emoji
from typing import Union
from utils import discord_utils, logging_utils, command_predicates

"""
Misc module. A collection of Misc useful/fun commands. Also everything not in any other module.
"""


class MiscCog(commands.Cog, name="Misc"):
    """
    A collection of Misc useful/fun commands.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="emojiall")
    async def emojiall(self, ctx, emoji_count: int = 20):
        """Reacts to the replied message with respective number of emojis (Uses A-Z emojis).

        Use: (as reply to another message) `~emojiall 5`
        Use: (as reply to another message) `~emojiall` (defaults to 20)
        """
        await logging_utils.log_command("emojiall", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if emoji_count <= 0:
            emoji_count = 1
        elif emoji_count > 20:
            emoji_count = 20

        letters_emojis = [chr(0x1F1E6 + i) for i in range(26)]
        # 🇦 🇧 🇨 🇩 🇪 🇫 🇬 🇭 🇮 🇯 🇰 🇱 🇲 🇳 🇴 🇵 🇶 🇷 🇸 🇹 🇺 🇻 🇼 🇽 🇾 🇿

        if not ctx.message.reference:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value="You need to reply to a message to use emojiall",
            )
            await discord_utils.send_message(ctx, embed)
            return

        # If it's replying to a message
        orig_msg = ctx.message.reference.resolved
        for i in range(emoji_count):
            e = letters_emojis[i]
            await orig_msg.add_reaction(emoji.emojize(e))

        await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))

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
                value="Unable to delete original message. Do I have `manage_messages` permissions?",
            )
            await discord_utils.send_message(ctx, embed)
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
            await discord_utils.send_message(ctx, embed)
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
            name="About Me!",
            value=f"Hello!\n"
            f"I am Bot Be Named (BBN) - a bot to help with puzzle hunts (more specifically, Google Sheets) on Discord!\n"
            f"BBN is designed to make puzzle hunts run more smoothly on Discord by:\n"
            f"- Creating and managing channels and sheets\n"
            f"- Talking with Google Sheets to easily collaborate with your fellow solvers on one central worksheet\n"
            f"- Marking puzzles as solved, unsolved, stuck, and more with easy commands\n"
            f"- And much more...!\n\n",
        )
        await discord_utils.send_message(ctx, embed)

        embed = discord_utils.create_embed()
        embed.add_field(
            name="Start Solving!",
            value=f"To start solving with BBN, follow these steps!\n"

            f"1. Invite BBN to your server by clicking on me in the member list!\n"
            f"2. Make your own copy of the template! (Ask us in BBN server)\n"
            f"3. Give permissions to people! (e.g. `{ctx.prefix}addperm Solver @everyone` or `{ctx.prefix}addperm Verified @everyone` etc.)\n"
            f"4. Create your category! Name it whatever you like, but make sure to make an archive category. (i.e. `My Category` and `My Category Archive`)\n"
            f"5. Create channels in your category! Channels like `#mycategory-discussion`, `#mycategory-bot-spam` maybe be useful to you!\n"
            f"6. Tether your sheet to your category! (`{ctx.prefix}tetherlion https://your.google.sheet.here`) Make sure you configure the sharing settings so I can edit it! \n"
            f"7. Start making puzzle channels! (`{ctx.prefix}chanlion 'Puzzle Name Here' 'puzzle.url.here.com'`)\n"
            f"8. Start solving! Mark puzzles as solved with `{ctx.prefix}solvedlion 'ANSWER'`, backsolved with `{ctx.prefix}backsolvedlion 'ANSWER'`,"
            f" move to archive with `{ctx.prefix}mtalion` and more! and more!\n\n",
        )
        await discord_utils.send_message(ctx, embed)

        embed = discord_utils.create_embed()
        embed.add_field(
            name="Need Help?",
            value=f"When in doubt, use `{ctx.prefix}help commandname` to get more info about a specific command!\n\n"

            f"Refer to `{ctx.prefix}info` for additional information!\n\n"

            f"[Bot Github Link (I'm open source!)](https://github.com/PuzzleTechHub/bot-be-named)  - [Bot Discord Link](https://discord.gg/x8f2ywHUky)\n\n"

            f"Any problems? Let {owner.mention} know.",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)

    @commands.command(name="info", aliases=["startup","start"])
    async def info(self, ctx):
        """A quick primer about helpful BBN functions

        Usage : `~info`
        """
        await logging_utils.log_command("info", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        embed.add_field(
            name="Helpful commands!",
            value=f"Here are some of the things I can do:\n"
            f"- `{ctx.prefix}about` a quick reference on how to start using the bot\n"
            f"- `{ctx.prefix}help` for a list of commands\n"
            f"- `{ctx.prefix}help commandname` for a description of a command (and its limitations). \n **When in doubt, use this command**.\n"
            f"Commonly used commands include-\n"
            f"- `{ctx.prefix}chanlion` for making Google Sheet tabs for your current hunt\n"
            f"- `{ctx.prefix}solvedlion` etc for marking puzzle channels as solved etc, and `{ctx.prefix}mtalion` for cleaning up the channels. \n"
            f"- `{ctx.prefix}addcustomcommand` etc for making a customised command with reply.\n\n",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)

        embed = discord_utils.create_embed()
        embed.add_field(
            name="Permissions!",
            value=f"I have a simple permisison system to manage who can use what commands. Most commands are restricted to certain permissions. "
            f"There are five permission categories:\n"
            f"- `(everyone)`: Can use basic commands like `{ctx.prefix}about`, `{ctx.prefix}help` etc.\n"
            f"- `Solver`: Can use most puzzle management commands.\n"
            f"- `Verified`: Can use generalised server or channel management commands like `{ctx.prefix}stats` or `{ctx.prefix}createchan`.\n"
            f"- `Trusted`: Can create custom commands, manage roles and channels.\n"
            f"- `(admin)`: Users who have a role with administrator privileges (this permission can not be assigned via command). "
            f"This permission is generally for destructive commands like `{ctx.prefix}deletecategory`.\n\n",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)

        embed = discord_utils.create_embed()
        embed.add_field(
            name="Assigning them!",
            value=f"- Use `{ctx.prefix}addperm level role` to add a permission to a role. Keep in mind only server admins or owners can use this command.\n"
            f"- Use `{ctx.prefix}removeperm level role` to remove a permission from a role.\n"
            f"- Example usage: `{ctx.prefix}addperm Solver @everyone`, `{ctx.prefix}addperm Trusted @Mods` etc.\n\n"
            f"- Note: Even though permission categories *seem* like they're ordered, they're actually not! You may be the owner of the server but you'll still need "
            f"to assign yourself the Verified/Solver/Trusted roles to use those commands!\n\n",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)

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
            await discord_utils.send_message(ctx, embed)
            return

        message = " ".join(args)

        channel = await discord_utils.find_chan_or_thread(ctx, channel_id_or_name)
        if channel is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Error! The channel `{channel_id_or_name}` was not found",
            )
            await discord_utils.send_message(ctx, embed)
            return

        try:
            await channel.send(message)
        except nextcord.Forbidden:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Forbidden! The bot is unable to speak on {channel.mention}! Have you checked if "
                f"the bot has the required permisisons?",
            )
            await discord_utils.send_message(ctx, embed)
            return

        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Message sent to {channel.mention}: {message}!",
        )
        # reply to user
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_trusted()
    @commands.command(name="botsayembed")
    async def botsayembed(self, ctx, channel_id_or_name: str, *args):
        """Say something in another channel, but as an embed

        Permission Category : Trusted roles only.
        Usage: `~botsayembed channelname Message`
        Usage: `~botsayembed #channelmention Longer Message`
        """
        await logging_utils.log_command(
            "botsayembed", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        if len(args) < 1:
            embed = discord_utils.create_no_argument_embed("Message")
            await discord_utils.send_message(ctx, embed)
            return

        message = " ".join(args)

        channel = await discord_utils.find_chan_or_thread(ctx, channel_id_or_name)
        if channel is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Error! The channel `{channel_id_or_name}` was not found",
            )
            await discord_utils.send_message(ctx, embed)
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
            await discord_utils.send_message(ctx, embed)
            return

        # reply to user
        sent_embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Embed sent to {channel.mention}",
            inline=False,
        )
        await discord_utils.send_message(ctx, sent_embed)


def setup(bot):
    bot.add_cog(MiscCog(bot))
