from discord.ext import commands
import constants
import discord
from utils import discord_utils
from modules.help import help_constants
from modules.lookup import lookup_constants
from modules.code import code_constants


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help')
    async def real_help(self, ctx, *args):
        if len(args) < 1:
            embed = discord.Embed(title=f"{help_constants.HELP}",
                                  url="https://github.com/kevslinger/DiscordCipherRace",
                                  color=constants.EMBED_COLOR)
            embed.add_field(name="Welcome!",
                            value=f"Welcome to the help page! We offer the following modules. "
                                  f"Use {ctx.prefix}help <module> to learn about "
                                  f"the commands in that module!",
                            inline=False)
            embed.add_field(name=help_constants.ADMIN,
                            value=f"Commands for server admins to use.",
                            inline=False)
            embed.add_field(name=help_constants.CIPHER_RACE,
                            value=f"Race against the clock as you decode ciphers. "
                                  f"Use {ctx.prefix}startrace "
                                   "to start a race! "
                                  f"\nRead more on the [GitHub README]({help_constants.CIPHER_RACE_README})",
                            inline=False)
            embed.add_field(name=help_constants.CHANNEL_MANAGEMENT,
                            value=f"Clone, Create, and Move discord channels! For approved users only."
                                  f"\nRead more on the [GitHub README]({help_constants.CHANNEL_MANAGEMENT_README})",
                            inline=False)
            embed.add_field(name=help_constants.SOLVED,
                            value=f"Mark a channel as solved! This will prepend 'solved' to the channel name. "
                                  f"Use {ctx.prefix}solved in a channel to mark it as solved!"
                                  f"\nRead more on the [GitHub README]({help_constants.SOLVED_README})",
                            inline=False)
            embed.add_field(name=help_constants.ARCHIVE_CHANNEL,
                            value=f"Download the contents of a channel in a zip file! For bot mods only."
                                  f"\nRead more on the [GitHub README]({help_constants.ARCHIVE_CHANNEL_README})",
                            inline=False)
            embed.add_field(name=help_constants.LOOKUP,
                            value=f"Search the interwebs (google)!\n"
                                  f"Read more on the [GitHub README]({help_constants.LOOKUP_README})",
                            inline=False)
            embed.add_field(name=help_constants.TIME,
                            value=f"Current time anywhere in the world!\n"
                                  f"Read more on the [GitHub README]({help_constants.TIME_README})",
                            inline=False)
        else:
            module = ' '.join(args).lower()
            if module in MODULE_TO_HELP:
                embed = MODULE_TO_HELP[module](ctx.prefix)
            else:
                embed = discord_utils.create_embed()
                embed.add_field(name="Module not found!",
                                value=f"Sorry! Cannot find module {module}. The modules we have are \n"
                                      f"{', '.join(help_constants.MODULES)}",
                                inline=False)
        await ctx.send(embed=embed)

def admin_help(prefix: str):
    embed = discord.Embed(title=f"{help_constants.ADMIN} {help_constants.HELP}",
                          url=help_constants.ADMIN_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{prefix}setprefix",
                    value=f"Sets the prefix for the server.\n"
                          f"e.g. {prefix}setprefix ~",
                    inline=False)
    return embed

def cipher_race_help(prefix: str):
    embed = discord.Embed(title=f"{help_constants.CIPHER_RACE} {help_constants.HELP}",
                          url=help_constants.CIPHER_RACE_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{prefix}startrace",
                    value=f"Starts a race!\n"
                          f"Optional: choose a wordlist (from {', '.join(code_constants.SHEETS)})\n"
                          f"e.g. {prefix}startrace {code_constants.COMMON}",
                    inline=False)
    embed.add_field(name=f"{prefix}answer <your_answer>",
                    value=f"Answer any of the codes during a race! If you are correct, the bot will react with "
                          f"a {code_constants.CORRECT_EMOJI}. Otherwise, it will react with a {code_constants.INCORRECT_EMOJI}",
                    inline=False)
    embed.add_field(name=f"{prefix}practice",
                    value=f"Get a randomly selected word and cipher to decode at your own pace!\n"
                          f"Optional: Choose a cipher from {', '.join(code_constants.CIPHERS)}\n"
                          f"e.g. {prefix}practice {code_constants.PIGPEN}\n"
                          f"Optional: Choose a sheet from {', '.join(code_constants.SHEETS)}\n"
                          f"e.g. {prefix}practice {code_constants.MORSE} {code_constants.CHALLENGE}\n"
                          f"If you supply a sheet, you *must* supply a cipher first (i.e. order matters!)\n"
                          f"Note: the bot will NOT check your answer. When you've solved, check it yourself by "
                          f"uncovering the spoiler text next to the image!",
                    inline=False)
    embed = more_help(embed, help_constants.CIPHER_RACE_README)
    #TODO: Add reload and reset?
    return embed


