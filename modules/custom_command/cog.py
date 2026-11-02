import database
import constants
import os
from utils import discord_utils, logging_utils, command_predicates
from nextcord.ext import commands
from sqlalchemy.orm import Session
from sqlalchemy import insert

"""
Custom command module. Allows users to set their own "custom command" of saveable image/embed/messages making a lot of easy to retrieve utility.
"""


class CustomCommandCog(commands.Cog, name="Custom Commands"):
    """
    Customised commands saved for each server
    """

    def __init__(self, bot):
        self.bot = bot

    def parse_responses(self, args):
        """Parses args as list."""
        return [response for response in args if response.strip()]

    async def add_cc_generic(
        self,
        ctx,
        command_name,
        responses,
        is_image: bool,
        is_global: bool,
    ):
        embed = discord_utils.create_embed()
        command_return = " | ".join(responses)
        quoted_responses = " ".join(f'"{response}"' for response in responses)
        # Only save the list if there is more than one response to pick from
        if len(responses) < 2:
            responses = None

        if command_name in constants.DEFAULT_COMMANDS:
            embed.add_field(
                name="Failed",
                value=f"Command {command_name} is a default command. Please use a different name.",
            )
            await discord_utils.send_message(ctx, embed)
            return

        if not is_global and command_name in database.CUSTOM_COMMANDS[ctx.guild.id]:
            embed.add_field(
                name="Failed",
                value=f"The command `{ctx.prefix}{command_name}` already exists in `{ctx.guild.name}` with value{'s' if database.CUSTOM_COMMANDS[ctx.guild.id][command_name][2] else ''} "
                f"`{database.CUSTOM_COMMANDS[ctx.guild.id][command_name][0]}`. If you'd like to replace "
                f"`{ctx.prefix}{command_name}`, please use `{ctx.prefix}editcustomcommand {command_name} "
                f"{quoted_responses}`",
            )
            await discord_utils.send_message(ctx, embed)
            return

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
                    value=f"Added `{ctx.prefix}{command_name}` with value{'s' if responses else ''} `{command_return}`",
                )
            # Command exists in the DB but not in our constants.
            else:
                command_return = result.command_return
                responses = result.responses
            # update constants dict
            database.CUSTOM_COMMANDS[ctx.guild.id][command_name] = (
                command_return,
                is_image,
                responses,
            )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_trusted()
    @commands.command(
        name="addccommand",
        aliases=["addcustomcommand", "addembedcommand", "customcommand", "addcc"],
    )
    async def addcustomcommand(self, ctx, command_name: str, *args):
        """Add your own custom command to the bot with an embed reply
        Give more than one response and the bot picks one at random each time.
        Put quotes around any response with spaces in it.
        If there is no server-specific custom command, it defaults to global version (if exists).

        Permission Category : Trusted Roles only.
        Usage: `~addccommand command_name "This is my custom command!"`
        Usage: `~addccommand flipcoin Heads Tails`
        """
        await logging_utils.log_command(
            "addcustomcommand", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        responses = self.parse_responses(args)
        if len(responses) <= 0:
            embed = discord_utils.create_no_argument_embed("Command Return")
            await discord_utils.send_message(ctx, embed)
            return
        command_name = command_name.lower()
        await self.add_cc_generic(
            ctx, command_name, responses, is_image=False, is_global=False
        )

    @command_predicates.is_trusted()
    @commands.command(
        name="addcustomimage", aliases=["addcimage", "addccimage", "addimagecc"]
    )
    async def addcustomimage(self, ctx, command_name: str, *args):
        """Add your own custom command to the bot with a reply. It is not in a bot embed, so is ideal for images and role pings.
        Give more than one response and the bot picks one at random each time.
        Put quotes around any response with spaces in it.
        If there is no server-specific custom command, it defaults to global version (if exists).

        Permission Category : Trusted Roles only.
        Usage: `~addcimage command_name Link_to_image`
        Usage: `~addcimage command_name Link_to_hyperlink`
        Usage: `~addcimage command_name Link_to_image_1 Link_to_image_2`
        """
        await logging_utils.log_command(
            "addcustomimage", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        responses = self.parse_responses(args)
        if len(responses) <= 0:
            embed = discord_utils.create_no_argument_embed("Command Return")
            await discord_utils.send_message(ctx, embed)
            return

        command_name = command_name.lower()
        await self.add_cc_generic(
            ctx, command_name, responses, is_image=True, is_global=False
        )

    @command_predicates.is_bot_owner()
    @commands.command(
        name="addglobalccommand",
        aliases=["addglobalcustomcommand", "addglobalcc"],
    )
    async def addglobalcustomcommand(self, ctx, command_name: str, *args):
        """Add your own global custom command to the bot with an embed reply.
        Give more than one response and the bot picks one at random each time.
        Put quotes around any response with spaces in it.
        If there is no server-specific custom command, it defaults to global version.

        Permission Category : Bot Owner only.
        Usage: `~addglobalccommand command_name "This is my custom command!"`
        """
        await logging_utils.log_command(
            "addglobalcustomcommand", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        responses = self.parse_responses(args)
        if len(responses) <= 0:
            embed = discord_utils.create_no_argument_embed("Command Return")
            await discord_utils.send_message(ctx, embed)
            return
        command_name = command_name.lower()
        await self.add_cc_generic(
            ctx, command_name, responses, is_image=False, is_global=True
        )

    @command_predicates.is_bot_owner()
    @commands.command(
        name="addglobalcustomimage",
        aliases=["addglobalcimage", "addglobalccimage", "addglobalimagecc"],
    )
    async def addglobalcustomimage(self, ctx, command_name: str, *args):
        """Add your own custom command to the bot with a reply. It is not in a bot embed, so is ideal for images and role pings.
        Give more than one response and the bot picks one at random each time.
        Put quotes around any response with spaces in it.
        If there is no custom command, it defaults to global version.

        Permission Category : Bot Owner only.
        Usage: `~addglobalcimage command_name Link_to_image`
        Usage: `~addglobalcimage command_name Link_to_hyperlink`
        """
        await logging_utils.log_command(
            "addglobalcustomimage", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        responses = self.parse_responses(args)
        if len(responses) <= 0:
            embed = discord_utils.create_no_argument_embed("Command Return")
            await discord_utils.send_message(ctx, embed)
            return

        command_name = command_name.lower()
        await self.add_cc_generic(
            ctx, command_name, responses, is_image=True, is_global=True
        )

    @commands.command(
        name="listcustomcommands",
        aliases=["lsccommands", "lscustomcommands", "listccommands", "listcc"],
    )
    async def lscustomcommands(self, ctx):
        """List custom commands in the server

        Usage: `~listccommands`
        """
        await logging_utils.log_command(
            "lscustomcommands", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        # Guild custom command
        guildid = ctx.guild.id
        if (
            guildid in database.CUSTOM_COMMANDS
            and len(database.CUSTOM_COMMANDS[guildid]) > 0
        ):
            cclist = database.CUSTOM_COMMANDS[guildid].keys()
            custom_commands = "\n".join(sorted(cclist))
            embed.add_field(
                name=f"Custom Commands for {guildid} : {ctx.guild.name}",
                value=custom_commands,
            )
        else:
            embed.add_field(
                name="Failed",
                value=f"No custom commands in `{guildid}`, why not use "
                f"`{ctx.prefix}addcustomcommand` to create one?",
                inline=False,
            )

        # Global commands: Guild id = -1
        guildid = -1
        owner = await self.bot.fetch_user(os.getenv("BOT_OWNER_DISCORD_ID"))
        if (
            guildid in database.CUSTOM_COMMANDS
            and len(database.CUSTOM_COMMANDS[guildid]) > 0
        ):
            cclist = database.CUSTOM_COMMANDS[guildid].keys()
            custom_commands = (
                "\n".join(sorted(cclist))
                + f"\nContact {owner.mention} to suggest any more custom commands."
            )
            embed.add_field(
                name="Global Custom Commands",
                value=custom_commands,
                inline=False,
            )
        else:
            embed.add_field(
                name="Success",
                value=f"No global custom commands yet. Contact {owner.mention} to suggest one.",
                inline=False,
            )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_trusted()
    @commands.command(
        name="editcustomcommand", aliases=["editccommand", "editcimage", "editcc"]
    )
    async def editcustomcommand(self, ctx, command_name: str, *args):
        """Edit an existing custom command. If the command doesn't already exist, adds the command.
        Give more than one response and the bot picks one at random each time.
        Put quotes around any response with spaces in it.
        See also: `~addccommand`

        Permission Category : Trusted Roles only.
        Usage: `~editcustomcommand potato "My new return value"`
        Usage: `~editcustomcommand flipcoin Heads Tails Edge`
        """
        await logging_utils.log_command(
            "editcustomcommand", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        responses = self.parse_responses(args)
        if len(responses) <= 0:
            embed = discord_utils.create_no_argument_embed("Command Return")
            await discord_utils.send_message(ctx, embed)
            return

        command_name = command_name.lower()

        # If the command does not exist yet, just add it to DB.
        if command_name not in database.CUSTOM_COMMANDS[ctx.guild.id]:
            await self.add_cc_generic(
                ctx, command_name, responses, is_image=False, is_global=False
            )
            return

        command_return = " | ".join(responses)
        # Only save the list if there is more than one response to pick from
        if len(responses) < 2:
            responses = None

        # Update command in DB, keeping whether it's an image or embed
        with Session(database.DATABASE_ENGINE) as session:
            session.query(database.CustomCommands).filter_by(
                server_id_command=f"{ctx.guild.id} {command_name}"
            ).update({"command_return": command_return, "responses": responses})
            session.commit()
        database.CUSTOM_COMMANDS[ctx.guild.id][command_name] = (
            command_return,
            database.CUSTOM_COMMANDS[ctx.guild.id][command_name][1],
            responses,
        )
        embed.add_field(
            name="Success",
            value=f"Edited command `{ctx.prefix}{command_name}` to have value{'s' if responses else ''} "
            f"`{command_return}`",
        )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_trusted_or_bot_owner()
    @commands.command(
        name="removecustomcommand",
        aliases=[
            "rmcustomcommand",
            "rmccommand",
            "removeccommand",
            "removecc",
            "rmcc",
        ],
    )
    async def rmcustomcommand(self, ctx, command_name: str):
        """Remove an existing custom command.
        If triggered by Bot Owner, can remove a global custom command (if a guild custom command does not also exist).

        Permission Category : Trusted Roles or Bot Owner only.
        Usage: `~rmcustomcommand potato`
        """
        await logging_utils.log_command(
            "rmcustomcommand", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        command_name = command_name.lower()
        guildid = ctx.guild.id
        if command_name in database.CUSTOM_COMMANDS[guildid]:
            del database.CUSTOM_COMMANDS[guildid][command_name]
            with Session(database.DATABASE_ENGINE) as session:
                session.query(database.CustomCommands).filter_by(
                    server_id_command=f"{guildid} {command_name}"
                ).delete()
                session.commit()
            embed.add_field(
                name="Success",
                value=f"Deleted custom command `{ctx.prefix}{command_name}`",
            )
        elif (
            await ctx.bot.is_owner(ctx.author)
            and command_name in database.CUSTOM_COMMANDS[-1]
        ):
            # Global commands: Guild id = -1
            guildid = -1
            del database.CUSTOM_COMMANDS[guildid][command_name]
            with Session(database.DATABASE_ENGINE) as session:
                session.query(database.CustomCommands).filter_by(
                    server_id_command=f"{guildid} {command_name}"
                ).delete()
                session.commit()
            embed.add_field(
                name="Success",
                value=f"Deleted global command `{ctx.prefix}{command_name}`",
            )
        else:
            embed.add_field(
                name="Failed",
                value=f"Command `{ctx.prefix}{command_name}` does not exist in {ctx.guild.name}",
                # Technically it's the same error if no global command either, but no need to duplicate error fields yet
            )
        await discord_utils.send_message(ctx, embed)


def setup(bot):
    bot.add_cog(CustomCommandCog(bot))
