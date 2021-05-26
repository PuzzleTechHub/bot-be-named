from discord.ext import commands
import constants
import discord
from utils import discord_utils, admin_utils
from modules.help import help_constants
from modules.lookup import lookup_constants
from modules.cipher_race import cipher_race_constants

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
            embed.add_field(name=constants.ADMIN,
                            value=f"Commands for server admins to use.",
                            inline=False)
            embed.add_field(name=constants.CIPHER_RACE,
                            value=f"Race against the clock as you decode ciphers. "
                                  f"Use {ctx.prefix}startrace "
                                   "to start a race! "
                                  f"\nRead more on the [GitHub README]({help_constants.CIPHER_RACE_README})",
                            inline=False)
            embed.add_field(name=constants.CHANNEL_MANAGEMENT,
                            value=f"Clone, Create, and Move discord channels! For approved users only."
                                  f"\nRead more on the [GitHub README]({help_constants.CHANNEL_MANAGEMENT_README})",
                            inline=False)
            embed.add_field(name=constants.DISCORD,
                            value=f"Discord utility commands like pinning and getting server stats."
                                  f"\nRead more on the [GitHub README]({help_constants.DISCORD_README})",
                            inline=False)
            embed.add_field(name=constants.SOLVED,
                            value=f"Mark a channel as solved! This will prepend 'solved' to the channel name. "
                                  f"Use {ctx.prefix}solved in a channel to mark it as solved!"
                                  f"\nRead more on the [GitHub README]({help_constants.SOLVED_README})",
                            inline=False)
            embed.add_field(name=constants.ARCHIVE,
                            value=f"Download the contents of a channel in a zip file! For bot mods only."
                                  f"\nRead more on the [GitHub README]({help_constants.ARCHIVE_README})",
                            inline=False)
            embed.add_field(name=constants.LOOKUP,
                            value=f"Search the interwebs (google)!\n"
                                  f"Read more on the [GitHub README]({help_constants.LOOKUP_README})",
                            inline=False)
            embed.add_field(name=constants.TIME,
                            value=f"Current time anywhere in the world!\n"
                                  f"Read more on the [GitHub README]({help_constants.TIME_README})",
                            inline=False)
            embed.add_field(name=constants.SHEETS,
                            value=f"GSheet management from Discord.\n"
                                  f"Read more on the [GitHub README]({help_constants.SHEETS_README})",
                            inline=False)
        else:
            module = ' '.join(args).lower()
            if module in MODULE_TO_HELP:
                embed = MODULE_TO_HELP[module](ctx.prefix)
            else:
                embed = discord_utils.create_embed()
                embed.add_field(name="Module not found!",
                                value=f"Sorry! Cannot find module {module}. The modules we have are \n"
                                      f"{', '.join(constants.MODULES)}",
                                inline=False)
        await ctx.send(embed=embed)

    @admin_utils.is_owner_or_admin()
    @commands.command(name="adminhelp")
    async def adminhelp(self, ctx):
        embed = discord.Embed(title=f"Admin {help_constants.HELP}",
                              url="https://github.com/kevslinger/DiscordCipherRace",
                              color=constants.EMBED_COLOR)
        # reload, reset, setprefix, createrole, deleterole
        embed.add_field(name=f"{ctx.prefix}addrole rolename (Optional: color, pingable)",
                        value=f"Create a new role (also: createrole)\n"
                              f"Can add color in hex code, e.g. \n"
                              f"{ctx.prefix}addrole myrole 1b2f3e\n"
                              f"Can additionally include whether or not to allow pings (True or False), defaults to True e.g.\n"
                              f"{ctx.prefix}createrole myrole 0x1b2f3e False",
                        inline=False)
        embed.add_field(name=f"{ctx.prefix}assignrole rolename <user1> <user2> ...",
                        value=f"Assign role to user(s) (also: giverole). Must @ the user(s), but rolename can be "
                              f"just the name. If role does not exist, bot will create it. e.g.\n"
                              f"{ctx.prefix}giverole potato @user1 @user2",
                        inline=False)
        embed.add_field(name=f"{ctx.prefix}deleterole rolename",
                        value=f"Delete role with given name (also: removerole, rmrole). Can use the role's mention (i.e. @), too, e.g.\n"
                              f"{ctx.prefix}deleterole myrole, {ctx.prefix}rmrole @myrole",
                        inline=False)
        embed.add_field(name=f"{ctx.prefix}reload",
                        value=f"Used in Cipher race. Reloads the wordlists (used if you want to add/modify/remove words.\n"
                              f"Note: Bot reloads automatically every 24 hours.",
                        inline=False)
        embed.add_field(name=f"{ctx.prefix}setprefix",
                        value=f"Set the bot prefix to be used in the server. Currently is {ctx.prefix} in {ctx.guild.name}. e.g.\n"
                              f"{ctx.prefix}setprefix !",
                        inline=False)
        await ctx.send(embed=embed)

