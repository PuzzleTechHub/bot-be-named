from discord.ext import commands
from sqlalchemy.orm import Session
from sqlalchemy import insert
import database
from utils import discord_utils, logging_utils, command_predicates
import constants


class CustomCommandCog(commands.Cog, name="Custom Command"):
    """Create your own custom command!"""

    def __init__(self, bot):
        self.bot = bot

    @command_predicates.is_trusted()
    @commands.command(
        name="addembedcommand",
        aliases=["addcustomcommand", "addccommand", "customcommand", "addcc"],
    )
    async def addembedcommand(self, ctx, command_name: str, *args):
        """Add your own custom command to the bot with an embed reply

        Category: Trusted Roles only.
        Usage: `~addccommand command_name "This is my custom command!"`
        """
        logging_utils.log_command("addembedcommand", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if len(args) <= 0:
            embed = discord_utils.create_no_argument_embed("Command Return")
            await ctx.send(embed=embed)
            return

        command_name = command_name.lower()
        command_return = " ".join(args)

        if command_name in constants.DEFAULT_COMMANDS:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Command {command_name} is a default command. Please use a different name.",
            )

            await ctx.send(embed=embed)
            return

        if command_name in database.CUSTOM_COMMANDS[ctx.guild.id]:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The command `{ctx.prefix}{command_name}` already exists in `{ctx.guild.name}` with value "
                f"`{database.CUSTOM_COMMANDS[ctx.guild.id][command_name][0]}`. If you'd like to replace "
                f"`{ctx.prefix}{command_name}`, please use `{ctx.prefix}editcustomcommand {command_name} "
                f"{command_return}`",
            )
            await ctx.send(embed=embed)
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
                    image=False,
                )
                session.execute(stmt)
                session.commit()

                embed = discord_utils.create_embed()
                embed.add_field(
                    name=f"{constants.SUCCESS}",
                    value=f"Added `{ctx.prefix}{command_name}` with value `{command_return}`",
                )
            # Command exists in the DB but not in our constants.
            else:
                command_return = result.command_return
            # update constants dict
            database.CUSTOM_COMMANDS[ctx.guild.id][command_name] = (
                command_return,
                False,
            )

        await ctx.send(embed=embed)

    @command_predicates.is_trusted()
    @commands.command(
        name="addcustomimage", aliases=["addcimage", "addccimage", "addimagecc"]
    )
    async def addtextcommand(self, ctx, command_name: str, *args):
        """Add your own custom command to the bot with a text reply. It is not in embed, so is ideal for images and role pings.

        Category: Trusted Roles only.
        Usage: `~addcimage command_name Link_to_image`
        Usage: `~addcimage command_name Link_to_hyperlink`
        """
        logging_utils.log_command("addtextcommand", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if len(args) <= 0:
            embed = discord_utils.create_no_argument_embed("Command Return")
            await ctx.send(embed=embed)
            return

        command_name = command_name.lower()
        command_return = " ".join(args)

        if command_name in constants.DEFAULT_COMMANDS:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Command {command_name} is a default command. Please use a different name.",
            )

            await ctx.send(embed=embed)
            return

        if command_name in database.CUSTOM_COMMANDS[ctx.guild.id]:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The command `{ctx.prefix}{command_name}` already exists in `{ctx.guild.name}` with value "
                f"`{database.CUSTOM_COMMANDS[ctx.guild.id][command_name][0]}`. If you'd like to replace "
                f"`{ctx.prefix}{command_name}`, please use `{ctx.prefix}editcustomcommand {command_name} "
                f"{command_return}`",
            )
            await ctx.send(embed=embed)
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
                    image=True,
                )
                session.execute(stmt)
                session.commit()

                embed = discord_utils.create_embed()
                embed.add_field(
                    name=f"{constants.SUCCESS}",
                    value=f"Added `{ctx.prefix}{command_name}` with value `{command_return}`",
                )
            # Command exists in the DB but not in our constants.
            else:
                command_return = result.command_return
            # update constants dict
            database.CUSTOM_COMMANDS[ctx.guild.id][command_name] = (
                command_return,
                True,
            )

        await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(
        name="listcustomcommands",
        aliases=["lsccommands", "lscustomcommands", "listccommands", "listcc"],
    )
    async def lscustomcommands(self, ctx):
        """List custom commands in the server

        Category: Verified Roles only.
        Usage: `~listccommands`
        """
        logging_utils.log_command(
            "lscustomcommands", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        if (
            ctx.guild.id in database.CUSTOM_COMMANDS
            and len(database.CUSTOM_COMMANDS[ctx.guild.id]) > 0
        ):
            cclist = database.CUSTOM_COMMANDS[ctx.guild.id].keys()
            custom_commands = "\n".join(sorted(cclist))
            embed.add_field(
                name=f"Custom Commands for {ctx.guild.name}", value=custom_commands
            )
        else:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"No custom commands in `{ctx.guild}`, why not use "
                f"`{ctx.prefix}addcustomcommand` to create one?",
            )
        await ctx.send(embed=embed)

    @command_predicates.is_trusted()
    @commands.command(
        name="editcustomcommand", aliases=["editccommand", "editcimage", "editcc"]
    )
    async def editcustomcommand(self, ctx, command_name: str, *args):
        """Edit an existing custom command. If the command doesn't already exist, adds the command.
        See also: `~addccommand`

        Category: Trusted Roles only.
        Usage: `~editcustomcommand potato "My new return value"`
        """
        logging_utils.log_command(
            "editcustomcommand", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        if len(args) <= 0:
            embed = discord_utils.create_no_argument_embed("Command Return")
            await ctx.send(embed=embed)
            return

        command_name = command_name.lower()
        command_return = " ".join(args)

        if command_name in database.CUSTOM_COMMANDS[ctx.guild.id]:
            # Update command in DB
            with Session(database.DATABASE_ENGINE) as session:
                session.query(database.CustomCommands).filter_by(
                    server_id_command=f"{ctx.guild.id} {command_name}"
                ).update({"command_return": command_return})
                session.commit()
            embed.add_field(
                name=f"{constants.SUCCESS}",
                value=f"Edited command `{ctx.prefix}{command_name}` to have return value "
                f"`{command_return}`",
            )
            database.CUSTOM_COMMANDS[ctx.guild.id][command_name] = (
                command_return,
                database.CUSTOM_COMMANDS[ctx.guild.id][command_name][1],
            )
        else:
            # If the command does not exist yet, just add it to DB.
            with Session(database.DATABASE_ENGINE) as session:
                stmt = insert(database.CustomCommands).values(
                    server_id=ctx.guild.id,
                    server_name=ctx.guild.name,
                    server_id_command=f"{ctx.guild.id} {command_name}",
                    command_name=command_name,
                    command_return=command_return,
                    image=False,
                )
                session.execute(stmt)
                session.commit()
            database.CUSTOM_COMMANDS[ctx.guild.id][command_name] = (
                command_return,
                False,
            )
            embed.add_field(
                name=f"{constants.SUCCESS}",
                value=f"Added command `{ctx.prefix}{command_name}` with return value "
                f"`{command_return}`",
            )

        await ctx.send(embed=embed)

    @command_predicates.is_trusted()
    @commands.command(
        name="removecustomcommand",
        aliases=["rmcustomcommand", "rmccommand", "removeccommand", "removecc"],
    )
    async def rmcustomcommand(self, ctx, command_name: str):
        """Remove an existing custom command

        Category: Trusted Roles only.
        Usage: `~rmcustomcommand potato`
        """
        logging_utils.log_command("rmcustomcommand", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        command_name = command_name.lower()
        if command_name in database.CUSTOM_COMMANDS[ctx.guild.id]:
            del database.CUSTOM_COMMANDS[ctx.guild.id][command_name]
            with Session(database.DATABASE_ENGINE) as session:
                session.query(database.CustomCommands).filter_by(
                    server_id_command=f"{ctx.guild.id} {command_name}"
                ).delete()
                session.commit()
            embed.add_field(
                name=f"{constants.SUCCESS}",
                value=f"Deleted custom command `{ctx.prefix}{command_name}`",
            )
        else:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Command `{ctx.prefix}{command_name}` does not exist in {ctx.guild.name}",
            )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(CustomCommandCog(bot))
