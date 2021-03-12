from discord.ext import commands
import constants
import discord


class FredDeadCog(commands.Cog):
    def __init__(self, bot):
        pass
    
    @commands.command(name='dead')
    async def dead(self, ctx):
        embed = discord.Embed(color=constants.EMBED_COLOR)
        embed.add_field(name="Oops!", value=f"Sorry, that was a misspelling on our part! You should not have been using {constants.BOT_PREFIX}dead. Instead, have you tried using {constants.BOT_PREFIX}fred ?", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='fred')
    async def fred(self, ctx):
        embed = discord.Embed(color=constants.EMBED_COLOR)
        embed.add_field(name='Congratulations!', value="You are this close to finding the answer! Now for your final step, answer this question!", inline=False)
        embed.add_field(name="Final Question", value="According to the Daily Prophet article written by Andy Smudgley, a descending __ distracted Armando Dippet", inline=False)
        await ctx.send(embed=embed)



def setup(bot):
    bot.add_cog(FredDeadCog(bot))