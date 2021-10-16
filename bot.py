from dotenv.main import load_dotenv
load_dotenv(override=True)
import os
import discord
from discord.ext import commands
from utils import admin_utils, google_utils, database_utils
import constants
from sqlalchemy import text, insert
from sqlalchemy.orm import Session


def get_prefix(client, message):
    # Check if in new server or DM
    if message.guild is not None or message.guild.id in constants.PREFIXES:
        return constants.PREFIXES[message.guild.id]
    else:
        return constants.DEFAULT_BOT_PREFIX


# TODO: Move these to better locations
constants.PREFIXES = admin_utils.get_prefixes()
constants.VERIFIEDS = admin_utils.get_verifieds()


def main():
    intents = discord.Intents.default()
    intents.members = True
    client = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None, case_insensitive=True)

    # Get the modules of all cogs whose directory structure is modules/<module_name>/cog.py
    for folder in os.listdir("modules"):
        if os.path.exists(os.path.join("modules", folder, "cog.py")):
            client.load_extension(f"modules.{folder}.cog")


    @client.event
    async def on_ready():
        """When the bot starts up"""
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="you solve👀 |~help"))
        # Keep a database of all the servers the bot is in and what command prefix to use for them.
        with Session(constants.DATABASE_ENGINE) as session:
            for guild in client.guilds:
                result = session.query(database_utils.Prefixes).filter_by(server_id=guild.id).first()
                if result is None:
                    prefix = constants.DEFAULT_BOT_PREFIX
                    stmt = insert(database_utils.Prefixes).values(server_id=guild.id,
                                                                  server_name=guild.name,
                                                                  prefix=prefix)
                    session.execute(stmt)
                    session.commit()
                else:
                    prefix = result.prefix

                print(f"{client.user.name} has connected to the following guild: "
                    f"{guild.name} (id: {guild.id}) with prefix {prefix}")

    # TODO: This function will respond to the user when the bot gets pinged, letting the user know it's prefix
    # TODO: Is there a way we can toggle it on/off?
    # @client.event
    # async def on_message(message):
        # """On mention, state the bot's prefix for the server"""
        # if client.user.mentioned_in(message):
            # print("I have been mentioned")
            # cell = prefix_sheet.find(str(message.guild.id))
            # pre = prefix_sheet.cell(cell.row, cell.col+1).value
            # embed = discord_utils.create_embed()
            # embed.add_field(name="Prefix",
            #                 value=f"My prefix in this server is \"{pre}\". Use {pre}help "
            #                       f"to learn about my commands!",
            #                 inline=False)
            # await message.channel.send(embed=embed)

        # await client.process_commands(message)

    client.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
    # with Session(constants.DATABASE_ENGINE) as session:
    #     result = session.execute(text("SELECT * FROM verifieds where server_id=820327073213186079"))
    #     for row in result:
    #         print(f"Verified role ids: {row['role_id']}")
    #     rows = session.query(database_utils.Verifieds).all()
    #     for row in rows:
    #         print(f"Verified role name: {row.role_name}")
    #     from sqlalchemy import insert
    #     stmt = insert(database_utils.Verifieds).values(role_id=843661971323879424, role_name="Potato Farmer", server_id=470251021554286602, server_name="Soni's Server", category="Tester")
    #     session.execute(stmt)
    #     session.commit()
    #     rows = session.query(database_utils.Verifieds).all()
    #     for row in rows:
    #         print(f"Verified role name: {row.role_name}")
    main()
