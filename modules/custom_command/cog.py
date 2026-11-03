import database
import constants
import os  # noqa: F401
import asyncio
from typing import Optional
from utils import discord_utils, logging_utils, command_predicates
from nextcord.ext import commands
from sqlalchemy.orm import Session
from sqlalchemy import insert


"""
Custom command module. Allows users to set their own "custom command" of saveable image/embed/messages making a lot of easy to retrieve utility.
"""

RESPONSE_TIMEOUT_SECONDS = 300  # Seconds the bot waits for the next response choice before locking the one it has in


class CustomCommandCog(commands.Cog, name="Custom Commands"):
    """
    Customised commands saved for each server
    """

    def __init__(self, bot):
        self.bot = bot
        self.response_timeout = RESPONSE_TIMEOUT_SECONDS

    async def check_cc_name(self, ctx, command_name, is_global: bool) -> bool:
        """Checks if the command name is free before asking for any responses to fill it with."""
        embed = discord_utils.create_embed()
        if command_name in constants.DEFAULT_COMMANDS:
            embed.add_field(
                name="Failed",
                value=f"Command {command_name} is a default command. Please use a different name.",
            )
            await discord_utils.send_message(ctx, embed)
            return False

        if not is_global and command_name in database.CUSTOM_COMMANDS[ctx.guild.id]:
            command_return, _, responses = database.CUSTOM_COMMANDS[ctx.guild.id][
                command_name
            ]
            embed.add_field(
                name="Failed",
                value=f"The command `{ctx.prefix}{command_name}` already exists in `{ctx.guild.name}` with value{'s' if responses and len(responses) > 1 else ''} "
                f"`{' | '.join(responses or [command_return])}`. If you'd like to replace "
                f"`{ctx.prefix}{command_name}`, please use `{ctx.prefix}editcustomcommand {command_name}`",
            )
            await discord_utils.send_message(ctx, embed)
            return False
        return True

    async def get_responses(self, ctx, command_name, command_return):
        """Returns the response given as a list. If none was given, triggers a method that asks for responses
        one message at a time. Returns None if cancelled."""
        if command_return:
            return [command_return]
        return await self.collect_responses(ctx, command_name)

    async def collect_responses(self, ctx, command_name):
        """Collects responses for a custom command that will be randomly selected out of, until they lock it in.
        Returns None if cancelled."""
        confirm_emoji = "✅"
        abort_emoji = "❌"
        responses = []

        while True:
            embed = discord_utils.create_embed()
            if responses:
                embed.add_field(
                    name=f"Received response {len(responses)}!",
                    value=f"Send another message to add another response to `{ctx.prefix}{command_name}`, "
                    f"or react {confirm_emoji} to lock in the responses. React {abort_emoji} to cancel "
                    "the creation of the custom command.",
                )
            else:
                embed.add_field(
                    name="Waiting for first response...",
                    value=f"Send the first response for `{ctx.prefix}{command_name}`. "
                    f"React {abort_emoji} to cancel.",
                )

            prompt = (await discord_utils.send_message(ctx, embed))[0]
            if responses:
                await prompt.add_reaction(confirm_emoji)
            await prompt.add_reaction(abort_emoji)

            def check_message(message):
                """Checks if the author of a message is the person who called the command in the same channel"""
                return (
                    message.author == ctx.author
                    and message.channel == ctx.channel
                    and not message.content.startswith(ctx.prefix)
                )

            def check_reaction(reaction, user):
                return (
                    reaction.message.id == prompt.id
                    and user == ctx.author
                    and (
                        reaction.emoji == abort_emoji
                        or (responses and reaction.emoji == confirm_emoji)
                    )
                )

            # Wait for whichever comes first, a reaction or an additional response
            message_task = asyncio.create_task(
                self.bot.wait_for("message", check=check_message)
            )
            react_task = asyncio.create_task(
                self.bot.wait_for("reaction_add", check=check_reaction)
            )
            done, pending = await asyncio.wait(
                {message_task, react_task},
                timeout=self.response_timeout,
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()

            final_embed = discord_utils.create_embed()
            # The user timed out...
            if not done:
                if responses:
                    final_embed.add_field(
                        name="Timed out",
                        value=f"Saving the {len(responses)} response{'s' if len(responses) > 1 else ''} into the command!",
                    )
                else:
                    final_embed.add_field(
                        name="Cancelled",
                        value="The operation was cancelled because no response was sent in time.",
                    )
                await discord_utils.send_message(ctx, final_embed)
                return (
                    responses or None
                )  # If any saved responses, return it, else return None

            if react_task in done:
                reaction, _ = react_task.result()
                if reaction.emoji == confirm_emoji:
                    return responses
                final_embed.add_field(
                    name="Cancelled",
                    value="The operation was cancelled by the user.",
                )
                await discord_utils.send_message(ctx, final_embed)
                return None

            # Otherwise the user sent another response, so add it and go round again
            response = message_task.result().content.strip()
            if response:
                responses.append(response)

    def describe_response(self, ctx, command_name, responses):
        """Short summary of how the customcommand went."""
        return (
            f"I have gathered {len(responses)} response{'s' if len(responses) > 1 else ''} for the command `{command_name}`. "
            f"Use `{ctx.prefix}listcc {command_name}` to see {'them' if len(responses) > 1 else 'it'}."
        )

    async def add_cc_generic(
        self,
        ctx,
        command_name,
        responses,
        is_image: bool,
        is_global: bool,
    ):
        """Saves a new custom command to the database and then the cache. Then, it sends the result."""
        embed = discord_utils.create_embed()
        command_return = responses[0]  # TODO Drop this soon

        with Session(database.DATABASE_ENGINE) as session:
            result = (
                session.query(database.CustomCommands)
                .filter_by(server_id_command=f"{ctx.guild.id} {command_name}")
                .first()
            )
            if result is None:
                stmt = insert(database.CustomCommands).values(
                    server_id=ctx.guild.id,
                    server_name=ctx.guild.name,
                    server_id_command=f"{ctx.guild.id} {command_name}",
                    command_name=command_name,
                    command_return=command_return,
                    image=is_image,
                    responses=responses,
                )
                session.execute(stmt)
                session.commit()

                embed.add_field(
                    name="Success",
                    value=f"Added `{ctx.prefix}{command_name}` with value{'s' if len(responses) > 1 else ''}"
                    f" `{' | '.join(responses)}`",
                )
            # Already in the database but missing from the cache, so
            # tell the user that the command already exists
            else:
                command_return = result.command_return
                responses = result.responses
                is_image = bool(result.image)
                embed.add_field(
                    name="Failed",
                    value=f"The command `{ctx.prefix}{command_name}` already exists in `{ctx.guild.name}`. "
                    f"If you'd like to replace `{ctx.prefix}{command_name}`, please use "
                    f"`{ctx.prefix}editcustomcommand {command_name}`",
                )

            # update cache
            database.CUSTOM_COMMANDS[ctx.guild.id][command_name] = (
                command_return,
                is_image,
                responses,
            )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_trusted()
    @commands.command(
        name="addcustomcommand",
        aliases=["addccommand", "addembedcommand", "customcommand", "addcc", "cc"],
    )
    async def addcustomcommand(
        self, ctx, command_name: str, *, command_return: Optional[str] = None
    ):
        """Add your own custom command to the bot with an embed reply.
        Everything after the command name is the reply, line breaks are included.

        If you leave everything after the command name empty, you'll be prompted to
        enter possible responses for the command, from which the bot will pick
        one randomly out of. If you override a global command with the same name
        with a server command, your server command will take priority over the global one.

        Permission Category : Trusted Roles only.
        Usage: `~addcustomcommand command_name This is my custom command!`
        Usage: `~addcustomcommand flipcoin` (then say `Heads` and `Tails` in subsequent
        messages)

        """
        await logging_utils.log_command(
            "addcustomcommand", ctx.guild, ctx.channel, ctx.author
        )
        command_name = command_name.lower()
        if not await self.check_cc_name(ctx, command_name, is_global=False):
            return
        responses = await self.get_responses(ctx, command_name, command_return)
        if responses is None:
            return
        await self.add_cc_generic(
            ctx, command_name, responses, is_image=False, is_global=False
        )

    @command_predicates.is_trusted()
    @commands.command(
        name="addcustomimage",
        aliases=["addcimage", "addccimage", "addimagecc"],
    )
    async def addcustomimage(
        self, ctx, command_name: str, *, command_return: Optional[str] = None
    ):
        """Add your own custom command to the bot with a reply. It is not in a bot embed, so is ideal for images and role pings.
        Everything after the command name is the reply, line breaks included.
        Leave it empty and the bot asks for responses one message at a time. Give more than one and the bot picks one at random each time.

        Permission Category : Trusted Roles only.
        Usage: `~addcimage command_name Link_to_image`
        Usage: `~addcimage command_name Link_to_hyperlink`
        """
        await logging_utils.log_command(
            "addcustomimage", ctx.guild, ctx.channel, ctx.author
        )
        command_name = command_name.lower()
        if not await self.check_cc_name(ctx, command_name, is_global=False):
            return
        responses = await self.get_responses(ctx, command_name, command_return)
        if responses is None:
            return
        await self.add_cc_generic(
            ctx, command_name, responses, is_image=True, is_global=False
        )

    @command_predicates.is_bot_owner()
    @commands.command(
        name="addglobalcustomcommand",
        aliases=["addglobalccommand", "addgcustomcommand", "addgcc", "addglobalcc"],
    )
    async def addglobalcustomcommand(
        self, ctx, command_name: str, *, command_return: Optional[str] = None
    ):
        pass

    @command_predicates.is_bot_owner()
    @commands.command(
        name="addglobalcustomimage",
        aliases=[
            "addglobalcimage",
            "addglobalccimage",
            "addglobalimagecc",
            "addgcustomimage",
            "addgccimage",
        ],
    )
    async def addglobalcustomimage(
        self, ctx, command_name: str, *, command_return: Optional[str] = None
    ):
        pass

    async def list_cc_responses(self, ctx, command_name):
        """Sends all the numbered response(s) of a given custom command."""
        embed = discord_utils.create_embed()
        # Look in this server first, then the global custom commands. Server commands take priority.
        # The else block below only runs if the command is in neither.
        for guild_id in (ctx.guild.id, constants.DB_GLOBAL):
            if command_name in database.CUSTOM_COMMANDS.get(guild_id, {}):
                command_return, _, responses = database.CUSTOM_COMMANDS[guild_id][
                    command_name
                ]
                # Some custom commands (old) have nothing in the responses list, only command_return
                # So treat it as a command with one response
                responses = responses or [command_return]
                for number, response in enumerate(responses, start=1):
                    embed.add_field(
                        name=f"Response {number}", value=response, inline=False
                    )
                break
        else:
            embed.add_field(
                name="Error",
                value=f"The command `{command_name}` does not exist.",
                inline=False,
            )
        await discord_utils.send_message(ctx, embed)

    # def parse_responses(self, args):
    #     """Parses args as list."""
    #     return [response for response in args if response.strip()]

    # async def add_cc_generic(
    #     self,
    #     ctx,
    #     command_name,
    #     responses,
    #     is_image: bool,
    #     is_global: bool,
    # ):
    #     embed = discord_utils.create_embed()
    #     command_return = " | ".join(responses)
    #     quoted_responses = " ".join(f'"{response}"' for response in responses)
    #     # Only save the list if there is more than one response to pick from
    #     if len(responses) < 2:
    #         responses = None

    #     if command_name in constants.DEFAULT_COMMANDS:
    #         embed.add_field(
    #             name="Failed",
    #             value=f"Command {command_name} is a default command. Please use a different name.",
    #         )
    #         await discord_utils.send_message(ctx, embed)
    #         return

    #     if not is_global and command_name in database.CUSTOM_COMMANDS[ctx.guild.id]:
    #         embed.add_field(
    #             name="Failed",
    #             value=f"The command `{ctx.prefix}{command_name}` already exists in `{ctx.guild.name}` with value{'s' if database.CUSTOM_COMMANDS[ctx.guild.id][command_name][2] else ''} "
    #             f"`{database.CUSTOM_COMMANDS[ctx.guild.id][command_name][0]}`. If you'd like to replace "
    #             f"`{ctx.prefix}{command_name}`, please use `{ctx.prefix}editcustomcommand {command_name} "
    #             f"{quoted_responses}`",
    #         )
    #         await discord_utils.send_message(ctx, embed)
    #         return

    #     with Session(database.DATABASE_ENGINE) as session:
    #         result = (
    #             session.query(database.CustomCommands)
    #             .filter_by(server_id_command=f"{ctx.guild.id} {command_name}")
    #             .first()
    #         )
    #         if result is None:
    #             stmt = insert(database.CustomCommands).values(
    #                 server_id=ctx.guild.id,
    #                 server_name=ctx.guild.name,
    #                 server_id_command=f"{ctx.guild.id} {command_name}",
    #                 command_name=command_name,
    #                 command_return=command_return,
    #                 image=is_image,
    #                 responses=responses,
    #             )
    #             session.execute(stmt)
    #             session.commit()

    #             embed.add_field(
    #                 name="Success",
    #                 value=f"Added `{ctx.prefix}{command_name}` with value{'s' if responses else ''} `{command_return}`",
    #             )
    #         # Command exists in the DB but not in our constants.
    #         else:
    #             command_return = result.command_return
    #             responses = result.responses
    #         # update constants dict
    #         database.CUSTOM_COMMANDS[ctx.guild.id][command_name] = (
    #             command_return,
    #             is_image,
    #             responses,
    #         )
    #     await discord_utils.send_message(ctx, embed)

    # @command_predicates.is_trusted()
    # @commands.command(
    #     name="addccommand",
    #     aliases=["addcustomcommand", "addembedcommand", "customcommand", "addcc"],
    # )
    # async def addcustomcommand(self, ctx, command_name: str, *args):
    #     """Add your own custom command to the bot with an embed reply
    #     Give more than one response and the bot picks one at random each time.
    #     Put quotes around any response with spaces in it.
    #     If there is no server-specific custom command, it defaults to global version (if exists).

    #     Permission Category : Trusted Roles only.
    #     Usage: `~addccommand command_name "This is my custom command!"`
    #     Usage: `~addccommand flipcoin Heads Tails`
    #     """
    #     await logging_utils.log_command(
    #         "addcustomcommand", ctx.guild, ctx.channel, ctx.author
    #     )
    #     embed = discord_utils.create_embed()

    #     responses = self.parse_responses(args)
    #     if len(responses) <= 0:
    #         embed = discord_utils.create_no_argument_embed("Command Return")
    #         await discord_utils.send_message(ctx, embed)
    #         return
    #     command_name = command_name.lower()
    #     await self.add_cc_generic(
    #         ctx, command_name, responses, is_image=False, is_global=False
    #     )

    # @command_predicates.is_trusted()
    # @commands.command(
    #     name="addcustomimage", aliases=["addcimage", "addccimage", "addimagecc"]
    # )
    # async def addcustomimage(self, ctx, command_name: str, *args):
    #     """Add your own custom command to the bot with a reply. It is not in a bot embed, so is ideal for images and role pings.
    #     Give more than one response and the bot picks one at random each time.
    #     Put quotes around any response with spaces in it.
    #     If there is no server-specific custom command, it defaults to global version (if exists).

    #     Permission Category : Trusted Roles only.
    #     Usage: `~addcimage command_name Link_to_image`
    #     Usage: `~addcimage command_name Link_to_hyperlink`
    #     Usage: `~addcimage command_name Link_to_image_1 Link_to_image_2`
    #     """
    #     await logging_utils.log_command(
    #         "addcustomimage", ctx.guild, ctx.channel, ctx.author
    #     )
    #     embed = discord_utils.create_embed()

    #     responses = self.parse_responses(args)
    #     if len(responses) <= 0:
    #         embed = discord_utils.create_no_argument_embed("Command Return")
    #         await discord_utils.send_message(ctx, embed)
    #         return

    #     command_name = command_name.lower()
    #     await self.add_cc_generic(
    #         ctx, command_name, responses, is_image=True, is_global=False
    #     )

    # @command_predicates.is_bot_owner()
    # @commands.command(
    #     name="addglobalccommand",
    #     aliases=["addglobalcustomcommand", "addglobalcc"],
    # )
    # async def addglobalcustomcommand(self, ctx, command_name: str, *args):
    #     """Add your own global custom command to the bot with an embed reply.
    #     Give more than one response and the bot picks one at random each time.
    #     Put quotes around any response with spaces in it.
    #     If there is no server-specific custom command, it defaults to global version.

    #     Permission Category : Bot Owner only.
    #     Usage: `~addglobalccommand command_name "This is my custom command!"`
    #     """
    #     await logging_utils.log_command(
    #         "addglobalcustomcommand", ctx.guild, ctx.channel, ctx.author
    #     )
    #     embed = discord_utils.create_embed()

    #     responses = self.parse_responses(args)
    #     if len(responses) <= 0:
    #         embed = discord_utils.create_no_argument_embed("Command Return")
    #         await discord_utils.send_message(ctx, embed)
    #         return
    #     command_name = command_name.lower()
    #     await self.add_cc_generic(
    #         ctx, command_name, responses, is_image=False, is_global=True
    #     )

    # @command_predicates.is_bot_owner()
    # @commands.command(
    #     name="addglobalcustomimage",
    #     aliases=["addglobalcimage", "addglobalccimage", "addglobalimagecc"],
    # )
    # async def addglobalcustomimage(self, ctx, command_name: str, *args):
    #     """Add your own custom command to the bot with a reply. It is not in a bot embed, so is ideal for images and role pings.
    #     Give more than one response and the bot picks one at random each time.
    #     Put quotes around any response with spaces in it.
    #     If there is no custom command, it defaults to global version.

    #     Permission Category : Bot Owner only.
    #     Usage: `~addglobalcimage command_name Link_to_image`
    #     Usage: `~addglobalcimage command_name Link_to_hyperlink`
    #     """
    #     await logging_utils.log_command(
    #         "addglobalcustomimage", ctx.guild, ctx.channel, ctx.author
    #     )
    #     embed = discord_utils.create_embed()

    #     responses = self.parse_responses(args)
    #     if len(responses) <= 0:
    #         embed = discord_utils.create_no_argument_embed("Command Return")
    #         await discord_utils.send_message(ctx, embed)
    #         return

    #     command_name = command_name.lower()
    #     await self.add_cc_generic(
    #         ctx, command_name, responses, is_image=True, is_global=True
    #     )

    # @commands.command(
    #     name="listcustomcommands",
    #     aliases=["lsccommands", "lscustomcommands", "listccommands", "listcc"],
    # )
    # async def lscustomcommands(self, ctx):
    #     """List custom commands in the server

    #     Usage: `~listccommands`
    #     """
    #     await logging_utils.log_command(
    #         "lscustomcommands", ctx.guild, ctx.channel, ctx.author
    #     )
    #     embed = discord_utils.create_embed()

    #     # Guild custom command
    #     guildid = ctx.guild.id
    #     if (
    #         guildid in database.CUSTOM_COMMANDS
    #         and len(database.CUSTOM_COMMANDS[guildid]) > 0
    #     ):
    #         cclist = database.CUSTOM_COMMANDS[guildid].keys()
    #         custom_commands = "\n".join(sorted(cclist))
    #         embed.add_field(
    #             name=f"Custom Commands for {guildid} : {ctx.guild.name}",
    #             value=custom_commands,
    #         )
    #     else:
    #         embed.add_field(
    #             name="Failed",
    #             value=f"No custom commands in `{guildid}`, why not use "
    #             f"`{ctx.prefix}addcustomcommand` to create one?",
    #             inline=False,
    #         )

    #     # Global commands: Guild id = -1
    #     guildid = -1
    #     owner = await self.bot.fetch_user(os.getenv("BOT_OWNER_DISCORD_ID"))
    #     if (
    #         guildid in database.CUSTOM_COMMANDS
    #         and len(database.CUSTOM_COMMANDS[guildid]) > 0
    #     ):
    #         cclist = database.CUSTOM_COMMANDS[guildid].keys()
    #         custom_commands = (
    #             "\n".join(sorted(cclist))
    #             + f"\nContact {owner.mention} to suggest any more custom commands."
    #         )
    #         embed.add_field(
    #             name="Global Custom Commands",
    #             value=custom_commands,
    #             inline=False,
    #         )
    #     else:
    #         embed.add_field(
    #             name="Success",
    #             value=f"No global custom commands yet. Contact {owner.mention} to suggest one.",
    #             inline=False,
    #         )
    #     await discord_utils.send_message(ctx, embed)

    # @command_predicates.is_trusted()
    # @commands.command(
    #     name="editcustomcommand", aliases=["editccommand", "editcimage", "editcc"]
    # )
    # async def editcustomcommand(self, ctx, command_name: str, *args):
    #     """Edit an existing custom command. If the command doesn't already exist, adds the command.
    #     Give more than one response and the bot picks one at random each time.
    #     Put quotes around any response with spaces in it.
    #     See also: `~addccommand`

    #     Permission Category : Trusted Roles only.
    #     Usage: `~editcustomcommand potato "My new return value"`
    #     Usage: `~editcustomcommand flipcoin Heads Tails Edge`
    #     """
    #     await logging_utils.log_command(
    #         "editcustomcommand", ctx.guild, ctx.channel, ctx.author
    #     )
    #     embed = discord_utils.create_embed()

    #     responses = self.parse_responses(args)
    #     if len(responses) <= 0:
    #         embed = discord_utils.create_no_argument_embed("Command Return")
    #         await discord_utils.send_message(ctx, embed)
    #         return

    #     command_name = command_name.lower()

    #     # If the command does not exist yet, just add it to DB.
    #     if command_name not in database.CUSTOM_COMMANDS[ctx.guild.id]:
    #         await self.add_cc_generic(
    #             ctx, command_name, responses, is_image=False, is_global=False
    #         )
    #         return

    #     command_return = " | ".join(responses)
    #     # Only save the list if there is more than one response to pick from
    #     if len(responses) < 2:
    #         responses = None

    #     # Update command in DB, keeping whether it's an image or embed
    #     with Session(database.DATABASE_ENGINE) as session:
    #         session.query(database.CustomCommands).filter_by(
    #             server_id_command=f"{ctx.guild.id} {command_name}"
    #         ).update({"command_return": command_return, "responses": responses})
    #         session.commit()
    #     database.CUSTOM_COMMANDS[ctx.guild.id][command_name] = (
    #         command_return,
    #         database.CUSTOM_COMMANDS[ctx.guild.id][command_name][1],
    #         responses,
    #     )
    #     embed.add_field(
    #         name="Success",
    #         value=f"Edited command `{ctx.prefix}{command_name}` to have value{'s' if responses else ''} "
    #         f"`{command_return}`",
    #     )
    #     await discord_utils.send_message(ctx, embed)

    # @command_predicates.is_trusted_or_bot_owner()
    # @commands.command(
    #     name="removecustomcommand",
    #     aliases=[
    #         "rmcustomcommand",
    #         "rmccommand",
    #         "removeccommand",
    #         "removecc",
    #         "rmcc",
    #     ],
    # )
    # async def rmcustomcommand(self, ctx, command_name: str):
    #     """Remove an existing custom command.
    #     If triggered by Bot Owner, can remove a global custom command (if a guild custom command does not also exist).

    #     Permission Category : Trusted Roles or Bot Owner only.
    #     Usage: `~rmcustomcommand potato`
    #     """
    #     await logging_utils.log_command(
    #         "rmcustomcommand", ctx.guild, ctx.channel, ctx.author
    #     )
    #     embed = discord_utils.create_embed()

    #     command_name = command_name.lower()
    #     guildid = ctx.guild.id
    #     if command_name in database.CUSTOM_COMMANDS[guildid]:
    #         del database.CUSTOM_COMMANDS[guildid][command_name]
    #         with Session(database.DATABASE_ENGINE) as session:
    #             session.query(database.CustomCommands).filter_by(
    #                 server_id_command=f"{guildid} {command_name}"
    #             ).delete()
    #             session.commit()
    #         embed.add_field(
    #             name="Success",
    #             value=f"Deleted custom command `{ctx.prefix}{command_name}`",
    #         )
    #     elif (
    #         await ctx.bot.is_owner(ctx.author)
    #         and command_name in database.CUSTOM_COMMANDS[-1]
    #     ):
    #         # Global commands: Guild id = -1
    #         guildid = -1
    #         del database.CUSTOM_COMMANDS[guildid][command_name]
    #         with Session(database.DATABASE_ENGINE) as session:
    #             session.query(database.CustomCommands).filter_by(
    #                 server_id_command=f"{guildid} {command_name}"
    #             ).delete()
    #             session.commit()
    #         embed.add_field(
    #             name="Success",
    #             value=f"Deleted global command `{ctx.prefix}{command_name}`",
    #         )
    #     else:
    #         embed.add_field(
    #             name="Failed",
    #             value=f"Command `{ctx.prefix}{command_name}` does not exist in {ctx.guild.name}",
    #             # Technically it's the same error if no global command either, but no need to duplicate error fields yet
    #         )
    #     await discord_utils.send_message(ctx, embed)


def setup(bot):
    bot.add_cog(CustomCommandCog(bot))
