from discord.ext import commands


def is_owner_or_admin():
    async def predicate(ctx):
        is_owner = await ctx.bot.is_owner(ctx.author)
        return is_owner or ctx.message.author.guild_permissions.administrator

    return commands.check(predicate)