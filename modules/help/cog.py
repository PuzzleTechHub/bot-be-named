from discord.ext import commands
import constants
import discord
from utils import discord_utils


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help')
    async def real_help(self, ctx, *args):
        if len(args) < 1:
            embed = discord.Embed(title=f"{constants.HELP}",
                                  url="https://github.com/kevslinger/DiscordCipherRace",
                                  color=constants.EMBED_COLOR)
            embed.add_field(name="Welcome!",
                            value=f"Welcome to the help page! We offer the following modules. "
                                  f"Use {constants.BOT_PREFIX}help <module> to learn about "
                                  f"the commands in that module!",
                            inline=False)
            embed.add_field(name=constants.CIPHER_RACE,
                            value=f"Race against the clock as you decode ciphers. "
                                  f"Use {constants.BOT_PREFIX}startrace "
                                   "to start a race! "
                                  f"\nRead more on the [GitHub README]({constants.CIPHER_RACE_README})",
                            inline=False)
            embed.add_field(name=constants.CREATE_CHANNEL,
                            value=f"Create a channel! Use {constants.BOT_PREFIX}createchannel <channel_name> "
                                  f"to create a channel.",
                            inline=False)
            embed.add_field(name=constants.MOVE_CHANNEL,
                            value=f"Move a channel to another category! Use {constants.BOT_PREFIX}movechannel <category_name> "
                                  f"to move the channel.",
                            inline=False)
            embed.add_field(name=constants.SOLVED,
                            value=f"Mark a channel as solved! This will prepend 'solved' to the channel name. "
                                  f"Use {constants.BOT_PREFIX}solved in a channel to mark it as solved!",
                            inline=False)
            embed.add_field(name=constants.ARCHIVE_CHANNEL,
                            value=f"Download the contents of a channel in a zip file!",
                            inline=False)
            embed.add_field(name=constants.LOOKUP,
                            value=f"Search the interwebs (google)!\n"
                                  f"Read more on the [GitHub README]({constants.LOOKUP_README})",
                            inline=False)
        else:
            module = ' '.join(args).lower()
            if module in MODULE_TO_HELP:
                embed = MODULE_TO_HELP[module]()
            else:
                embed = discord_utils.create_embed()
                embed.add_field(name="Module not found!",
                                value=f"Sorry! Cannot find module {module}. The modules we have are \n"
                                      f"{', '.join(constants.MODULES)}",
                                inline=False)
        await ctx.send(embed=embed)


def cipher_race_help():
    embed = discord.Embed(title=f"{constants.CIPHER_RACE} {constants.HELP}",
                          url=constants.CIPHER_RACE_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{constants.BOT_PREFIX}startrace",
                    value=f"Starts a race!\n"
                          f"Optional: choose a wordlist (from {', '.join(constants.SHEETS)})\n"
                          f"e.g. {constants.BOT_PREFIX}startrace {constants.COMMON}",
                    inline=False)
    embed.add_field(name=f"{constants.BOT_PREFIX}answer <your_answer>",
                    value=f"Answer any of the codes during a race! If you are correct, the bot will react with "
                          f"a {constants.CORRECT_EMOJI}. Otherwise, it will react with a {constants.INCORRECT_EMOJI}",
                    inline=False)
    embed.add_field(name=f"{constants.BOT_PREFIX}practice",
                    value=f"Get a randomly selected word and cipher to decode at your own pace!\n"
                          f"Optional: Choose a cipher from {', '.join(constants.CIPHERS)}\n"
                          f"e.g. {constants.BOT_PREFIX}practice {constants.PIGPEN}\n"
                          f"Note: the bot will NOT check your answer. When you've solved, check it yourself by "
                          f"uncovering the spoiler text next to the image!",
                    inline=False)
    embed = more_help(embed, constants.CIPHER_RACE_README)
    #TODO: Add reload and reset?
    return embed


def create_channel_help():
    embed = discord.Embed(title=f"{constants.CREATE_CHANNEL} {constants.HELP}",
                          url=constants.CREATE_CHANNEL_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{constants.BOT_PREFIX}createchannel <channel_name>",
                    value=f"Create a channel named <channel_name> in the same category as the one you're currently in!",
                    inline=False)
    embed = more_help(embed, constants.CREATE_CHANNEL_README)
    return embed


