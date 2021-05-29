import constants
import discord
import re
from discord.ext import commands
from utils import discord_utils
import modules.perfect_pitch
import os
import numpy as np

answers = ["FROZEN", "STARWARS", "ROCKY", "XMEN", "TITANIC", "HARRYPOTTER", "JAMESBOND", "LIONKING", "AVENGERS"]
answers_indexes = [3, 2, 3, 2, 7, 1, 7, 2, 7]


def get_letters():
    letters = {}
    for i in range(len(answers)):
        x = answers[i]
        for j in range(len(x)):
            c = x[j]
            if c in letters:
                letters[c].append((i, j))
            else:
                letters[c] = [(i, j)]
    return letters


def get_partition_mapping():
    map = {}
    for answer in answers:
        for idx, letter in enumerate(answer):
            if letter in map:
                map[letter].append(f"{answer}_part_{idx}.mp3")
            else:
                map[letter] = [f"{answer}_part_{idx}.mp3"]
    return map


class MusicRace(commands.Cog, name="Music Race"):
    
    """"Initialising"""
    def __init__(self, bot):
        self.bot = bot
        self.letters = get_letters()
        self.partition_map = get_partition_mapping()


    async def correct_answer(self, ctx, word, idx):
        """Answer found is correct"""
        print("Recieved correct_answer")
        embed = discord_utils.create_embed()

        """TODO : Send correct playtune... with appropriate number of rests (for indexing)"""
        """TODO : Send correct song with name idx/11.mp3"""



    @commands.command(name="puzzleplaceholder")
    @commands.has_any_role(
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE
    )
    async def puzzleplaceholder(self, ctx, *args):
        """Run the music id splicing puzzle"""
        print("Recieved puzzleplaceholder")
        embed = discord_utils.create_embed()

        if len(args) < 1:
            embed = discord_utils.create_no_argument_embed("word")
            await ctx.send(embed=embed)
            return

        # Replace any non-letters
        word = re.sub("[^A-Z]+", "", args[0].upper())

        if len(word) < 1 or len(word) > 20:
            embed.add_field(name=f"Error!",
                            value=f"Word provided `{word}` is not between 1-20 letters")
            await ctx.send(embed=embed)
            return

        if word in answers:
            embed.add_field(name=f"Success!",
                            value=f"Song `{word}` successfully identified")
            await ctx.send(embed=embed)
            await ctx.send(
                file=discord.File(os.path.join(os.getcwd(), "modules", "perfect_pitch", "music", "puzzle_songs",
                                               word.lower() + "_final.mp3"),
                                  filename=f"{answers.index(word)+1}of{len(answers)}.mp3"))
            return

        # We need to figure out the longest substring that is part of the answer
        # Add that duration of the song.
        # Afterwards, we need to find all the remaining letters
        # and add random partitions, or silence.
        finalanswer = []
        delay = 0
        for i in reversed(range(len(word))):
            x = word[0:i]
            for answer_idx, answer in enumerate(answers):
                if answer.startswith(x):
                    finalanswer.append((answer.lower(), i*3))
                    delay = i * 3
                    break
        # At this point, we've matched all we can to the song.
        # i is now the index of the longest substring that matches
        # So we need to start from the ith character
        for j in range(i, len(word)):
            c = word[i]
            if c not in self.partition_map:
                delay += 3
                continue
            else:
                finalanswer.append(np.random.choice(self.partition_map[c]), delay)
                delay += 3
        
        print(self.letters)
        await ctx.send(f"{self.letters}")

def setup(bot):
    bot.add_cog(MusicRace(bot))

