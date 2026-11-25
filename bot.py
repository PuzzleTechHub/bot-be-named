import asyncio
import os
import time
import constants
import nextcord
import random
from nextcord.ext import commands

from dotenv.main import load_dotenv

load_dotenv(override=True)

import database  # noqa: E402
from utils import discord_utils, logging_utils  # noqa: E402


def get_prefix(client, message):
    """Gets prefix for the bot"""
    # Check if in new server or DM
    if message.guild is not None and message.guild.id in database.PREFIXES:
        return database.PREFIXES[message.guild.id]
    else:
        return constants.DEFAULT_BOT_PREFIX


def main():
    database.load_all()

    intents = nextcord.Intents.default()
    intents.members = True
    intents.message_content = True
    client = commands.Bot(
        command_prefix=get_prefix,
        intents=intents,
        help_command=None,
        case_insensitive=True,
        # Everyone in BOT_OWNER_DISCORD_ID will have bot owner permissions
        owner_ids=set(discord_utils.bot_owner_ids()) or None,
        # Don't wait for member lists at startup, on_ready fetches them in the background
        chunk_guilds_at_startup=False,
    )
    background_tasks = set()

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
            # Default prefix for new servers, and empty role and custom command caches
            database.add_server(guild.id, guild.name)
            logging_utils.print_with_timestamp(
                f"{client.user.name} has connected to the following guild: "
                f"{guild.name} (id: {guild.id}) with prefix {database.PREFIXES[guild.id]}"
            )
        # Populate default command list
        for command in client.commands:
            constants.DEFAULT_COMMANDS.append(command.qualified_name.lower())
            for alias in command.aliases:
                constants.DEFAULT_COMMANDS.append(alias.lower())

        # on_ready can fire again after a reconnect, make sure only one fetch runs at a time
        if not background_tasks:
            task = asyncio.create_task(fetch_all_members(list(client.guilds)))
            # Keep a reference so the task isn't garbage collected
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)

    async def fetch_all_members(guilds):
        """Fetch every guild's member list in the background, after on_ready"""
        start = time.monotonic()
        failed = await discord_utils.chunk_all_guilds(guilds)
        logging_utils.print_with_timestamp(
            f"Fetched member lists for {len(guilds) - len(failed)}/{len(guilds)} guilds "
            f"in {time.monotonic() - start:.1f} s"
            + (f". Failed: {', '.join(g.name for g in failed)}" if failed else "")
        )

    @client.event
    async def on_guild_join(guild: nextcord.Guild):
        """When the bot joins a new guild, add it to the database for prefixes"""
        logging_utils.print_with_timestamp(f"Joining {guild} -- Hi!")
        database.add_server(guild.id, guild.name)

    @client.event
    async def on_guild_remove(guild: nextcord.Guild):
        """When the bot leaves a guild, remove all database entries pertaining to that guild"""
        logging_utils.print_with_timestamp(f"Leaving {guild} -- Bye bye!")
        database.delete_server_data(guild.id)

    @client.event
    async def on_guild_role_delete(role: nextcord.Role):
        """When a role is deleted, remove the summary grants"""
        database.delete_role_summary_grants(role.id)

    @client.event
    async def on_guild_channel_delete(channel: nextcord.abc.GuildChannel):
        """When a channel is deleted, remove its summary grants, solve streams and channel mirrors"""
        database.delete_channel_summary_grants(channel.id)
        database.delete_channel_solve_streams(channel.id)
        database.delete_channel_mirrors_for(channel.id)

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
                    custom_command = database.find_custom_command(
                        message.guild.id, command_name
                    )
                    # Not a custom command found in the DB either
                    if custom_command is None:
                        return

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

    @client.before_invoke
    async def log_command(ctx: commands.Context):
        """Log every command in the console/webhook, just before it runs and after the checks pass."""
        await logging_utils.log_command(
            ctx.command.qualified_name, ctx.guild, ctx.channel, ctx.author
        )

    @client.event
    async def on_close():
        await logging_utils.close_session()

    client.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()