def move_channel_help():
    embed = discord.Embed(title=f"{constants.MOVE_CHANNEL} {constants.HELP}",
                          url=constants.MOVE_CHANNEL_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{constants.BOT_PREFIX}movechannel <category_name>",
                    value=f"Moves the channel you're currently in to <category_name>",
                    inline=False)
    embed = more_help(embed, constants.MOVE_CHANNEL_README)
    return embed


def solved_help():
    embed = discord.Embed(title=f"{constants.SOLVED} {constants.HELP}",
                          url=constants.SOLVED_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{constants.BOT_PREFIX}solved",
                    value=f"Prepends 'solved' to the channel name you're currently in!",
                    inline=False)
    embed.add_field(name=f"{constants.BOT_PREFIX}unsolved",
                    value=f"Removes 'solved' to the channel name you're currently in!",
                    inline=False)
    embed.add_field(name=f"{constants.BOT_PREFIX}solvedish",
                    value=f"Prepends 'solvedish' to the channel name you're currently in!",
                    inline=False)
    embed.add_field(name=f"{constants.BOT_PREFIX}unsolvedish",
                    value=f"Removes 'solved' to the channel name you're currently in!",
                    inline=False)
    embed.add_field(name=f"{constants.BOT_PREFIX}backsolved",
                    value=f"Prepends 'backsolved' to the channel name you're currently in!",
                    inline=False)
    embed.add_field(name=f"{constants.BOT_PREFIX}unbacksolved",
                    value=f"Removes'backsolved' to the channel name you're currently in!",
                    inline=False)
    embed = more_help(embed, constants.SOLVED_README)
    return embed


def archive_channel_help():
    embed = discord.Embed(title=f"{constants.ARCHIVE_CHANNEL} {constants.HELP}",
                          url=constants.ARCHIVE_CHANNEL_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{constants.BOT_PREFIX}archivechannel <channel_id or #>",
                    value=f"Archives a channel! Gathers the chat history into a txt file, and compreses all attachments "
                          f"into a zip file.\n"
                          f"If you're in the same server as the channel you want to archive, you can use #channel_name. "
                          f"Otherwise, you need the channel ID.\n"
                          f"Note: Zips over 8MB will exceed discord's max file size. In that case, bot will only send the chat log.",
                    inline=False)
    embed.add_field(name=f"{constants.BOT_PREFIX}archivecategory <category_id>",
                    value=f"Archives a category! Will create a separate archive for each channel.\n"
                          f"*Whispers* It just uses {constants.BOT_PREFIX}archivechannel for each text "
                          f"channel in the category.",
                    inline=False)
    embed = more_help(embed, constants.ARCHIVE_CHANNEL_README)
    return embed


def lookup_help():
    embed = discord.Embed(title=f"{constants.LOOKUP} {constants.HELP}",
                          url=constants.LOOKUP_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{constants.BOT_PREFIX}search <target_site> <query>",
                    value=f"Search the interwebs!\n"
                          f"<target_site> must match ({', '.join(list(constants.REGISTERED_SITES.keys()))}) or "
                          f"be a domain name (e.g. 'khanacademy').\n"
                          f"e.g. {constants.BOT_PREFIX}search hp kevin entwhistle\n"
                          f"{constants.BOT_PREFIX}search kaspersky cryptography",
                    inline=False)
    embed = more_help(embed, constants.LOOKUP_README)
    return embed


def more_help(embed, readme_link):
    return embed.add_field(name=f"More {constants.HELP}",
                           value=f"Want to know more? Check out the [GitHub README]({readme_link})",
                           inline=False)


MODULE_TO_HELP = {
    constants.CIPHER_RACE.lower() : cipher_race_help,
    constants.CREATE_CHANNEL.lower(): create_channel_help,
    constants.MOVE_CHANNEL.lower(): move_channel_help,
    constants.SOLVED.lower(): solved_help,
    constants.ARCHIVE_CHANNEL.lower(): archive_channel_help,
    constants.LOOKUP.lower(): lookup_help
}


def setup(bot):
    bot.add_cog(HelpCog(bot))