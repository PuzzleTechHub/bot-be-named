import asyncio
from typing import Optional

from nextcord.ext import commands
from sqlalchemy import insert
from sqlalchemy.orm import Session

import constants
import database
from utils import command_predicates, discord_utils

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

    async def check_cc_name(
        self, ctx: commands.Context, command_name, is_global: bool
    ) -> bool:
        """Checks if the command name is free before asking for any responses to fill it with."""
        embed = discord_utils.create_embed()
        if command_name in constants.DEFAULT_COMMANDS:
            embed.add_field(
                name="Failed",
                value=f"Command {command_name} is a default command. Please use a different name.",
            )
            await discord_utils.send_message(ctx, embed)
            return False

        # Global commands are kept under constants.DB_GLOBAL instead of a server id
        server_id = constants.DB_GLOBAL if is_global else ctx.guild.id
        if command_name in database.CUSTOM_COMMANDS.get(server_id, {}):
            command_return, _, responses = database.CUSTOM_COMMANDS[server_id][
                command_name
            ]
            where = "global commands" if is_global else ctx.guild.name
            edit_command = "editgcc" if is_global else "editcc"
            embed.add_field(
                name="Failed",
                value=f"The command `{ctx.prefix}{command_name}` already exists in `{where}` with value{'s' if responses and len(responses) > 1 else ''} "
                f"`{' | '.join(responses or [command_return])}`. If you'd like to replace "
                f"`{ctx.prefix}{command_name}`, please use `{ctx.prefix}{edit_command} {command_name}`",
            )
            await discord_utils.send_message(ctx, embed)
            return False
        return True

    async def get_responses(self, ctx: commands.Context, command_name, command_return):
        """Returns the response given as a list. If none was given, triggers a method that asks for responses
        one message at a time. Returns None if cancelled."""
        if command_return:
            return [command_return]
        return await self.collect_responses(ctx, command_name)

    async def collect_responses(self, ctx: commands.Context, command_name):
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

    def describe_response(self, ctx: commands.Context, command_name, responses):
        """Short summary of how the customcommand went."""
        return (
            f"I have gathered {len(responses)} response{'s' if len(responses) > 1 else ''} for the command `{command_name}`. "
            f"Use `{ctx.prefix}listcr {command_name}` to see {'them' if len(responses) > 1 else 'it'}."
        )

    async def add_cc_generic(
        self,
        ctx: commands.Context,
        command_name,
        responses,
        is_image: bool,
        is_global: bool,
    ):
        """Saves a new custom command to the database and then the cache. Then, it sends the result."""
        embed = discord_utils.create_embed()
        command_return = responses[0]  # TODO Drop this soon
        # Global commands are kept under constants.DB_GLOBAL instead of a server id
        server_id = constants.DB_GLOBAL if is_global else ctx.guild.id
        server_name = "Global" if is_global else ctx.guild.name

        with Session(database.DATABASE_ENGINE) as session:
            result = (
                session.query(database.CustomCommands)
                .filter_by(server_id_command=f"{server_id} {command_name}")
                .first()
            )
            if result is None:
                stmt = insert(database.CustomCommands).values(
                    server_id=server_id,
                    server_name=server_name,
                    server_id_command=f"{server_id} {command_name}",
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
                    value=f"The command `{ctx.prefix}{command_name}` already exists in `{server_name}`. "
                    f"If you'd like to replace `{ctx.prefix}{command_name}`, please use "
                    f"`{ctx.prefix}{'editgcc' if is_global else 'editcc'} {command_name}`",
                )

            # update cache
            database.CUSTOM_COMMANDS.setdefault(server_id, {})[command_name] = (
                command_return,
                is_image,
                responses,
            )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_trusted()
    @commands.command(
        name="addcc",
        aliases=[
            "addcustomcommand",
            "addccommand",
            "addembedcommand",
            "customcommand",
            "cc",
        ],
    )
    async def addcustomcommand(
        self,
        ctx: commands.Context,
        command_name: str,
        *,
        command_return: Optional[str] = None,
    ):
        """Add your own custom command to the bot with an embed reply.
        Everything after the command name is the reply, line breaks are included.

        If you leave everything after the command name empty, you'll be prompted to
        enter possible responses for the command, from which the bot will pick
        one randomly out of. If you override a global command with the same name
        with a server command, your server command will take priority over the global one.

        All the possible responses for a custom command is referred to as the command's "responses".

        Permission Category : Trusted Roles only.
        Usage: `~addcc command_name This is my custom command!`
        Usage: `~addcc flipcoin` (then say `Heads` and `Tails` in subsequent
        messages)

        """
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
        name="addci",
        aliases=["addcustomimage", "addcimage", "addccimage", "addimagecc"],
    )
    async def addcustomimage(
        self,
        ctx: commands.Context,
        command_name: str,
        *,
        command_return: Optional[str] = None,
    ):
        """Add your own custom command to the bot with a reply. It is not in a bot embed, so is ideal for images and role pings.
        Everything after the command name is the reply, line breaks included.
        Leave it empty and the bot asks for responses one message at a time. Give more than one and the bot picks one at random each time.

        Permission Category : Trusted Roles only.
        Usage: `~addci command_name Link_to_image`
        Usage: `~addci command_name Link_to_hyperlink`
        """
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
        name="addgcc",
        aliases=[
            "addglobalcustomcommand",
            "addglobalccommand",
            "addgcustomcommand",
            "addglobalcc",
        ],
    )
    async def addglobalcustomcommand(
        self,
        ctx: commands.Context,
        command_name: str,
        *,
        command_return: Optional[str] = None,
    ):
        """Add a global custom command to the bot with an embed reply. Every
        server with this bot will be able to call a global command, as long
        as there are no commands specific to the server with the same name.
        Everything after the command name is the reply, line breaks included.
        Leave it empty and the bot asks for responses one message at a time.
        Give more than one and the bot picks one at random each time.

        Permission Category : Bot Owner only.
        Usage: `~addgcc command_name Reply`
        """
        command_name = command_name.lower()
        if not await self.check_cc_name(ctx, command_name, is_global=True):
            return
        responses = await self.get_responses(ctx, command_name, command_return)
        if responses is None:
            return
        await self.add_cc_generic(
            ctx,
            command_name,
            responses,
            is_image=False,
            is_global=True,
        )

    @command_predicates.is_bot_owner()
    @commands.command(
        name="addgci",
        aliases=[
            "addglobalcustomimage",
            "addglobalci",
            "addglobalcimage",
            "addglobalccimage",
            "addglobalimagecc",
            "addgcustomimage",
            "addgccimage",
        ],
    )
    async def addglobalcustomimage(
        self,
        ctx: commands.Context,
        command_name: str,
        *,
        command_return: Optional[str] = None,
    ):
        """Add a global custom command to the bot with a reply. It is not in
        a bot embed, so is ideal for images and role pings.
        Everything after the command name is the reply, line breaks included.
        Leave it empty and the bot asks for responses one message at a time.
        Give more than one and the bot picks one at random each time.

        Permission Category : Bot Owner only.
        Usage: `~addgci command_name Link_to_image`
        Usage: `~addgci command_name Link_to_hyperlink`
        """
        command_name = command_name.lower()
        if not await self.check_cc_name(ctx, command_name, is_global=True):
            return
        responses = await self.get_responses(ctx, command_name, command_return)
        if responses is None:
            return
        await self.add_cc_generic(
            ctx, command_name, responses, is_image=True, is_global=True
        )

    async def list_cc_responses(self, ctx: commands.Context, command_name):
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

    @commands.command(
        name="listcc",
        aliases=[
            "listcustomcommands",
            "lsccommands",
            "lscustomcommands",
            "listccommands",
            "lcc",
        ],
    )
    async def lscustomcommands(self, ctx: commands.Context):
        """Lists the custom commands in the server.

        Usage: `~listcc`
        """
        embed = discord_utils.create_embed()

        # The guild's custom commands
        guild_id = ctx.guild.id
        if (
            guild_id in database.CUSTOM_COMMANDS
            and len(database.CUSTOM_COMMANDS[guild_id]) > 0
        ):
            cc_list = database.CUSTOM_COMMANDS[guild_id].keys()
            custom_commands = "\n".join(sorted(cc_list))
            embed.add_field(
                name=f"Custom commands for {guild_id} : {ctx.guild.name}",
                value=custom_commands,
            )
        else:
            embed.add_field(
                name="Failed",
                value="No custom commands found for this server, why not"
                f" make one with {ctx.prefix}addcc?",
                inline=False,
            )

        # The global commands
        guild_id = constants.DB_GLOBAL  # So -1
        owner_mention = discord_utils.bot_owner_mention()
        if (
            guild_id in database.CUSTOM_COMMANDS
            and len(database.CUSTOM_COMMANDS[guild_id]) > 0
        ):
            cc_list = database.CUSTOM_COMMANDS[guild_id].keys()
            custom_commands = (
                "\n".join(sorted(cc_list))
                + f"\n\n **Contact {owner_mention} to suggest more custom commands!**"
            )
            embed.add_field(
                name="Global custom commands",
                value=custom_commands,
                inline=False,
            )
        else:
            embed.add_field(
                name="Success",
                value=f"No global custom commands yet. Contact {owner_mention} to suggest one!",
                inline=False,
            )
        await discord_utils.send_message(ctx, embed)

    @commands.command(
        name="listcr",
        aliases=[
            "listcustomresponses",
            "lscresponses",
            "lscustomresponses",
            "listcresponses",
        ],
    )
    async def listcustomresponses(self, ctx: commands.Context, command_name: str):
        """List all the custom responses for a command in a server.

        Usage: `~listcr foo`
        Usage: `~listcr flipcoin`
        """
        await self.list_cc_responses(ctx, command_name.lower())
        return

    @command_predicates.is_trusted()
    @commands.command(
        name="editcc",
        aliases=[
            "editcustomcommand",
            "editccommand",
            "editci",
            "editcimage",
        ],
    )
    async def editcustomcommand(
        self,
        ctx: commands.Context,
        command_name: str,
        *,
        command_return: Optional[str] = None,
    ):
        """Edit a custom command for the bot, by replacing all its responses. If the
        command doesn't already exist, this command will add it instead (see `~help addcc`).
        Everything after the command name is the reply, line breaks included.

        Permission Category : Trusted Roles only.
        Usage: `~editcc foo My new reply!`
        Usage: `~editcc flipcoin` (then say `Heads`, `Tails` and `Edge` in subsequent
        messages)
        """
        await self.edit_cc_generic(
            ctx, command_name.lower(), command_return, is_global=False
        )

    @command_predicates.is_bot_owner()
    @commands.command(
        name="editgcc",
        aliases=[
            "editglobalcustomcommand",
            "editglobalccommand",
            "editgcustomcommand",
            "editglobalcc",
            "editgci",
            "editglobalci",
            "editglobalcimage",
        ],
    )
    async def editglobalcustomcommand(
        self,
        ctx: commands.Context,
        command_name: str,
        *,
        command_return: Optional[str] = None,
    ):
        """Edit a global custom command for the bot, by replacing all its responses. If the
        global command doesn't already exist, this command will add it instead (see `~help addgcc`).
        Everything after the command name is the reply, line breaks included.

        Permission Category : Bot Owner only.
        Usage: `~editgcc foo My new reply!`
        """
        await self.edit_cc_generic(
            ctx, command_name.lower(), command_return, is_global=True
        )

    async def edit_cc_generic(
        self, ctx: commands.Context, command_name, command_return, is_global: bool
    ):
        """Replaces all the responses of a server (or global) custom command.
        If the command doesn't exist yet, it gets added as a non-image command instead."""
        # Global commands are kept under constants.DB_GLOBAL instead of a server id
        server_id = constants.DB_GLOBAL if is_global else ctx.guild.id
        is_new = command_name not in database.CUSTOM_COMMANDS.get(server_id, {})
        if is_new and not await self.check_cc_name(ctx, command_name, is_global):
            return
        responses = await self.get_responses(ctx, command_name, command_return)
        if responses is None:
            return
        # If the command doesn't exist yet, add it instead, which sends its own message
        if is_new:
            await self.add_cc_generic(
                ctx, command_name, responses, is_image=False, is_global=is_global
            )
            return

        embed = discord_utils.create_embed()
        # Update command in DB
        with Session(database.DATABASE_ENGINE) as session:
            session.query(database.CustomCommands).filter_by(
                server_id_command=f"{server_id} {command_name}"
            ).update({"command_return": responses[0], "responses": responses})
            session.commit()
        database.CUSTOM_COMMANDS[server_id][command_name] = (
            responses[0],
            database.CUSTOM_COMMANDS[server_id][command_name][1],
            responses,
        )
        embed.add_field(
            name="Success",
            value=f"Edited command `{ctx.prefix}{command_name}` to have value{'s' if len(responses) > 1 else ''} "
            f"`{' | '.join(responses)}`",
        )
        await discord_utils.send_message(ctx, embed)

    async def rm_cc_response(
        self, ctx: commands.Context, command_name, response_number
    ):
        """Removes one response from a server custom command, but will refuse to remove the last one.
        If the server has no command with that name, the Bot Owner can remove a response from the global one."""
        embed = discord_utils.create_embed()
        guild_id = ctx.guild.id
        if command_name not in database.CUSTOM_COMMANDS[guild_id]:
            if await ctx.bot.is_owner(
                ctx.author
            ) and command_name in database.CUSTOM_COMMANDS.get(constants.DB_GLOBAL, {}):
                guild_id = constants.DB_GLOBAL
            else:
                embed.add_field(
                    name="Failed",
                    value=f"The command `{ctx.prefix}{command_name}` does not exist in `{ctx.guild.name}`.",
                )
                await discord_utils.send_message(ctx, embed)
                return

        command_return, is_image, responses = database.CUSTOM_COMMANDS[guild_id][
            command_name
        ]

        # older custom commands have nothing in the response list (None), so treat
        # command_return as the one response.
        responses = list(responses or [command_return])
        if not 1 <= response_number <= len(responses):
            embed.add_field(
                name="Failed",
                value=f"`{ctx.prefix}{command_name}` does not have a response number `{response_number}`."
                f" `{ctx.prefix}{command_name}` only has {len(responses)} response{'s' if len(responses) > 1 else ''}.",
            )
            await discord_utils.send_message(ctx, embed)
            return
        if len(responses) == 1:
            embed.add_field(
                name="Failed",
                value=f"`{ctx.prefix}{command_name}` only has one response, so it can't be removed. "
                f"Use `{ctx.prefix}rmcc {command_name}` to delete the command instead.",
            )
            await discord_utils.send_message(ctx, embed)
            return

        responses.pop(response_number - 1)
        with Session(database.DATABASE_ENGINE) as session:
            session.query(database.CustomCommands).filter_by(
                server_id_command=f"{guild_id} {command_name}"
            ).update({"command_return": responses[0], "responses": responses})
            session.commit()
        database.CUSTOM_COMMANDS[guild_id][command_name] = (
            responses[0],
            is_image,
            responses,
        )
        embed.add_field(
            name="Success",
            value=f"Removed response {response_number} from `{ctx.prefix}{command_name}`. "
            f"{self.describe_response(ctx, command_name, responses)}",
        )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_trusted_or_bot_owner()
    @commands.command(
        name="rmcc",
        aliases=[
            "removecustomcommand",
            "rmcustomcommand",
            "rmccommand",
            "removeccommand",
            "removecc",
            "rmci",
            "removeci",
            "rmcimage",
            "removecimage",
        ],
    )
    async def rmcustomcommand(
        self,
        ctx: commands.Context,
        command_name: str,
    ):
        """Removes an existing custom command. If this is triggered by the Bot Owner,
        the Bot Owner can remove a global command (note: if a guild custom command
        exists with the same name, the guild command will be the one to get deleted).

        Permission Category : Trusted Roles or Bot Owner only.
        Usage: `~rmcc potato`
        """
        command_name = command_name.lower()

        embed = discord_utils.create_embed()
        guild_id = ctx.guild.id
        if command_name in database.CUSTOM_COMMANDS[guild_id]:
            del database.CUSTOM_COMMANDS[guild_id][command_name]  # Delete from cache
            with Session(database.DATABASE_ENGINE) as session:
                session.query(database.CustomCommands).filter_by(
                    server_id_command=f"{guild_id} {command_name}"
                ).delete()
                session.commit()

            # Tell the Bot Owner if a global command with the same name is still there
            owner_note = ""
            if await ctx.bot.is_owner(
                ctx.author
            ) and command_name in database.CUSTOM_COMMANDS.get(constants.DB_GLOBAL, {}):
                owner_note = (
                    ". Heads up: a global command has the same name as the"
                    " one you just deleted. The global one has not been removed."
                )
            embed.add_field(
                name="Success",
                value=f"Deleted custom command `{ctx.prefix}{command_name}`{owner_note}",
            )
        elif await ctx.bot.is_owner(
            ctx.author
        ) and command_name in database.CUSTOM_COMMANDS.get(constants.DB_GLOBAL, {}):
            # Delete global commands
            guild_id = constants.DB_GLOBAL
            del database.CUSTOM_COMMANDS[guild_id][command_name]  # Delete from cache
            with Session(database.DATABASE_ENGINE) as session:
                session.query(database.CustomCommands).filter_by(
                    server_id_command=f"{guild_id} {command_name}"
                ).delete()
                session.commit()
            embed.add_field(
                name="Success",
                value=f"Deleted global command `{ctx.prefix}{command_name}`",
            )
        else:
            embed.add_field(
                name="Failed",
                value=f"Custom command `{ctx.prefix}{command_name}` was not found.",
            )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_trusted_or_bot_owner()
    @commands.command(
        name="rmcr",
        aliases=[
            "removecustomresponse",
            "rmcustomresponse",
            "rmcresponse",
            "removecresponse",
            "removecr",
        ],
    )
    async def removecustomresponse(
        self, ctx: commands.Context, command_name: str, response_number: int
    ):
        """Remove an existing response from a custom command. Global commands
        can only be edited by the Bot Owner.

        Permission Category : Trusted Roles or Bot Owner only.
        Usage: `~rmcr potato 1` (Removes the first response)
        """
        command_name = command_name.lower()
        await self.rm_cc_response(ctx, command_name, response_number)
        return


def setup(bot):
    bot.add_cog(CustomCommandCog(bot))
