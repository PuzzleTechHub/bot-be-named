import typing
import discord
from discord.ext import commands
import aiohttp
import io
from emoji import EMOJI_ALIAS_UNICODE_ENGLISH as EMOJIS
from typing import Union

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
    @commands.command(name="assignrole", aliases=["giverole","rolegive","roleassign","makerole","createrole"])
    async def assignrole(self, ctx, rolename: Union[discord.Role,str], *args):
        """Assign a role to a list of users. If the role does not already exist, then creates the role.
        The role can be mentioned or named. The users must be mentioned. 
        The role created is always mentionable by all users.

        Category : Trusted Roles only.        
        Usage: `~assignrole @RoleName @User1 @User2`
        Usage: `~assignrole "NewRoleName" @User1`
        Usage: `~makerole "NewRolename"` (if no users given, just creates the role)
        """
        logging_utils.log_command("assignrole", ctx.guild, ctx.channel, ctx.author)

        #If user managed to tag a channel name instead of typing
        role_to_assign = None
        if(isinstance(rolename, str)):
            roles = await ctx.guild.fetch_roles()
            for role in roles:
                if role.name.lower() == rolename.lower():
                    role_to_assign = role
                    break
        else:
            role_to_assign=rolename

        embed = discord_utils.create_embed()
        # Cannot find the role, so we'll make one
        if not role_to_assign:
            try:
                role_to_assign = await ctx.guild.create_role(name=rolename)
                await role_to_assign.edit(mentionable=True)
                embed.add_field(name=f"Created role {rolename}",
                                value=f"Could not find role `{rolename}`, so I created it.",
                                inline=False)
            except discord.Forbidden:
                embed.add_field(name=f"Error!",
                                value=f"I couldn't find role `{rolename}`, so I tried to make it. But I don't have "
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
                                    value=f"Could not find user `{unclean_username}`. Did you ping them? I won't accept raw usernames",
                                    inline=False)
                    continue
            # User id not provided or bad argument
            except ValueError:
                embed.add_field(name="Error Finding User!",
                                value=f"Could not find user `{unclean_username}`. Did you ping them? I won't accept raw usernames",
                                inline=False)
                continue
            # Assign the role
            try:
                await user.add_roles(role_to_assign)
                users_with_role_list.append(user)
            except discord.Forbidden:
                embed.add_field(name="Error Assigning Role!",
                                value=f"I could not assign `{role_to_assign.mention}` to `{user}`. Either this role is "
                                      f"too high up on the roles list for them, or I do not have permissions to give "
                                      f"them this role. Please ensure I have the `manage_roles` permission.",
                                inline=False)
        if len(users_with_role_list) < 1:
            embed.insert_field_at(0,
                                  name="Complete!",
                                  value=f"Did not assign role `{role_to_assign.mention}` to anyone.",
                                  inline=False)
        else:
            embed.add_field(name="Success!",
                            value=f"Added the `{role_to_assign.mention}` role to {', '.join([user.mention for user in users_with_role_list])}",
                            inline=False)
        await ctx.send(embed=embed)

    @command_predicates.is_owner_or_admin()
    @commands.command(name="deleterole")
    async def deleterole(self, ctx, rolename: Union[discord.Role, str]):
        """Delete a role from the server

        Category : Admin or Bot Owner only.
        Usage: `~deleterole "RoleName"`
        Usage: `~deleterole @RoleMention`
        """
        logging_utils.log_command("deleterole", ctx.guild, ctx.channel, ctx.author)

        embed = discord_utils.create_embed()
        role_to_delete = None
        if isinstance(rolename, discord.Role):
            role_to_delete = rolename
        # The input was not an int (i.e. the user gave the name of the role (e.g. ~deleterole rolename))
        else:
            # Search over all roles
            roles = await ctx.guild.fetch_roles()
            for role in roles:
                if role.name.lower() == rolename.lower():
                    role_to_delete = role
                    break
            if role_to_delete is None:
                embed.add_field(name=f"Error!",
                                value=f"I can't find `{rolename}` in this server. Make sure you check the spelling and punctuation!",
                                inline=False)
                await ctx.send(embed=embed)
                return
        # Delete the role or error if it didn't work.
        try:
            role_name = role_to_delete.name
            await role_to_delete.delete()
            embed.add_field(name="Success!",
                            value=f"Removed role `{role_name}`",
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
