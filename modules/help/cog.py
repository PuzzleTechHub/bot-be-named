from discord.ext import commands
import constants
import discord


class HelpCog(commands.Cog):
    def __init__(self, bot):
        pass

    @commands.command(name='codebreaker')
    async def real_help(self, ctx):
        embed = discord.Embed(color=constants.EMBED_COLOR)
        embed.add_field(name="Welcome to Code-Breaker!", value=f"There's some {constants.CODE} that needs breaking, and you look like the right team for the job! There are a total of 5 levels, each of which will be 60 seconds. Within that time, you have to solve all the {constants.CODE}s of that level. Level 1 starts with 1 {constants.CODE} to solve, Level 2 with 2 {constants.CODE}s, and so on. Prepare well, and use the power of teamwork to solve it all quickly. Good luck!")
        embed.add_field(name="startrace", value=f"Starts the race!\n Usage: {constants.BOT_PREFIX}startrace", inline=False)
        embed.add_field(name="answer", value=f"Answer any of the current {constants.CODE}s. \nUsage: {constants.BOT_PREFIX}answer <your_answer>", inline=False)
        embed.add_field(name="help", value=f"If you are facing any problems with starting the race, tag @{constants.HINT}!")
        await ctx.send(embed=embed)

    @commands.command(name='fakehelp')
    async def fake_help(self, ctx):
        embed = discord.Embed(color=constants.EMBED_COLOR)
        embed.add_field(name='help', value=f"Welcome to {constants.BOT_NAME}! However, to actually use it, you need to say the right commands! Whenever a puzzle requires you to use the bot, it'll tell you what the correct command to use is! (Please do not brute-force the command names)\n\nIf you are still confused on how to use the bot, just tag @{constants.HINT}!")
        await ctx.send(embed=embed)
        

def setup(bot):
    bot.add_cog(HelpCog(bot))