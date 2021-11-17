import typing
import discord
from discord.ext import commands
import aiohttp
import io
from emoji import EMOJI_ALIAS_UNICODE_ENGLISH as EMOJIS

import constants
from utils import discord_utils, logging_utils, command_predicates


class RoleManagementCog(commands.Cog, name="Role Management"):
    """Role Management Commands"""

    def __init__(self, bot):
        self.bot = bot

    #################
    # ROLE COMMANDS #
    #################

    @commands.has_any_role(*constants.TRUSTED)
    @commands.command(name="assignrole", aliases=["giverole","rolegive","roleassign"])
    async def assignrole(self, ctx, rolename: str, *args):
        """Assign a role to a list of users. If the role does not already exist, then creates the role.
        The role can be mentioned or named. The users must be mentioned.

        Category : Trusted Roles only.        
        Usage: `~assignrole @RoleName @User1 @User2`
        Usage: `~assignrole "NewRoleName" @User1`
        """
        logging_utils.log_command("assignrole", ctx.guild, ctx.channel, ctx.author)
        # User didn't include any people to get the role
        if len(args) < 1:
            embed = discord_utils.create_no_argument_embed("Users to give the role")
            await ctx.send(embed=embed)
            return

        # Get role. Allow people to use the command by pinging the role, or just naming it
        role_to_assign = None
        try:
            # TODO: Fix replace?
            role_to_assign = ctx.guild.get_role(int(rolename.replace('<@&', '').replace('>', '')))
        # The input was not an int (i.e. the user gave the name of the role (e.g. ~deleterole rolename))
        except ValueError:
            # Search over all roles
            roles = await ctx.guild.fetch_roles()
            for role in roles:
                if role.name.lower() == rolename.lower():
                    role_to_assign = role
                    break

        embed = discord_utils.create_embed()
        # Cannot find the role, so we'll make one
        if not role_to_assign:
            try:
                role_to_assign = await ctx.guild.create_role(name=rolename)
                await role_to_assign.edit(mentionable=True)
                embed.add_field(name=f"Created role {rolename}",
                                value=f"Could not find role {rolename}, so I created it.",
                                inline=False)
            except discord.Forbidden:
                embed.add_field(name=f"Error!",
                                value=f"I couldn't find role {rolename}, so I tried to make it. But I don't have "
                                      f"permission to add a role in this server. Do I have the `add_roles` permission?",
                                inline=False)
                await ctx.send(embed=embed)
                return

        users_with_role_list = []
        for unclean_username in args:
            # Get the user
            try:
                # TODO: Fix replace?
                user = ctx.guild.get_member(int(unclean_username.replace('<@', '').replace('>', '').replace('!', '')))
                # User not found
                if not user:
                    embed.add_field(name="Error Finding User!",
                                    value=f"Could not find user {unclean_username}. Did you ping them? I won't accept raw usernames",
                                    inline=False)
                    continue
            # User id not provided or bad argument
            except ValueError:
                embed.add_field(name="Error Finding User!",
                                value=f"Could not find user {unclean_username}. Did you ping them? I won't accept raw usernames",
                                inline=False)
                continue
            # Assign the role
            try:
                await user.add_roles(role_to_assign)
                users_with_role_list.append(user)
            except discord.Forbidden:
                embed.add_field(name="Error Assigning Role!",
                                value=f"I could not assign {role_to_assign.mention} to {user}. Either this role is "
                                      f"too high up on the roles list for them, or I do not have permissions to give "
                                      f"them this role. Please ensure I have the `manage_roles` permission.",
                                inline=False)
        if len(users_with_role_list) < 1:
            embed.insert_field_at(0,
                                  name="Failed!",
                                  value=f"Could not assign role {role_to_assign.mention} to anyone.",
                                  inline=False)
        else:
            embed.add_field(name="Success!",
                            value=f"Added the {role_to_assign.mention} role to {', '.join([user.mention for user in users_with_role_list])}",
                            inline=False)
        await ctx.send(embed=embed)

    @commands.has_any_role(*constants.TRUSTED)
    @commands.command(name="createrole", aliases=["makerole"])
    async def createrole(self, ctx, rolename: str, color: str = None, mentionable: bool = True):
        """Create a role in the server. 

        Category : Trusted Roles only.        
        Usage: `~makerole RoleName`
        Usage: `~makerole RoleName d0d0ff True` (colour of role, if the role is mentionable)
        """
        logging_utils.log_command("createrole", ctx.guild, ctx.channel, ctx.author)

        # Convert color from hex str into int
        if color:
            try:
                color = discord.Color(int(color, 16))
            except ValueError:
                embed = discord_utils.create_embed()
                embed.add_field(name=f"Error!",
                                value=f"I didn't understand that color. Make sure you use a valid hex code!",
                                inline=False)
                await ctx.send(embed=embed)
                return
        else:
            color = discord.Color.default()

        try:
            role = await ctx.guild.create_role(name=rolename, color=color, mentionable=mentionable)
        except discord.Forbidden:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error!",
                            value=f"I don't have permission to add a role in this server. Do I have the `add_roles` permission?",
                            inline=False)
            await ctx.send(embed=embed)
            return
        embed = discord_utils.create_embed()
        embed.add_field(name="Success!",
                        value=f"Created role {role.mention}!",
                        inline=False)
        await ctx.send(embed=embed)

    @command_predicates.is_owner_or_admin()
    @commands.command(name="deleterole")
    async def deleterole(self, ctx, rolename: str):
        """Remove a role from the server

        Category : Admin or Bot Owner only.
        Usage: `~removerole "RoleName"`
        Usage: `~removerole @RoleMention`
        """
        logging_utils.log_command("deleterole", ctx.guild, ctx.channel, ctx.author)

        embed = discord_utils.create_embed()
        role_to_delete = None
        # Try to find the role if the user mentioned it (e.g. ~deleterole @rolename)
        try:
            # TODO: Fix replace?
            role_to_delete = ctx.guild.get_role(int(rolename.replace('<@&', '').replace('>', '')))
        # The input was not an int (i.e. the user gave the name of the role (e.g. ~deleterole rolename))
        except ValueError:
            # Search over all roles
            roles = await ctx.guild.fetch_roles()
            for role in roles:
                if role.name.lower() == rolename.lower():
                    role_to_delete = role
                    break
        # Delete the role or error if it didn't work.
        try:
            if role_to_delete:
                role_name = role_to_delete.name
                await role_to_delete.delete()
                embed.add_field(name="Success!",
                                value=f"Removed role {role_name}",
                                inline=False)
                await ctx.send(embed=embed)
                return
            else:
                embed.add_field(name=f"Error!",
                                value=f"I can't find {rolename} in this server. Make sure you check the spelling and punctuation!",
                                inline=False)
                await ctx.send(embed=embed)
                return
        except discord.Forbidden:
            embed.add_field(name=f"Error!",
                            value=f"I don't have permission to add a role in this server. Do I have the `add_roles` permission?",
                            inline=False)
            await ctx.send(embed=embed)
            return

    @commands.command(name="listroles", aliases=["lsroles", "listrole", "lsrole"])
    async def listroles(self, ctx):
        """List all roles in the server

        Usage:`~listroles`
        """
        logging_utils.log_command("listroles", ctx.guild, ctx.channel, ctx.author)
        roles = await ctx.guild.fetch_roles()
        embed = discord.Embed(title=f"Roles in {ctx.guild.name}",
                              description=f"{', '.join([role.mention for role in roles])}",
                              color = constants.EMBED_COLOR)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(RoleManagementCog(bot))
