import constants
import discord
import re
from discord.ext import commands
from utils import discord_utils
from modules.perfect_pitch import perfect_pitch_constants
import os
import numpy as np
import string

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
                map[letter].append(f"{answer}_part_{idx}")
            else:
                map[letter] = [f"{answer}_part_{idx}"]
    return map


class MusicRace(commands.Cog, name="Music Race"):
    
    """"Initialising"""
    def __init__(self, bot):
        self.bot = bot
        self.letters = get_letters()
        self.partition_map = get_partition_mapping()

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
            if delay > 0: # If we found a match
                break
        print(finalanswer)
        # At this point, we've matched all we can to the song.
        # i is now the index of the longest substring that matches
        # So we need to start from the ith character
        for j in range(i, len(word)):
            char = word[j]
            if char not in self.partition_map:
                delay += 3
                continue
            else:
                finalanswer.append((np.random.choice(self.partition_map[char]).lower(), delay))
                delay += 3

        print(self.letters)
        debug_output_msg = f"0-{finalanswer[0][1]}: {finalanswer[0][0]}\n"
        for ans in finalanswer[1:]:
            debug_output_msg += f"{ans[1]}-{ans[1]+3}: {ans[0]}\n"

        await ctx.send(debug_output_msg)
        print(finalanswer)

        inputs = ''.join([f"-i {os.path.join(os.getcwd(), 'modules', 'perfect_pitch', 'music', 'puzzle_songs', finalanswer[idx][0] + '.mp3')} " for idx in range(len(finalanswer))])
        filter_complex = f"[0]atrim=0:{finalanswer[0][1]},adelay=0|0[a];"
        filter_complex += "".join([f"[{idx+1}]adelay={finalanswer[idx+1][1]*1000}|{finalanswer[idx+1][1]*1000}[{letter}];"
                                  for idx, letter in zip(range(len(finalanswer[1:])), string.ascii_lowercase[1:])])
        mix = ''.join([f"[{letter}]" for _, letter in zip(finalanswer, list(string.ascii_lowercase))])
        print(inputs)
        print(filter_complex)
        print(mix)
        print(len(finalanswer))
        if not os.path.exists(os.path.join(os.getcwd(), 'modules', 'perfect_pitch', 'music', 'puzzle_outputs', ctx.channel.name)):
            os.mkdir(os.path.join(os.getcwd(), 'modules', 'perfect_pitch', 'music', 'puzzle_outputs', ctx.channel.name))
        os.system(
            f"ffmpeg -y  {inputs} " +
            f"-filter_complex '{filter_complex}{mix}amix=inputs={len(finalanswer)}:dropout_transition=1000,volume={perfect_pitch_constants.VOLUME/2}' "
            f"{os.path.join(os.getcwd(), 'modules', 'perfect_pitch', 'music', 'puzzle_outputs', ctx.channel.name, 'jam.mp3')}"
        )
        await ctx.send(file=discord.File(os.path.join(os.getcwd(), 'modules', 'perfect_pitch', 'music', 'puzzle_outputs', ctx.channel.name, 'jam.mp3')))


def setup(bot):
    bot.add_cog(MusicRace(bot))

