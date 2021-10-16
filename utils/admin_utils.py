from discord.ext import commands
from sqlalchemy.orm import Session
from utils import database_utils
import constants


def is_owner_or_admin():
    async def predicate(ctx):
        is_owner = await ctx.bot.is_owner(ctx.author)
        return is_owner or ctx.message.author.guild_permissions.administrator

    return commands.check(predicate)


def is_verified():
    async def predicate(ctx):
        if ctx.guild.id in constants.VERIFIEDS:
            for role_id in [role.id for role in ctx.author.roles]:
                if role_id in constants.VERIFIEDS[ctx.guild.id]:
                    return True
            return False  
        else:
            return False
    return commands.check(predicate)


def get_prefixes():
    prefixes = {}
    with Session(constants.DATABASE_ENGINE) as session:
        result = session.query(database_utils.Prefixes).all()
        for row in result:
            prefixes[row.server_id] = row.prefix
    return prefixes


def get_verifieds():
    verifieds = {}
    with Session(constants.DATABASE_ENGINE) as session:
        result = session.query(database_utils.Verifieds).filter_by(category="Verified").all()
        for row in result:
            if row.server_id in verifieds:
                verifieds[row.server_id].append(row.role_id)
            else:
                verifieds[row.server_id] = [row.role_id] 
    return verifieds
