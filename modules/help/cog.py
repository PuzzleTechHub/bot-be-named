from discord.ext import commands
import constants
import discord
# KEV
from modules.code.cog import CodeCog
import inspect

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


    @commands.command(name='kevhelp')
    async def kevhelp(self, ctx):
        embed = discord.Embed(color=constants.EMBED_COLOR)
        print(inspect.getmembers(CodeCog))
        print(dir(CodeCog))
        print(CodeCog.__cog_commands__)
        for func in CodeCog.__cog_commands__:#inspect.getmembers(CodeCog, predicate=inspect.iscoroutine):
            print(func)
            print(dir(func))

            #print(func.help)
            # func is a 2-tuple of (func_name, function)
            if func.__doc__ is None:#func[1].__doc__ is None: 
                continue
            #print(func.__doc__)
            embed.add_field(name=func.name, value=f"{func.help}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='adminhelp')
    @commands.has_role('bot-whisperer')
    async def adminhelp(self, ctx):
        embed = discord.Embed(color=constants.EMBED_COLOR)
        embed.add_field(name="startrace", value=f"Start a race.\nUsage: {constants.BOT_PREFIX}startrace\nNeeds to be done in a channel that is given access with {constants.BOT_PREFIX}addchannel", inline=False)
        embed.add_field(name="answer", value=f"Answer a {constants.CODE}.\nUsage: {constants.BOT_PREFIX}answer <your_answer>\nNeeds to be done in the same channel as a currently running race.", inline=False)
        # embed.add_field(name="giveup", value=f"Returns the solution\nUsage: {constants.BOT_PREFIX}giveup\nNOTE: For emergencies only.")
        embed.add_field(name="giveup", value=f"Never give up!\nUsage: ~giveup")
        embed.add_field(name="nameteam", value=f"Name a team.\nUsage: {constants.BOT_PREFIX}nameteam <(1,2,3)> <new_name>\nNote: Team 3 is reserved for testers.", inline=False)
        embed.add_field(name="getname", value=f"Get the name of a team.\nUsage: {constants.BOT_PREFIX}getname <(1,2,3)>", inline=False)
        embed.add_field(name="getchannels", value=f"Get the name and bound channels for all teams.\nUsage: {constants.BOT_PREFIX}getchannels", inline=False)
        embed.add_field(name="addchannel", value=f"Bind a channel to a team.\nUsage: {constants.BOT_PREFIX}addchannel <channel_name> <(1,2,3)>\nNote: use 0 for channel name to set that team's channel to NONE", inline=False)
        embed.add_field(name="reload", value=f"Reload the google sheet to update {constants.CODE} values.\nUsage: {constants.BOT_PREFIX}reload\nNote: this is already performed hourly without the command.", inline=False)
        embed.add_field(name="reset", value=f"Reset the bot as if it has just loaded up\nUsage: {constants.BOT_PREFIX}reset\nNote: Does not reload google sheet. Use {constants.BOT_PREFIX}reload for that", inline=False)
        embed.add_field(name="codebreaker", value=f"Gives the help the solvers will see, which gives them info on startpuzzle and answer only.\nUsage: {constants.BOT_PREFIX}codebreaker", inline=False)
        embed.add_field(name="help", value=f"A fun and useful help command XD\nUsage: {constants.BOT_PREFIX}help", inline=False)
        await ctx.send(embed=embed)
        

def setup(bot):
    bot.add_cog(HelpCog(bot))