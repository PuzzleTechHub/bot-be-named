from nextcord.ext import commands

import database

"""
Commands predicate utils. Informs all the functions on the rest of the modules what level of access the function caller has.
Currently set to multiple granularities we need most. See ~addperm and the rest of "Admin module" for more.
Used throughout the bot.
"""


def is_bot_owner():
    """
    Is bot owner.
    """

    async def predicate(ctx: commands.Context):
        return await ctx.bot.is_owner(ctx.author)

    return commands.check(predicate)


def is_admin():
    """
    Is an admin on the server.
    """

    async def predicate(ctx: commands.Context):
        if ctx.message.guild is None:
            return False
        return ctx.message.author.guild_permissions.administrator

    return commands.check(predicate)


def is_bot_owner_or_admin():
    """
    Is bot owner, or an admin.
    """

    async def predicate(ctx: commands.Context):
        is_bot_owner = await ctx.bot.is_owner(ctx.author)
        if ctx.message.guild is None:
            return False
        return is_bot_owner or ctx.message.author.guild_permissions.administrator

    return commands.check(predicate)


def is_tester():
    async def predicate(ctx: commands.Context):
        if ctx.message.guild is None:
            return False
        if ctx.guild.id in database.TESTERS:
            for role in ctx.author.roles:
                role_id = role.id
                if role_id in database.TESTERS[ctx.guild.id]:
                    return True
            return False
        else:
            return False

    return commands.check(predicate)


def is_solver():
    async def predicate(ctx: commands.Context):
        if ctx.message.guild is None:
            return False
        if ctx.guild.id in database.SOLVERS:
            for role in ctx.author.roles:
                role_id = role.id
                if role_id in database.SOLVERS[ctx.guild.id]:
                    return True
            return False
        else:
            return False

    return commands.check(predicate)


def is_verified():
    async def predicate(ctx: commands.Context):
        if ctx.message.guild is None:
            return False
        if ctx.guild.id in database.VERIFIEDS:
            for role in ctx.author.roles:
                role_id = role.id
                if role_id in database.VERIFIEDS[ctx.guild.id]:
                    return True
            return False
        else:
            return False

    return commands.check(predicate)


def is_trusted():
    async def predicate(ctx: commands.Context):
        if ctx.message.guild is None:
            return False
        if ctx.guild.id in database.TRUSTEDS:
            for role in ctx.author.roles:
                role_id = role.id
                if role_id in database.TRUSTEDS[ctx.guild.id]:
                    return True
            return False

    return commands.check(predicate)


def is_trusted_or_bot_owner():
    async def predicate(ctx: commands.Context):
        if ctx.message.guild is None:
            return False

        if await ctx.bot.is_owner(ctx.author):
            return True

        if ctx.guild.id in database.TRUSTEDS:
            for role in ctx.author.roles:
                role_id = role.id
                if role_id in database.TRUSTEDS[ctx.guild.id]:
                    return True
            return False

    return commands.check(predicate)


# The "Permission Category : ..." line each check's commands show in their docstring
PERMISSION_CATEGORIES = {
    "is_bot_owner": "Bot Owner only.",
    "is_admin": "Admin only.",
    "is_bot_owner_or_admin": "Admin or Bot Owner only.",
    "is_tester": "Tester Roles only.",
    "is_solver": "Solver Roles only.",
    "is_verified": "Verified Roles only.",
    "is_trusted": "Trusted Roles only.",
    "is_trusted_or_bot_owner": "Trusted Roles or Bot Owner only.",
}


def permission_category(command: commands.Command) -> str | None:
    """Who can use the command, worked out from its checks, e.g. "Solver Roles only.".
    Non-guarded commands return None. Several checks are joined with "and"."""
    names = [
        PERMISSION_CATEGORIES.get(check.__qualname__.split(".")[0])
        for check in command.checks
    ]
    if None in names:
        raise ValueError(f"{command.qualified_name} has a check with no category")
    return " and ".join(names) or None
