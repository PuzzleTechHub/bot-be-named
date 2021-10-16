import os
import discord
from discord.ext import commands
import constants
from utils import discord_utils, logging_utils, admin_utils, google_utils, database_utils
from sqlalchemy.orm import Session
from sqlalchemy import insert


class AdminCog(commands.Cog, name="Admin"):
    """Downloads a channel's history and sends it as a file to the user"""
    def __init__(self, bot):
        self.bot = bot
        self.gspread_client = google_utils.create_gspread_client()
        self.prefix_sheet = self.gspread_client.open_by_key(os.getenv('MASTER_SHEET_KEY')).worksheet(constants.PREFIX_TAB_NAME)

    @admin_utils.is_owner_or_admin()
    @commands.command(name="addverified")
    async def addverified(self, ctx, rolename, role_category: str = "Verified"):
        """Add a new verified category for this server. Only available to server admins or bot owners
        
        Usage: `~addverified @Verified Verified"""
        logging_utils.log_command("addverified", ctx.channel, ctx.author)

        if len(rolename) < 1:
            embed = discord_utils.create_no_argument_embed("Role or Role category")
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
        role_to_assign = None
        try:
            role_to_assign = ctx.guild.get_role(int(rolename.replace('<@&', '').replace('>', '')))
        # The input was not an int (i.e. the user gave the name of the role (e.g. ~addverified rolename))
        except ValueError:
            # Search over all roles and see if we get a match.
            roles = await ctx.guild.fetch_roles()
            for role in roles:
                if role.name.lower() == rolename.lower():
                    role_to_assign = role
                    break

        if not role_to_assign:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error!",
                value=f"I couldn't find role {rolename}",
                inline=False)
            await ctx.send(embed=embed)
            return

        # values = [ctx.message.guild.name, str(role_prefix_sheet = gspread_client.open_by_key(os.getenv('MASTER_SHEET_KEY')).worksheet(constants.PREFIX_TAB_NAME)to_assign.id), verifiedname]
        # VERIFIED_SHEET.append_row(values)
        with Session(constants.DATABASE_ENGINE) as session:
            stmt = insert(database_utils.Verifieds).values(role_id=role_to_assign.id, role_name=role_to_assign.name, 
                                                           server_id=ctx.guild.id, server_name=ctx.guild.name,
                                                           category=role_category)
            session.execute(stmt)
            session.commit()

        constants.VERIFIEDS = admin_utils.get_verifieds()

        embed = discord_utils.create_embed()
        embed.add_field(name=constants.SUCCESS,
                        value=f"Added the role {role_to_assign.mention} for this server set to {role_category}",
                        inline=False)
        await ctx.send(embed=embed)

    @admin_utils.is_owner_or_admin()
    @commands.command(name="lsverifieds", aliases=["listverifieds", "verifieds", "lsverified", "listverified"])
    async def lsverifieds(self, ctx):
        """List all verified roles within the server
        
        Usage: `~lsverifieds`"""
        logging_utils.log_command("lsverifieds", ctx.channel, ctx.author)

        if ctx.guild.id in constants.VERIFIEDS:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Verifieds for {ctx.guild.name}",
                            value=f"{' '.join([ctx.guild.get_role(verified).mention for verified in constants.VERIFIEDS[ctx.guild.id]])}")
        else:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"No verified roles for {ctx.guild.name}",
                            value="Set up verified roles with `{ctx.prefix}addverified`")
            
        await ctx.send(embed=embed)

    @admin_utils.is_owner_or_admin()
    @commands.command(name="rmverified", aliases=["removeverified"])
    async def rmverified(self, ctx, rolename):
        """Remove a role from the list of verifieds
        
        Usage: `~rmverified @Verified"""
        logging_utils.log_command("rmverified", ctx.channel, ctx.author)

        # Get role. Allow people to use the command by pinging the role, or just naming it
        role_to_remove = None
        try:
            role_to_remove = ctx.guild.get_role(int(rolename.replace('<@&', '').replace('>', '')))
        # The input was not an int (i.e. the user gave the name of the role (e.g. ~rmverified rolename))
        except ValueError:
            # Search over all roles and see if we get a match.
            roles = await ctx.guild.fetch_roles()
            for role in roles:
                if role.name.lower() == rolename.lower():
                    role_to_assign = role
                    break
        if not role_to_remove:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"{constants.FAILED}",
                            value=f"Sorry, I can't find role {rolename}.")
            await ctx.send(embed=embed)
            return

        with Session(constants.DATABASE_ENGINE) as session:
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
        
        constants.VERIFIEDS = admin_utils.get_verifieds()

        embed = discord_utils.create_embed()
        embed.add_field(name=f"{constants.SUCCESS}",
                        value=f"Removed {role_to_remove.mention} from Verifieds in {ctx.guild.name}")
        await ctx.send(embed=embed)

    @admin_utils.is_owner_or_admin()
    @commands.command(name="setprefix")
    async def setprefix(self, ctx, prefix: str):
        """Sets the bot prefix for the server. Only available to server admins or bot owners"""
        logging_utils.log_command("setprefix", ctx.channel, ctx.author)
        find_cell = self.prefix_sheet.find(str(ctx.message.guild.id))
        self.prefix_sheet.update_cell(find_cell.row, find_cell.col+1, prefix)
        constants.PREFIXES[ctx.message.guild.id] = prefix

        with Session(constants.DATABASE_ENGINE) as session:
            session.query(database_utils.Prefixes).filter_by(server_id=ctx.guild.id).\
                update({"prefix": prefix})
            session.commit()
        embed = discord_utils.create_embed()
        embed.add_field(name=constants.SUCCESS,
                        value=f"Prefix for this server set to {prefix}",
                        inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(AdminCog(bot))