import os
import discord
from discord.ext import commands
from utils import admin_utils, discord_utils, google_utils
from dotenv.main import load_dotenv
load_dotenv(override=True)
import constants
from gspread.exceptions import CellNotFound
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

gspread_client = google_utils.create_gspread_client()
prefix_sheet = gspread_client.open_by_key(os.getenv('MASTER_SHEET_KEY')).worksheet(constants.PREFIX_TAB_NAME)

def get_prefixes():
    prfx = {}
    prefix_list = prefix_sheet.get_all_values()[1:]
    for row in prefix_list:
        prfx[row[1]] = row[2]
    return prfx

PREFIXES = get_prefixes()

def get_prefix(client, message):
    return PREFIXES[str(message.guild.id)]


def main():
    intents = discord.Intents.default()
    client = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

    # Get the modules of all cogs whose directory structure is modules/<module_name>/cog.py
    for folder in os.listdir("modules"):
        if os.path.exists(os.path.join("modules", folder, "cog.py")):
            client.load_extension(f"modules.{folder}.cog")


    @client.event
    async def on_ready():
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="you solve👀 |~help"))
        # Keep a google sheet of all the servers the bot is in and what command prefix to use for them.
        for guild in client.guilds:
            try:
                # Check if the guild is in the sheet.
                cell = prefix_sheet.find(str(guild.id))
                prefix = prefix_sheet.cell(cell.row, cell.col+1).value
            except CellNotFound:
                prefix = constants.DEFAULT_BOT_PREFIX
                prefix_sheet.append_row([guild.name, str(guild.id), prefix])
                print(f"Added {constants.DEFAULT_BOT_PREFIX} as prefix in {guild}")

            print(f"{client.user.name} has connected to the following guild: {guild.name} (id: {guild.id}) with prefix {prefix}")


    @client.event
    async def on_message(message):
        if client.user.mentioned_in(message):
            print("I have been mentioned")
            cell = prefix_sheet.find(str(message.guild.id))
            pre = prefix_sheet.cell(cell.row, cell.col+1).value
            embed = discord_utils.create_embed()
            embed.add_field(name="Prefix",
                            value=f"My prefix in this server is \"{pre}\". Use {pre}help "
                                  f"to learn about my commands!",
                            inline=False)
            await message.channel.send(embed=embed)

        await client.process_commands(message)


    @admin_utils.is_owner_or_admin()
    @client.command(name="setprefix")
    async def setprefix(ctx, prefix: str):
        print("Received setprefix")
        find_cell = prefix_sheet.find(str(ctx.message.guild.id))
        prefix_sheet.update_cell(find_cell.row, find_cell.col+1, prefix)
        PREFIXES[str(ctx.message.guild.id)] = prefix

        embed = discord_utils.create_embed()
        embed.add_field(name=constants.SUCCESS,
                        value=f"Prefix for this server set to {prefix}",
                        inline=False)
        await ctx.send(embed=embed)


    client.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()
