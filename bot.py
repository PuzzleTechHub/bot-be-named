import os
import constants
import sqlalchemy
import nextcord
import random
from nextcord.ext import commands
from sqlalchemy import insert
from sqlalchemy.orm import Session

from dotenv.main import load_dotenv

load_dotenv(override=True)

import database  # noqa: E402
from utils import logging_utils, discord_utils  # noqa: E402


def get_prefix(client, message):
    """Gets prefix for the bot"""
    # Check if in new server or DM
    if message.guild is not None and message.guild.id in database.PREFIXES:
        return database.PREFIXES[message.guild.id]
    else:
        return constants.DEFAULT_BOT_PREFIX


def main():
    intents = nextcord.Intents.default()
    intents.members = True
    intents.message_content = True
    client = commands.Bot(
        command_prefix=get_prefix,
        intents=intents,
        help_command=None,
        case_insensitive=True,
    )

    # Get the modules of all cogs whose directory structure is modules/<module_name>/cog.py
    for folder in os.listdir("modules"):
        if os.path.exists(os.path.join("modules", folder, "cog.py")):
            client.load_extension(f"modules.{folder}.cog")

    @client.event
    async def on_ready():
        """When the bot starts up"""
        logging_utils.print_with_timestamp("Bot is ready")
        await logging_utils.open_session()
        await client.change_presence(
            activity=nextcord.Activity(
                type=nextcord.ActivityType.watching, name="you solve👀 | ~about"
            )
        )
        for guild in client.guilds:
            if guild.id not in database.PREFIXES:
                database.PREFIXES[guild.id] = constants.DEFAULT_BOT_PREFIX
                # Add default prefix to DB
                with Session(database.DATABASE_ENGINE) as session:
                    stmt = sqlalchemy.insert(database.Prefixes).values(
                        server_id=guild.id,
                        server_name=guild.name,
                        prefix=constants.DEFAULT_BOT_PREFIX,
                    )
                    session.execute(stmt)
                    session.commit()
            logging_utils.print_with_timestamp(
                f"{client.user.name} has connected to the following guild: "
                f"{guild.name} (id: {guild.id}) with prefix {database.PREFIXES[guild.id]}"
            )
            # Make sure there are at least empty entries for VERIFIEDS, and CUSTOM_COMMANDS for every guild we're in
            if guild.id not in database.VERIFIEDS:
                database.VERIFIEDS[guild.id] = []
            if guild.id not in database.TRUSTEDS:
                database.TRUSTEDS[guild.id] = []
            if guild.id not in database.SOLVERS:
                database.SOLVERS[guild.id] = []
            if guild.id not in database.TESTERS:
                database.TESTERS[guild.id] = []
            if guild.id not in database.CUSTOM_COMMANDS:
                database.CUSTOM_COMMANDS[guild.id] = {}
        # Populate default command list
        for command in client.commands:
            constants.DEFAULT_COMMANDS.append(command.qualified_name.lower())
            for alias in command.aliases:
                constants.DEFAULT_COMMANDS.append(alias.lower())

    @client.event
    async def on_guild_join(guild: nextcord.Guild):
        """When the bot joins a new guild, add it to the database for prefixes"""
        logging_utils.print_with_timestamp(f"Joining {guild} -- Hi!")
        with Session(database.DATABASE_ENGINE) as session:
            stmt = insert(database.Prefixes).values(
                server_id=guild.id,
                server_name=guild.name,
                prefix=constants.DEFAULT_BOT_PREFIX,
            )
            session.execute(stmt)
            session.commit()
        database.PREFIXES[guild.id] = constants.DEFAULT_BOT_PREFIX
        database.VERIFIEDS[guild.id] = []
        database.TRUSTEDS[guild.id] = []
        database.SOLVERS[guild.id] = []
        database.TESTERS[guild.id] = []
        database.CUSTOM_COMMANDS[guild.id] = {}

    @client.event
    async def on_guild_remove(guild: nextcord.Guild):
        """When the bot leaves a guild, remove all database entries pertaining to that guild"""
        logging_utils.print_with_timestamp(f"Leaving {guild} -- Bye bye!")
        with Session(database.DATABASE_ENGINE) as session:
            session.query(database.CustomCommands).filter_by(
                server_id=guild.id
            ).delete()
            session.commit()
            session.query(database.Prefixes).filter_by(server_id=guild.id).delete()
            session.commit()
            session.query(database.Verifieds).filter_by(server_id=guild.id).delete()
            session.commit()
            session.query(database.SheetTethers).filter_by(server_id=guild.id).delete()
            session.commit()
            session.query(database.SummaryGrants).filter_by(server_id=guild.id).delete()
            session.commit()
        database.PREFIXES.pop(guild.id)
        database.VERIFIEDS.pop(guild.id)
        database.TRUSTEDS.pop(guild.id)
        database.CUSTOM_COMMANDS.pop(guild.id)

    @client.event
    async def on_guild_role_delete(role: nextcord.Role):
        """When a role is deleted, remove the summary grants"""
        with Session(database.DATABASE_ENGINE) as session:
            session.query(database.SummaryGrants).filter_by(role_id=role.id).delete()
            session.commit()

    @client.event
    async def on_guild_channel_delete(channel: nextcord.abc.GuildChannel):
        """When a channel is deleted, remove its summary grants"""
        with Session(database.DATABASE_ENGINE) as session:
            session.query(database.SummaryGrants).filter_by(
                channel_id=channel.id
            ).delete()
            session.commit()

    @client.event
    async def on_message(message: nextcord.Message):
        # We only want to respond to user messages
        if message.is_system() or message.author.id == client.user.id:
            return

        command_prefix = get_prefix(client, message)

        if message.clean_content.startswith(command_prefix):
            # If the command is a default one, just run it.
            command_name = message.clean_content.split()[0][
                len(command_prefix) :
            ].lower()
            if command_name in constants.DEFAULT_COMMANDS:
                await client.process_commands(message)
            # Don't use custom commands for DMs also I think this fixes a bug which gets an error when someone
            # uses a command right as the box is starting up.
            elif (
                message.guild is not None
                and message.guild.id in database.CUSTOM_COMMANDS
            ):
                # Check the cache for this server's custom command first, then look for the global one.
                # Each entry is (command_return, is_image, responses). TODO: make it a class
                custom_command = database.CUSTOM_COMMANDS[message.guild.id].get(
                    command_name
                ) or database.CUSTOM_COMMANDS.get(constants.DB_GLOBAL, {}).get(
                    command_name
                )

                # Find it in the DB if it's not in the cache
                if custom_command is None:
                    with Session(database.DATABASE_ENGINE) as session:
                        # Check in this server
                        result = (
                            session.query(database.CustomCommands)
                            .filter_by(
                                server_id_command=f"{message.guild.id} {command_name}"
                            )
                            .first()
                        )
                        # Check for global custom commands
                        if result is None:
                            result = (
                                session.query(database.CustomCommands)
                                .filter_by(
                                    server_id_command=f"{constants.DB_GLOBAL} {command_name}"
                                )
                                .first()
                            )
                        # Not a custom command found in the DB either
                        if result is None:
                            return
                        custom_command = (
                            result.command_return,
                            result.image,
                            result.responses,
                        )

                        # Add to cache under the id it was found under
                        database.CUSTOM_COMMANDS.setdefault(result.server_id, {})[
                            command_name
                        ] = custom_command

                command_return, is_image, responses = custom_command

                # If it has random responses, pick one of them
                if responses:
                    command_return = random.choice(responses)

                # Image, so use normal text
                if is_image:
                    await message.channel.send(command_return)

                # Non-image, so use embed
                else:
                    embed = nextcord.Embed(
                        description=command_return, color=constants.EMBED_COLOR
                    )
                    await message.channel.send(embed=embed)

    client.run(os.getenv("DISCORD_TOKEN"))

    @client.event
    async def on_close():
        await logging_utils.close_session()

    @client.event
    async def on_command_error(self, ctx, error):
        """Intercept ~help a_custom_command errors"""
        if isinstance(error, commands.CommandNotFound):
            command_name = str(ctx.invoked_with).lower() if ctx.invoked_with else None

            if command_name:
                if ctx.guild and command_name in database.CUSTOM_COMMANDS.get(
                    ctx.guild.id, {}
                ):
                    embed = discord_utils.create_embed()
                    embed.add_field(
                        name="Thats a custom command!",
                        value=f'The command "{command_name}" is a custom command created for this server! '
                        f"Use `~help Custom Commands` to see how they work!"
                        f"Your custom command response is: {database.CUSTOM_COMMANDS[ctx.guild.id][command_name]}",
                        inline=False,
                    )
                    await discord_utils.send_message(ctx, embed)
                    return
        # If not a custom command, let the error propagate normally
        # TODO global custom commands


if __name__ == "__main__":
    main()
