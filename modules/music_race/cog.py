import constants
import discord
import re
from discord.ext import commands
from utils import discord_utils
import modules.perfect_pitch

answers = ["","GHOSTBUSTERS", "FROZEN", "STARWARS", "ROCKY", "XMEN", "DOCTORWHO", "TITANIC", "HARRYPOTTER", "JAMESBOND", "LIONKING", "AVENGERS"]
answers_indexes = [6, 3, 2, 3, 2, 1, 7, 1, 7, 2, 7]

class MusicRace(commands.Cog, name="Music Race"):
    
    """"Initialising"""
    def __init__(self, bot):
        self.bot = bot


    async def correct_answer(self, ctx, word, idx):
        """Answer found is correct"""
        print("Recieved correct_answer")
        embed = discord_utils.create_embed()

        """TODO : Send correct playtune... with appropriate number of rests (for indexing)"""
        """TODO : Send correct song with name idx/11.mp3"""

        embed.add_field(name=f"Success!",
            value=f"Song `{word}` successfully identified")
            # reply to user
        await ctx.send(embed=embed)
        return 1

    @commands.command(name="puzzleplaceholder")
    @commands.has_any_role(
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE
    )
    async def puzzleplaceholder(self, ctx, *args):
        """Run the music id splicing puzzle"""
        print("Recieved puzzleplaceholder")
        embed = discord_utils.create_embed()

        if(len(args)<1):
            embed = discord_utils.create_no_argument_embed("word")
            await ctx.send(embed=embed)
            return

        word = re.sub("[^A-Z]+","",args[0].upper())

        if(len(word)<1 or len(word)>20):
            embed.add_field(name=f"Error!",
                value=f"Word provided `{word}` is not between 1-20 letters")
            # reply to user
            await ctx.send(embed=embed)
            return 0

        letters = {}
        for i in range(len(answers)):
            x=answers[i]
            for j in range(len(x)):
                c=x[j]
                if(c in letters):
                    letters[c].append((i,j))
                else:
                    letters[c] = [(i,j)]

        if word in answers:
            idx = answers.index(word)
            await self.correct_answer(ctx,word,idx)
            return 1

        finalanswer = []
        flag = 0
        allsplices = []
        for i in range(len(word)):
            x = word[0:i+1]
            for j in range(len(answers)):
                a = answers[j]
                if(a.startswith(x)):
                    finalanswer.append((j,i))
                    break
            c = word[i]
            if c not in letters:
                finalanswer.append((-1,-1))
                continue
            else:
                #TODO: FINISH HIM
                pass
            #TODO : FINISH HIM
        #TODO : FINISH HIM
        print(letters)
        await ctx.send(f"{letters}")

def setup(bot):
    bot.add_cog(MusicRace(bot))

