import discord
from discord.ext import commands
from discord.ext.commands.core import command
from sqlalchemy.orm import Session
from sqlalchemy import insert
from utils import discord_utils, admin_utils, logging_utils, database_utils
import constants


class CustomCommandCog(commands.Cog, name="Custom Command"):
    """Create your own custom command!"""
    def __init__(self, bot):
        self.bot = bot

    @admin_utils.is_verified()
    @commands.command(name="addcustomcommand", aliases=["addcommand"])
    async def addcustomcommand(self, ctx, command_name: str, *args):
        """Add your own custom command to the bot
        
        Usage: `~addcustomcommand command_name \"This is my custom command!\""""
        logging_utils.log_command("addcustomcommand", ctx.channel, ctx.author)

        if len(args) <= 0:
            discord_utils.create_no_argument_embed("Command Return")

        command_return = " ".join(args)

        if command_name in constants.CUSTOM_COMMANDS[ctx.guild.id]:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"{constants.FAILED}",
                            value=f"The command `{ctx.prefix}{command_name}` already exists in `{ctx.guild.name}` with value "
                                    f"`{constants.CUSTOM_COMMANDS[ctx.guild.id][command_name]}`. If you'd like to replace "
                                    f"`{ctx.prefix}{command_name}`, please use `{ctx.prefix}editcustomcommand {command_name} "
                                    f"{command_return}`")
            await ctx.send(embed=embed)
            return

        with Session(constants.DATABASE_ENGINE) as session:
            result = session.query(database_utils.CustomCommmands)\
                            .filter_by(server_id_command=f"{ctx.guild.id} {command_name}")\
                            .first()
            if result is None:
                stmt = insert(database_utils.CustomCommmands).values(server_id=ctx.guild.id, server_name=ctx.guild.name,
                                                                     server_id_command=f"{ctx.guild.id} {command_name}",
                                                                     command_name=command_name, command_return=command_return)
                session.execute(stmt)
                session.commit()

                
                embed = discord_utils.create_embed()
                embed.add_field(name=f"{constants.SUCCESS}",
                                value=f"Added `{ctx.prefix}{command_name} with value `{command_return}`")
            # Command exists in the DB but not in our constants.
            else:
                command_return = result.command_return
            # update constants dict
            constants.CUSTOM_COMMANDS[ctx.guild.id][command_name] = command_return
                 
        await ctx.send(embed=embed)

    @admin_utils.is_verified()
    @commands.command(name="lscustomcommands", aliases=["listcustomcommands"])
    async def lscustomcommands(self, ctx):
        """List custom commands in the server
        
        Usage: `~lscustomcommands`"""
        logging_utils.log_command("lscustomcommands", ctx.channel, ctx.author)

        custom_commands = "\n".join(constants.CUSTOM_COMMANDS[ctx.guild.id].keys())
        embed = discord.Embed(title=f"Custom Commands for {ctx.guild.name}",
                              description=custom_commands,
                              color=constants.EMBED_COLOR)
        await ctx.send(embed=embed)

    @admin_utils.is_verified()
    @commands.command(name="editcustomcommand")
    async def editcustomcommand(self, ctx, command_name: str, *args):
        """Edit an existing custom command, or adds the command if it doesn't exist.
        
        Usage: `~editcustomcommand potato My new return value`"""
        logging_utils.log_command("editcustomcommand", ctx.channel, ctx.author)

        command_return = " ".join(args)

        if command_name in constants.CUSTOM_COMMANDS[ctx.guild.id]:
            # Update command in DB
            with Session(constants.DATABASE_ENGINE) as session:
                result = session.query(database_utils.CustomCommmands)\
                       .filter_by(server_id_command=f"{ctx.guild.id} {command_name}")\
                       .update({"command_return": command_return})
            embed = discord_utils.create_embed()
            embed.add_field(name=f"{constants.SUCCESS}",
                            value=f"Edited command `{ctx.prefix}{command_name}` to have return value "
                                  f"`{command_return}`")
        else:
            # If the command does not exist yet, just add it to DB.
            with Session(constants.DATABASE_ENGINE) as session:
                stmt = insert(database_utils.CustomCommmands).values(server_id=ctx.guild.id, server_name=ctx.guild.name,
                                                                     server_id_command=f"{ctx.guild.id} {command_name}",
                                                                     command_name=command_name, command_return=command_return)
                session.execute(stmt)
                session.commit()
            embed = discord_utils.create_embed()
            embed.add_field(name=f"{constants.SUCCESS}",
                            value=f"Added command `{ctx.prefix}{command_name}` with return value "
                                  f"`{command_return}`")
        # Update constants dict
        constants.CUSTOM_COMMANDS[ctx.guild.id][command_name] = command_return
        await ctx.send(embed=embed)

    @admin_utils.is_verified()
    @commands.command(name="rmcustomcommand", aliases=["removecustomcommand"])
    async def rmcustomcommand(self, ctx, command_name: str):
        """Remove an existing custom command
        
        Usage: `~rmcustomcommand potato`"""
        logging_utils.log_command("rmcustomcommand", ctx.channel, ctx.author)

        if command_name in constants.CUSTOM_COMMANDS[ctx.guild.id]:
            del constants.CUSTOM_COMMANDS[ctx.guild.id][command_name]
            with Session(constants.DATABASE_ENGINE) as session:
                session.query(database_utils.CustomCommmands)\
                       .filter_by(server_id_command=f"{ctx.guild.id} {command_name}")\
                       .delete()
                session.commit()
            embed = discord_utils.create_embed()
            embed.add_field(name=f"{constants.SUCCESS}",
                            value=f"Deleted custom command `{ctx.prefix}{command_name}`")
        else:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"{constants.FAILED}",
                            value=f"Command `{ctx.prefix}{command_name}` does not exist in {ctx.guild.name}")
        await ctx.send(embed=embed)
                

def setup(bot):
    bot.add_cog(CustomCommandCog(bot))