def channel_management_help(prefix: str):
    embed = discord.Embed(title=f"{help_constants.CHANNEL_MANAGEMENT} {help_constants.HELP}",
                          url=help_constants.CHANNEL_MANAGEMENT_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{prefix}clone-channel <#cloned-channel> <new-channel-name>",
                    value=f"Create a new channel with the same permissions as #cloned-channel",
                    inline=False)
    embed.add_field(name=f"{prefix}createchannel <channel_name>",
                    value=f"Create a channel named <channel_name> in the same category as the one you're currently in!",
                    inline=False)
    embed.add_field(name=f"{prefix}movechannel <category_name>",
                    value=f"Moves the channel you're currently in to <category_name>",
                    inline=False)
    embed = more_help(embed, help_constants.CHANNEL_MANAGEMENT_README)
    return embed


def solved_help(prefix: str):
    embed = discord.Embed(title=f"{help_constants.SOLVED} {help_constants.HELP}",
                          url=help_constants.SOLVED_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{prefix}solved",
                    value=f"Prepends 'solved' to the channel name you're currently in!",
                    inline=False)
    embed.add_field(name=f"{prefix}unsolved",
                    value=f"Removes the prefix (if applicable) to the channel name you're currently in!",
                    inline=False)
    embed.add_field(name=f"{prefix}solvedish",
                    value=f"Prepends 'solvedish' to the channel name you're currently in!",
                    inline=False)
    embed.add_field(name=f"{prefix}backsolved",
                    value=f"Prepends 'backsolved' to the channel name you're currently in!",
                    inline=False)
    embed = more_help(embed, help_constants.SOLVED_README)
    return embed


def archive_channel_help(prefix: str):
    embed = discord.Embed(title=f"{help_constants.ARCHIVE_CHANNEL} {help_constants.HELP}",
                          url=help_constants.ARCHIVE_CHANNEL_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{prefix}archivechannel <channel_name_or_id>",
                    value=f"Archives a channel! Gathers the chat history into a txt file, and compreses all attachments "
                          f"into a zip file.\n"
                          f"If you're in the same server as the channel you want to archive, you can use #channel_name. "
                          f"Otherwise, you need the channel ID.\n"
                          f"Note: Zips over 8MB will exceed discord's max file size. In that case, bot will only send the chat log.",
                    inline=False)
    embed.add_field(name=f"{prefix}archivecategory <category_name_or_id>",
                    value=f"Archives a category! Will create a separate archive for each text channel.\n"
                          f"*Whispers* It just uses {prefix}archivechannel for each text "
                          f"channel in the category.",
                    inline=False)
    embed = more_help(embed, help_constants.ARCHIVE_CHANNEL_README)
    return embed


def lookup_help(prefix: str):
    embed = discord.Embed(title=f"{help_constants.LOOKUP} {help_constants.HELP}",
                          url=help_constants.LOOKUP_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{prefix}search <target_site> <query>",
                    value=f"Search the interwebs!\n"
                          f"<target_site> must match ({', '.join(list(lookup_constants.REGISTERED_SITES.keys()))}) or "
                          f"be a domain name (e.g. 'khanacademy').\n"
                          f"e.g. {prefix}search hp kevin entwhistle\n"
                          f"{prefix}search kaspersky cryptography",
                    inline=False)
    embed = more_help(embed, help_constants.LOOKUP_README)
    return embed


def time_help(prefix: str):
    embed = discord.Embed(title=f"{help_constants.TIME} {help_constants.HELP}",
                          url=help_constants.TIME_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{prefix}time <location>",
                    value=f"Find the time zone and current time anywhere in the world!\n"
                          f"e.g. {prefix}time New York City",
                    inline=False)
    embed = more_help(embed, help_constants.TIME_README)
    return embed


def more_help(embed, readme_link):
    return embed.add_field(name=f"More {help_constants.HELP}",
                           value=f"Want to know more? Check out the [GitHub README]({readme_link})",
                           inline=False)


MODULE_TO_HELP = {
    help_constants.ADMIN.lower(): admin_help,
    help_constants.CIPHER_RACE.lower(): cipher_race_help,
    help_constants.CHANNEL_MANAGEMENT.lower(): channel_management_help,
    help_constants.SOLVED.lower(): solved_help,
    help_constants.ARCHIVE_CHANNEL.lower(): archive_channel_help,
    help_constants.LOOKUP.lower(): lookup_help,
    help_constants.TIME.lower(): time_help
}


def setup(bot):
    bot.add_cog(HelpCog(bot))