#########################################
# Module-Specific help helper functions #
#########################################

def admin_help(prefix: str):
    embed = discord.Embed(title=f"{constants.ADMIN} {help_constants.HELP}",
                          url=help_constants.ADMIN_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{prefix}setprefix",
                    value=f"Sets the prefix for the server.\n"
                          f"e.g. {prefix}setprefix ~",
                    inline=False)
    return embed

def cipher_race_help(prefix: str):
    embed = discord.Embed(title=f"{constants.CIPHER_RACE} {help_constants.HELP}",
                          url=help_constants.CIPHER_RACE_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{prefix}startrace",
                    value=f"Starts a race!\n"
                          f"Optional: choose a wordlist (from {', '.join(cipher_race_constants.SHEETS)})\n"
                          f"e.g. {prefix}startrace {cipher_race_constants.COMMON}",
                    inline=False)
    embed.add_field(name=f"{prefix}answer <your_answer>",
                    value=f"Answer any of the codes during a race! If you are correct, the bot will react with "
                          f"a {cipher_race_constants.CORRECT_EMOJI}. Otherwise, it will react with a {cipher_race_constants.INCORRECT_EMOJI}",
                    inline=False)
    embed.add_field(name=f"{prefix}practice",
                    value=f"Get a randomly selected word and cipher to decode at your own pace!\n"
                          f"Optional: Choose a cipher from {', '.join(cipher_race_constants.CIPHERS)}\n"
                          f"e.g. {prefix}practice {cipher_race_constants.PIGPEN}\n"
                          f"Optional: Choose a sheet from {', '.join(cipher_race_constants.SHEETS)}\n"
                          f"e.g. {prefix}practice {cipher_race_constants.MORSE} {cipher_race_constants.CHALLENGE}\n"
                          f"If you supply a sheet, you *must* supply a cipher first (i.e. order matters!)\n"
                          f"Note: the bot will NOT check your answer. When you've solved, check it yourself by "
                          f"uncovering the spoiler text next to the image!",
                    inline=False)
    embed = more_help(embed, help_constants.CIPHER_RACE_README)
    #TODO: Add reload and reset?
    return embed


def channel_management_help(prefix: str):
    embed = discord.Embed(title=f"{constants.CHANNEL_MANAGEMENT} {help_constants.HELP}",
                          url=help_constants.CHANNEL_MANAGEMENT_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{prefix}clone-channel <#cloned-channel> <new-channel-name>",
                    value=f"Create a new channel with the same permissions as #cloned-channel",
                    inline=False)
    embed.add_field(name=f"{prefix}createchannel <channel_name>",
                    value=f"Create a channel named <channel_name> in the same category as the one you're currently in!",
                    inline=False)
    embed.add_field(name=f"{prefix}renamechannel <new_channel_name>",
                    value=f"Renames the current to <new_channel_name>!",
                    inline=False)
    embed.add_field(name=f"{prefix}movechannel <category_name>",
                    value=f"Moves the channel you're currently in to <category_name>",
                    inline=False)
    embed = more_help(embed, help_constants.CHANNEL_MANAGEMENT_README)
    return embed


def discord_help(prefix: str):
    embed = discord.Embed(title=f"{constants.DISCORD} {help_constants.HELP}",
                          url=help_constants.DISCORD_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{prefix}catstats",
                    value="Get category stats!",
                    inline=False)
    embed.add_field(name=f"{prefix}listroles",
                    value="List all the roles in the server",
                    inline=False)
    embed.add_field(name=f"{prefix}pin",
                    value="Pin the previous message! You can also reply to a message with {prefix}pin and the bot will"
                          " pin the message you replied to.",
                    inline=False)
    embed.add_field(name=f"{prefix}pinme",
                    value="Pins the message",
                    inline=False)
    embed.add_field(name=f"{prefix}stats",
                    value="Get server stats!",
                    inline=False),
    embed.add_field(name=f"{prefix}unpin <optional: number_to_unpin (default 1)>",
                    value="Unpins the most recent <number_to_unpin> messages!",
                    inline=False)
    embed = more_help(embed, help_constants.DISCORD_README)
    return embed


