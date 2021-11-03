from dotenv.main import load_dotenv
import sqlalchemy
load_dotenv(override=True)
import os
import discord
from discord.ext import commands
from utils import database_utils
import constants
from sqlalchemy import text, insert
from sqlalchemy.orm import Session


def get_prefix(client, message):
    # Check if in new server or DM
    if message.guild is not None and message.guild.id in database_utils.PREFIXES:
        return database_utils.PREFIXES[message.guild.id]
    else:
        return constants.DEFAULT_BOT_PREFIX


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
        for guild in client.guilds:
            if guild.id not in database_utils.PREFIXES:
                database_utils.PREFIXES[guild.id] = constants.DEFAULT_BOT_PREFIX
                # Add default prefix to DB
                with Session(database_utils.DATABASE_ENGINE) as session:
                    stmt = sqlalchemy.insert(database_utils.Prefixes).values(server_id=guild.id,
                                                                             server_name=guild.name,
                                                                             prefix=constants.DEFAULT_BOT_PREFIX)
                    session.execute(stmt)
                    session.commit()
            print(f"{client.user.name} has connected to the following guild: "
                  f"{guild.name} (id: {guild.id} with prefix {database_utils.PREFIXES[guild.id]}")
            # Make sure there are at least empty entries for VERIFIEDS, and CUSTOM_COMMANDS for every guild we're in
            if guild.id not in database_utils.VERIFIEDS:
                database_utils.VERIFIEDS[guild.id] = []
            if guild.id not in database_utils.CUSTOM_COMMANDS:
                database_utils.CUSTOM_COMMANDS[guild.id] = {}
        # Populate default command list
        for command in client.commands:
            constants.DEFAULT_COMMANDS.append(command.qualified_name.lower())
            for alias in command.aliases:
                constants.DEFAULT_COMMANDS.append(alias.lower())

    @client.event
    async def on_guild_join(guild: discord.Guild):
        """When the bot joins a new guild, add it to the database for prefixes"""
        print("Joining {guild} -- Hi!")
        with Session(database_utils.DATABASE_ENGINE) as session:
            stmt = insert(database_utils.Prefixes).values(server_id=guild.id,
                                                          server_name=guild.name,
                                                          prefix=constants.DEFAULT_BOT_PREFIX)
            session.execute(stmt)
            session.commit()
        database_utils.PREFIXES[guild.id] = constants.DEFAULT_BOT_PREFIX
        database_utils.VERIFIEDS[guild.id] = []
        database_utils.CUSTOM_COMMANDS[guild.id] = {}

    @client.event
    async def on_guild_remove(guild: discord.Guild):
        """When the bot leaves a guild, remove all database entries pertaining to that guild"""
        print("Leaving {guild} -- Bye bye!")
        with Session(database_utils.DATABASE_ENGINE) as session:
            session.query(database_utils.CustomCommmands)\
                   .filter_by(server_id=guild.id)\
                   .delete()
            session.commit()
            session.query(database_utils.Prefixes)\
                   .filter_by(server_id=guild.id)\
                   .delete()
            session.commit()
            session.query(database_utils.Verifieds)\
                   .filter_by(server_id=guild.id)\
                   .delete()
            session.commit()
        database_utils.PREFIXES.pop(guild.id)
        database_utils.VERIFIEDS.pop(guild.id)
        database_utils.CUSTOM_COMMANDS.pop(guild.id)

    @client.event
    async def on_message(message: discord.Message): 
        # If the message doesn't start with the command prefix, no use querying the db.
        if message.guild is not None:
            command_prefix = database_utils.PREFIXES[message.guild.id]  
        else:
            command_prefix = constants.DEFAULT_BOT_PREFIX

        if message.clean_content.startswith(command_prefix):
            # If the command is a default one, just run it.
            command_name = message.clean_content.split()[0][len(command_prefix):].lower()
            if command_name in constants.DEFAULT_COMMANDS:
                await client.process_commands(message)
            # Don't use custom commands for DMs also I think this fixes a bug which gets an error when someone
            # uses a command right as the box is starting up.
            elif message.guild is not None and message.guild.id in database_utils.CUSTOM_COMMANDS:
                # check if custom command is in cache. If it's not, query the DB for it
                if command_name in [command.lower() for command in database_utils.CUSTOM_COMMANDS[message.guild.id].keys()]:
                    command_return = database_utils.CUSTOM_COMMANDS[message.guild.id][command_name][0]
                    # Image, so we use normal text.
                    if database_utils.CUSTOM_COMMANDS[message.guild.id][command_name][1]:
                        await message.channel.send(command_return)
                    # Non-Image, so use embed.
                    else:
                        embed = discord.Embed(description=command_return,
                                              color=constants.EMBED_COLOR)
                        await message.channel.send(embed=embed)
                    return
                # If the custom command is not in the cache, query the DB to see if we have a command with that name for this server
                else:
                    with Session(database_utils.DATABASE_ENGINE) as session:
                        result = session.query(database_utils.CustomCommmands)\
                                        .filter_by(server_id_command=f"{message.guild.id} {command_name}")\
                                        .first()
                        if result is not None:
                            if result.image:
                                await message.channel.send(result.command_return)
                            else:
                                embed = discord.Embed(description=result.command_return,
                                              color=constants.EMBED_COLOR)
                                await message.channel.send(embed=embed)
                            database_utils.CUSTOM_COMMANDS[message.guild.id][command_name] = (result.command_return, result.image)

    client.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
    main()
