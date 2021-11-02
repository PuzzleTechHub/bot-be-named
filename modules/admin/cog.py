import discord
from discord.ext import commands
from discord.ext.commands.core import command
import psycopg2
from sqlalchemy.orm import Session
import sqlalchemy
from utils import discord_utils, logging_utils, database_utils, command_predicates
import constants
from typing import Union


class AdminCog(commands.Cog, name="Admin"):
    """Downloads a channel's history and sends it as a file to the user"""
    def __init__(self, bot):
        self.bot = bot

    @command_predicates.is_owner_or_admin()
    @commands.command(name="addverified")
    async def addverified(self, ctx, role_or_rolename: Union[discord.Role, str], role_category: str = "Verified"):
        """Add a new verified category for this server. Only available to server admins or bot owners.
        
        Usage: `~addverified @Verified Verified`"""
        logging_utils.log_command("addverified", ctx.guild, ctx.channel, ctx.author)

        if not role_or_rolename:
            embed = discord_utils.create_no_argument_embed("role")
            await ctx.send(embed=embed)
            return

        if role_category not in database_utils.VERIFIED_CATEGORIES:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"{constants.FAILED}",
                            value=f"`role_category` must be in {', '.join(database_utils.VERIFIED_CATEGORIES)}, "
                                  f"but you supplied {role_category}")
            await ctx.send(embed=embed)
            return

        # Get role. Allow people to use the command by pinging the role, or just naming it
        if isinstance(role_or_rolename, str):
            rolename = role_or_rolename
            try:
                role = ctx.guild.get_role(int(rolename.replace('<@&', '').replace('>', '')))
            # The input was not an int (i.e. the user gave the name of the role (e.g. ~addverified rolename))
            except ValueError:
                # Search over all roles and see if we get a match.
                roles = await ctx.guild.fetch_roles()
                for role in roles:
                    if role.name.lower() == rolename.lower():
                        role_to_assign = role
                        break
        else:
            role_to_assign = role_or_rolename

        if not role_to_assign:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error!",
                value=f"I couldn't find role {rolename}",
                inline=False)
            await ctx.send(embed=embed)
            return

        with Session(database_utils.DATABASE_ENGINE) as session:
            # TODO: Figure out how to catch the duplicate unique key error so I can insert first, then find if exists.
            # TODO: Just look in database_utils.VERIFIEDS instead of querying DB?
            result = session.query(database_utils.Verifieds)\
                                .filter_by(role_id=role_to_assign.id)\
                                .first()
            if result is None:
                stmt = sqlalchemy.insert(database_utils.Verifieds).values(role_id=role_to_assign.id, role_name=role_to_assign.name, 
                                                            server_id=ctx.guild.id, server_name=ctx.guild.name,
                                                            category=role_category)
                session.execute(stmt)
                session.commit()
            else:
                embed = discord_utils.create_embed()
                embed.add_field(name=f"{constants.FAILED}!",
                                value=f"Role {role_to_assign.mention} is already {result.category}!")
                await ctx.send(embed=embed)
                return

        if ctx.guild.id in database_utils.VERIFIEDS:
            database_utils.VERIFIEDS[ctx.guild.id].append(role_to_assign.id)
        else:
            database_utils.VERIFIEDS[ctx.guild.id] = [role_to_assign.id]

        embed = discord_utils.create_embed()
        embed.add_field(name=constants.SUCCESS,
                        value=f"Added the role {role_to_assign.mention} for this server set to {role_category}",
                        inline=False)
        await ctx.send(embed=embed)

    @command_predicates.is_owner_or_admin()
    @commands.command(name="lsverifieds", aliases=["listverifieds", "verifieds", "lsverified", "listverified"])
    async def lsverifieds(self, ctx):
        """List all verified roles within the server. Only available to server admins or bot owners.
        
        Usage: `~lsverifieds`"""
        logging_utils.log_command("lsverifieds", ctx.guild, ctx.channel, ctx.author)

        if ctx.guild.id in database_utils.VERIFIEDS and len(database_utils.VERIFIEDS[ctx.guild.id]) > 0:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Verifieds for {ctx.guild.name}",
                            value=f"{' '.join([ctx.guild.get_role(verified).mention for verified in database_utils.VERIFIEDS[ctx.guild.id]])}")
        else:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"No verified roles for {ctx.guild.name}",
                            value="Set up verified roles with `{ctx.prefix}addverified`")
            
        await ctx.send(embed=embed)

    @command_predicates.is_owner_or_admin()
    @commands.command(name="rmverified", aliases=["removeverified"])
    async def rmverified(self, ctx, role_or_rolename: Union[discord.Role, str]):
        """Remove a role from the list of verifieds. Only available to server admins or bot owners.
        
        Usage: `~rmverified @Verified`"""
        logging_utils.log_command("rmverified", ctx.guild, ctx.channel, ctx.author)

        # Get role. Allow people to use the command by pinging the role, or just naming it
        if isinstance(role_or_rolename, discord.Role):
            role_to_remove = role_or_rolename
        else:
            rolename = role_or_rolename
            try:
                role_to_remove = ctx.guild.get_role(int(rolename.replace('<@&', '').replace('>', '')))
            # The input was not an int (i.e. the user gave the name of the role (e.g. ~rmverified rolename))
            except ValueError:
                # Search over all roles and see if we get a match.
                roles = await ctx.guild.fetch_roles()
                for role in roles:
                    if role.name.lower() == rolename.lower():
                        role_to_remove = role
                        break
            if not role_to_remove:
                embed = discord_utils.create_embed()
                embed.add_field(name=f"{constants.FAILED}",
                                value=f"Sorry, I can't find role {rolename}.")
                await ctx.send(embed=embed)
                return

        with Session(database_utils.DATABASE_ENGINE) as session:
            result = session.query(database_utils.Verifieds).filter_by(server_id=ctx.guild.id, role_id=role_to_remove.id).all()
            if result is None:
                embed = discord_utils.create_embed()
                embed.add_field(name=f"{constants.FAILED}",
                                value=f"Role {role_to_remove.mention} is not verified in {ctx.guild.name}")
                await ctx.send(embed=embed)
                return
            else:
                for row in result:
                    session.delete(row)
                    session.commit()
        
        database_utils.VERIFIEDS[ctx.guild.id].pop(database_utils.VERIFIEDS[ctx.guild.id].index(role_to_remove.id))

        embed = discord_utils.create_embed()
        embed.add_field(name=f"{constants.SUCCESS}",
                        value=f"Removed {role_to_remove.mention} from Verifieds in {ctx.guild.name}")
        await ctx.send(embed=embed)

    @command_predicates.is_owner_or_admin()
    @commands.command(name="setprefix")
    async def setprefix(self, ctx, prefix: str):
        """Sets the bot prefix for the server. Only available to server admins or bot owners.
        
        Usage: `~setprefix !`"""
        logging_utils.log_command("setprefix", ctx.guild, ctx.channel, ctx.author)

        with Session(database_utils.DATABASE_ENGINE) as session:
            session.query(database_utils.Prefixes).filter_by(server_id=ctx.guild.id).\
                update({"prefix": prefix})
            session.commit()
        database_utils.PREFIXES[ctx.message.guild.id] = prefix
        embed = discord_utils.create_embed()
        embed.add_field(name=constants.SUCCESS,
                        value=f"Prefix for this server set to {prefix}",
                        inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(AdminCog(bot))