def solved_help(prefix: str):
    embed = discord.Embed(title=f"{constants.SOLVED} {help_constants.HELP}",
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


def archive_help(prefix: str):
    embed = discord.Embed(title=f"{constants.ARCHIVE} {help_constants.HELP}",
                          url=help_constants.ARCHIVE_README,
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
    embed = more_help(embed, help_constants.ARCHIVE_README)
    return embed


def lookup_help(prefix: str):
    embed = discord.Embed(title=f"{constants.LOOKUP} {help_constants.HELP}",
                          url=help_constants.LOOKUP_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{prefix}search <target_site> <query>",
                    value=f"Search the interwebs!\n"
                          f"<target_site> must match ({', '.join(list(lookup_constants.REGISTERED_SITES.keys()))}) or "
                          f"be a domain name (e.g. 'khanacademy').\n"
                          f"e.g. {prefix}search hp kevin entwhistle\n"
                          f"{prefix}search kaspersky cryptography",
                    inline=False)
    embed.add_field(name=f"{prefix}google <query>",
                    value="Search google!",
                    inline=False)
    embed.add_field(name=f"{prefix}wikipedia <query>",
                    value=f"Also {prefix}wiki",
                    inline=False)
    embed = more_help(embed, help_constants.LOOKUP_README)
    return embed


def time_help(prefix: str):
    embed = discord.Embed(title=f"{constants.TIME} {help_constants.HELP}",
                          url=help_constants.TIME_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{prefix}time <location>",
                    value=f"Find the time zone and current time anywhere in the world!\n"
                          f"e.g. {prefix}time New York City",
                    inline=False)
    embed = more_help(embed, help_constants.TIME_README)
    return embed

def sheets_help(prefix: str):
    embed = discord.Embed(title=f"{constants.SHEETS} {help_constants.HELP}",
                          url=help_constants.SHEETS_README,
                          color=constants.EMBED_COLOR)
    embed.add_field(name=f"{prefix}tether <string> or channeltether <string>",
                    value=f"Connects the current category/channel to a GSheet with <string> ID or link\n"
                          f"Either of these commands are necessary before the other sheet commands\n"
                          f"e.g. {prefix}tether 1ZuOT4g8nGTrJrBvuknTIHWfLhmUzuquQtAKLCIdsLt4",
                    inline=False)
    embed.add_field(name=f"{prefix}displaytether",
                    value=f"Links the GSheet connected to current category\n",
                    inline=False)
    embed.add_field(name=f"{prefix}removetether <string>",
                    value=f"Unconnects the current category from the linked GSheet\n",
                    inline=False)
    embed.add_field(name=f"{prefix}sheetcreatetab <Tabname>",
                    value=f"Makes a new tab in the connected GSheet, links it in the current channel and pins it.\n"
                          f"e.g. {prefix}sheetcreatetab Puzzle1",
                    inline=False)
    embed.add_field(name=f"{prefix}channelsheetcreatetab <channel_name> (<links to pin>)",
                    value=f"Makes a new channel in the current category with <channel_name>, then makes a new tab in "
                          f"the connected GSheet with <channel_name>, links it in the new channel and pins it.\n"
                          f"If there's any extra arguments, say link to puzzle, it posts them in new channel and pins them\n"
                          f"e.g. {prefix}channelsheetcreatetab Puzzle1 http://puzzlelink.net",
                    inline=False)
    embed = more_help(embed, help_constants.SHEETS_README)
    return embed


def more_help(embed, readme_link):
    return embed.add_field(name=f"More {help_constants.HELP}",
                           value=f"Want to know more? Check out the [GitHub README]({readme_link})",
                           inline=False)


MODULE_TO_HELP = {
    constants.ADMIN.lower(): admin_help,
    constants.CIPHER_RACE.lower(): cipher_race_help,
    constants.CHANNEL_MANAGEMENT.lower(): channel_management_help,
    constants.DISCORD.lower(): discord_help,
    constants.SOLVED.lower(): solved_help,
    constants.ARCHIVE.lower(): archive_help,
    constants.LOOKUP.lower(): lookup_help,
    constants.TIME.lower(): time_help,
    constants.SHEETS.lower(): sheets_help
}


def setup(bot):
    bot.add_cog(HelpCog(bot))