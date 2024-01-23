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

    async def predicate(ctx):
        return await ctx.bot.is_owner(ctx.author)

    return commands.check(predicate)


def is_admin():
    """
    Is an admin on the server.
    """

    async def predicate(ctx):
        if ctx.message.guild is None:
            return False
        return ctx.message.author.guild_permissions.administrator

    return commands.check(predicate)


def is_bot_owner_or_admin():
    """
    Is bot owner, or an admin.
    """

    async def predicate(ctx):
        is_bot_owner = await ctx.bot.is_owner(ctx.author)
        if ctx.message.guild is None:
            return False
        return is_bot_owner or ctx.message.author.guild_permissions.administrator

    return commands.check(predicate)


def is_guild_owner():
    """
    Is guild owner.
    """

    async def predicate(ctx):
        if ctx.message.guild is None:
            return False
        return ctx.author == ctx.guild.owner

    return commands.check(predicate)


def is_tester():
    async def predicate(ctx):
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
    async def predicate(ctx):
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
    async def predicate(ctx):
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
    async def predicate(ctx):
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
    async def predicate(ctx):
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
