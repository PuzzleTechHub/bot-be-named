import nextcord
import database
import constants
from nextcord.ext import commands
from utils import discord_utils, command_predicates
from database import models
from typing import Union

"""
Admin module. Bundle of commands related to Bot management and permission categories,
as well as other commands useful for bot owners and admins generally.
"""


class AdminCog(commands.Cog, name="Admin"):
    """
    Commands for bot owners and bot management commands for server admins.
    """

    def __init__(self, bot):
        self.bot = bot

    ################################
    # PERMISSION CATEGORY COMMANDS #
    ################################

    @command_predicates.is_bot_owner_or_admin()
    @commands.command(
        name="addperm", aliases=["addverifieds", "addverified", "addperms"]
    )
    async def addperm(
        self,
        ctx: commands.Context,
        role_permissions: str,
        role_or_rolename: Union[nextcord.Role, str],
    ):
        """Add a new Permission Category for a given role on this server. Only available to server admins or bot owners.

        This command is necessary before most to all bot commands. Nearly all commands are restricted to some Permission Category or the other.
        The Permission Categories available are - Verified, Trusted, Solver, Tester.

        See `~info` for more info.

        Permission Category : Admin or Bot Owner Roles only.
        Usage: `~addperm Verified @VerifiedRoleName`
        Usage: `~addperm Trusted @everyone`
        """
        embed = discord_utils.create_embed()

        if role_permissions not in database.VERIFIED_CATEGORIES:
            await discord_utils.send_failure(
                ctx,
                f"`role_permissions` must be in {', '.join(database.VERIFIED_CATEGORIES)}, "
                f"but you supplied {role_permissions}",
            )
            return

        role_to_assign = await discord_utils.find_role(ctx, role_or_rolename)

        # Ensure role exists
        if role_to_assign is None:
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Error!",
                value=f"I couldn't find role {role_or_rolename}",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        if not database.add_permission_role(
            ctx.guild.id,
            ctx.guild.name,
            role_to_assign.id,
            role_to_assign.name,
            role_permissions,
        ):
            await discord_utils.send_failure(
                ctx,
                f"Role {role_to_assign.mention} is already `{role_permissions}`!",
            )
            return

        embed.add_field(
            name="Success",
            value=f"Added the role {role_to_assign.mention} for this server set to `{role_permissions}`",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_bot_owner_or_admin()
    @commands.command(
        name="listperm",
        aliases=[
            "lsperms",
            "listperms",
            "lsperm",
        ],
    )
    async def listperm(self, ctx: commands.Context, role_permissions: str):
        """List all roles in the given Permission Category within the server.

        See also: `~addperms`

        Permission Category : Admin or Bot Owner Roles only.
        Usage: `~listperm Verified`
        """
        embed = discord_utils.create_embed()

        if role_permissions not in database.VERIFIED_CATEGORIES:
            await discord_utils.send_failure(
                ctx,
                f"`role_permissions` must be in `{', '.join(database.VERIFIED_CATEGORIES)}`, "
                f"but you supplied `{role_permissions}`",
            )
            return

        cache_map = database.PERMISSION_CACHES

        if (
            ctx.guild.id in cache_map[role_permissions]
            and len(cache_map[role_permissions][ctx.guild.id]) > 0
        ):
            embed.add_field(
                name=f"{role_permissions}s for {ctx.guild.name}",
                value=f"{' '.join([ctx.guild.get_role(role).mention for role in cache_map[role_permissions][ctx.guild.id]])}",
                inline=False,
            )
        else:
            embed.add_field(
                name=f"No {role_permissions} roles for {ctx.guild.name}",
                value=f"Set up `{role_permissions}` roles with `{ctx.prefix}addverified`",
                inline=False,
            )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_bot_owner_or_admin()
    @commands.command(
        name="removeperm",
        aliases=["removeperms", "rmperms", "rmverified", "rmperm"],
    )
    async def removeperm(
        self,
        ctx: commands.Context,
        role_permissions: str,
        role_or_rolename: Union[nextcord.Role, str],
    ):
        """Remove a role from the given Permission Category within the server.
        Only available to server admins or bot owners.

        Permission Category : Admin or Bot Owner Roles only.
        Usage: `~removeperm Verified @VerifiedRoleName`
        Usage: `~removeperm Trusted @everyone`
        """
        embed = discord_utils.create_embed()

        if role_permissions not in database.VERIFIED_CATEGORIES:
            await discord_utils.send_failure(
                ctx,
                f"`role_permissions` must be in {', '.join(database.VERIFIED_CATEGORIES)}, "
                f"but you supplied {role_permissions}",
            )
            return

        role_to_remove = await discord_utils.find_role(ctx, role_or_rolename)
        if role_to_remove is None:
            await discord_utils.send_failure(
                ctx,
                f"Sorry, I can't find role `{role_or_rolename}`.",
            )
            return

        if not database.delete_permission_role(
            ctx.guild.id, role_to_remove.id, role_permissions
        ):
            await discord_utils.send_failure(
                ctx,
                f"Role {role_to_remove.mention} is not `{role_permissions}` in `{ctx.guild.name}`",
            )
            return

        embed.add_field(
            name="Success",
            value=f"Removed {role_to_remove.mention} from `{role_permissions}` in `{ctx.guild.name}`",
        )
        await discord_utils.send_message(ctx, embed)

    ##################
    # GUILD COMMANDS #
    ##################

    @command_predicates.is_bot_owner()
    @commands.command(
        name="commonmemberguilds",
        aliases=["commonguild", "guildcommon", "commonguildmembers"],
    )
    async def commonmemberguilds(
        self,
        ctx: commands.Context,
        guild_1: Union[nextcord.Guild, str],
        guild_2: Union[nextcord.Guild, str],
    ):
        """List all users in common between 2 guilds that the bot is in.

        Permission Category : Bot Owner Roles only.
        See also : `~lsguilds`
        Usage: `~commonmemberguilds "Guild1" "Guild2"`
        """
        embed = discord_utils.create_embed()

        guild_1_guild = await discord_utils.find_guild(ctx, guild_1)

        guild_2_guild = await discord_utils.find_guild(ctx, guild_2)

        if guild_1_guild is None:
            await discord_utils.send_failure(
                ctx,
                f"There is no guild named `{guild_1}`. Please double check the spelling.",
            )
            return

        if guild_2_guild is None:
            await discord_utils.send_failure(
                ctx,
                f"There is no guild named `{guild_2}`. Please double check the spelling.",
            )
            return

        await discord_utils.ensure_members_cached(guild_1_guild)
        await discord_utils.ensure_members_cached(guild_2_guild)
        members_guild_1 = guild_1_guild.members
        members_guild_2 = guild_2_guild.members

        # Skip the bot or "No members in common" will never be reached
        members_common = [
            member
            for member in members_guild_1
            if member in members_guild_2 and member != ctx.bot.user
        ]

        if len(members_common) > 0:
            members_string = " ".join(
                [
                    f"{member.mention} - `@{member.name}` \n "
                    for member in members_common
                ]
            )
            embed.add_field(
                name="Members common",
                value=f"Members common in `{guild_1}` and `{guild_2}`\n"
                f"{members_string}",
                inline=False,
            )
        else:
            embed.add_field(
                name="No members in common",
                value=f"The bot has no members in common between `{guild_1}` and `{guild_2}`",
                inline=False,
            )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_bot_owner()
    @commands.command(
        name="guildowner",
        aliases=["ownerguild"],
    )
    async def guildowner(
        self,
        ctx: commands.Context,
        guild_name: Union[nextcord.Guild, str],
    ):
        """Mentions the guild owner for a specific guild the bot is in.

        Note - This command is planned to be used extremely sparingly and for important (usually notification related) reasons only.

        Permission Category : Bot Owner Roles only.
        Usage: `~guildowner "Guild1"`
        """
        embed = discord_utils.create_embed()

        guild = await discord_utils.find_guild(ctx, guild_name)

        if guild is None:
            await discord_utils.send_failure(
                ctx,
                f"There is no guild named `{guild_name}`. Please double check the spelling.",
            )
            return

        owner = guild.owner
        embed.add_field(
            name="Guild owner : ",
            value=f"Guild owner for `{guild}` : {owner.mention} : `{owner.display_name}` : `{owner.name}`",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_bot_owner()
    @commands.command(
        name="lsguilds",
        aliases=["listguilds"],
    )
    async def lsguilds(self, ctx: commands.Context):
        """List all guilds that the bot is in, with their owners.

        Permission Category : Bot Owner Roles only.
        Usage: `~lsguilds`
        """
        embed = discord_utils.create_embed()

        guilds = ctx.bot.guilds
        guilds = sorted(guilds, key=lambda guild: guild.name)

        if len(guilds) > 0:
            guilds_string = " ".join(
                [
                    f"`{guild.name}` - `@{guild.owner.name if guild.owner else guild.owner_id}` \n"
                    for guild in guilds
                ]
            )
            embed.add_field(
                name=f"Guilds for {ctx.bot.user.name} = {len(guilds)}",
                value=f"Guilds for {ctx.bot.user.mention}\n{guilds_string}",
                inline=False,
            )
        else:
            embed.add_field(
                name="No guilds for the bot",
                value="The bot is currently not in any guilds.",
                inline=False,
            )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_bot_owner()
    @commands.command(
        name="quitguild",
    )
    async def quitguild(
        self, ctx: commands.Context, guild_name: Union[nextcord.Guild, str]
    ):
        """Quit a guild.

        Permission Category : Bot Owner Roles only.
        Usage: `~quitguild "Guildname"`
        """
        embed = discord_utils.create_embed()

        guild = await discord_utils.find_guild(ctx, guild_name)

        if guild is None:
            await discord_utils.send_failure(
                ctx,
                f"There is no guild named `{guild_name}`. Please double check the spelling.",
            )
            return

        try:
            await guild.leave()

        except nextcord.HTTPException:
            await discord_utils.send_failure(
                ctx,
                f"Could not leave guild `{guild_name}`",
            )
            return

        embed.add_field(
            name="Success",
            value=f"Successfully left guild `{guild_name}`",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_bot_owner_or_admin()
    @commands.command(name="setprefix")
    async def setprefix(self, ctx: commands.Context, prefix: str):
        """Sets the bot prefix for the server.

        Permission Category : Admin or Bot Owner Roles only.
        Usage: `~setprefix !`
        """
        embed = discord_utils.create_embed()

        database.set_prefix(ctx.guild.id, prefix)
        embed.add_field(
            name="Success",
            value=f"Prefix for this server set to {prefix}",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)

    ######################
    # BOT CACHE COMMANDS #
    ######################

    @command_predicates.is_bot_owner_or_admin()
    @commands.command(
        name="reloaddatabasecache", aliases=["reloaddbcache", "dbcachereload"]
    )
    async def reloaddatabasecache(self, ctx: commands.Context):
        """Reloads this server's custom commands, permission roles and prefix, channel mirrors plus
        the global custom commands. This is useful when we're editing commands or playing with the Database.

        Permission Category : Admin or Bot Owner Roles only.
        Usage: `~reloaddatabasecache`
        """
        embed = discord_utils.create_embed()
        guild_id = ctx.guild.id

        # Read from the database first
        custom_commands = database.get_server_custom_commands(guild_id)
        global_commands = database.get_server_custom_commands(constants.DB_GLOBAL)
        role_ids = database.get_server_permission_roles(guild_id)
        prefix = database.get_server_prefix(guild_id)

        # Mirrors are cached by the channel's ID, so reload al of them.
        channel_mirrors: dict[int, set[int]] = database.get_channel_mirrors()

        # Swap the new values in since everything was read
        database.CUSTOM_COMMANDS[guild_id] = custom_commands
        database.CUSTOM_COMMANDS[constants.DB_GLOBAL] = global_commands
        embed.add_field(
            name="Success",
            value="Successfully reloaded command cache.",
            inline=False,
        )

        database.VERIFIEDS[guild_id] = role_ids[models.VERIFIED]
        database.TRUSTEDS[guild_id] = role_ids[models.TRUSTED]
        database.SOLVERS[guild_id] = role_ids[models.SOLVER]
        database.TESTERS[guild_id] = role_ids[models.TESTER]
        embed.add_field(
            name="Success",
            value="Successfully reloaded role cache.",
            inline=False,
        )

        database.PREFIXES[guild_id] = prefix
        embed.add_field(
            name="Success",
            value="Successfully reloaded prefix cache.",
            inline=False,
        )

        database.CHANNEL_MIRRORS.clear()
        database.CHANNEL_MIRRORS.update(channel_mirrors)
        embed.add_field(
            name="Success",
            value="Successfully reloaded channel mirrors cache.",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)


def setup(bot):
    bot.add_cog(AdminCog(bot))
