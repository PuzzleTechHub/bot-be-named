from discord.ext import commands
from utils import database_utils


def is_owner_or_admin():
    async def predicate(ctx):
        if ctx.message.guild is None:
            return False
        is_owner = await ctx.bot.is_owner(ctx.author)
        return is_owner or ctx.message.author.guild_permissions.administrator
    return commands.check(predicate)


def is_verified():
    async def predicate(ctx):
        if ctx.message.guild is None:
            return False
        if ctx.guild.id in database_utils.VERIFIEDS:
            for role_id in [role.id for role in ctx.author.roles]:
                if role_id in database_utils.VERIFIEDS[ctx.guild.id]:
                    return True
            return False  
        else:
            return False
    return commands.check(predicate)
