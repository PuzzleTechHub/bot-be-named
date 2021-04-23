import os
import discord
from discord.ext import commands
from utils import discord_utils
from dotenv.main import load_dotenv
load_dotenv(override=True)
import constants
from utils import google_utils
from gspread.exceptions import CellNotFound
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

gspread_client = google_utils.create_gspread_client()
prefix_sheet = gspread_client.open_by_key(os.getenv('PREFIX_SHEET_KEY')).sheet1

def get_prefix(client, message):
    cell = prefix_sheet.find(str(message.guild.id))

    return prefix_sheet.cell(cell.row, cell.col+1).value


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

    client.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()
