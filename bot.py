from dotenv.main import load_dotenv
load_dotenv(override=True)
import os
import discord
from discord.ext import commands
from utils import admin_utils, database_utils, discord_utils
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
                prefix_result = session.query(database_utils.Prefixes)\
                                .filter_by(server_id=guild.id)\
                                .first()
                if prefix_result is None:
                    prefix = constants.DEFAULT_BOT_PREFIX
                    stmt = insert(database_utils.Prefixes).values(server_id=guild.id,
                                                                  server_name=guild.name,
                                                                  prefix=prefix)
                    session.execute(stmt)
                    session.commit()
                else:
                    prefix = prefix_result.prefix

                print(f"{client.user.name} has connected to the following guild: "
                    f"{guild.name} (id: {guild.id}) with prefix {prefix}")

                constants.CUSTOM_COMMANDS[guild.id] = {}
                custom_command_result = session.query(database_utils.CustomCommmands)\
                                    .filter_by(server_id=guild.id)\
                                    .all()
                if custom_command_result is not None:
                    for custom_command in custom_command_result:
                        # Populate custom command dict
                        constants.CUSTOM_COMMANDS[guild.id][custom_command.command_name] = (custom_command.command_return, custom_command.image)
        # Populate default command list
        for command in client.commands:
            constants.DEFAULT_COMMANDS.append(command.qualified_name)
            for alias in command.aliases:
                constants.DEFAULT_COMMANDS.append(alias)
                    

    @client.event
    async def on_message(message: discord.Message): 
        # If the message doesn't start with the command prefix, no use querying the db.
        command_prefix = constants.PREFIXES[message.guild.id]
        if message.clean_content.startswith(command_prefix):
            # If the command is a default one, just run it.
            command_name = message.clean_content.split()[0][len(command_prefix):]
            if command_name in constants.DEFAULT_COMMANDS:
                await client.process_commands(message)
            elif message.guild is not None:
                # TODO: Can I just use constants.CUSTOM_COMMANDS
                if command_name in constants.CUSTOM_COMMANDS[message.guild.id]:
                    command_return = constants.CUSTOM_COMMANDS[message.guild.id][command_name][0]
                    # Image, so we use normal text.
                    if constants.CUSTOM_COMMANDS[message.guild.id][command_name][1]:
                        await message.channel.send(command_return)
                    # Non-Image, so use embed.
                    else:
                        embed = discord.Embed(description=command_return,
                                              color=constants.EMBED_COLOR)
                        await message.channel.send(embed=embed)
                    return


    client.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
    main()
