import constants
import discord
import re
from discord.ext import commands
from utils import discord_utils
from modules.music_race import music_race_constants
import os
import numpy as np
import string


def get_partition_mapping():
    map = {}
    for answer in music_race_constants.ANSWERS:
        for idx, letter in enumerate(answer):
            if letter in map:
                map[letter].append(f"{answer}_part_{idx}")
            else:
                map[letter] = [f"{answer}_part_{idx}"]
    return map


class MusicRace(commands.Cog, name="Music Race"):
    """"Puzzle for Arithmancy June 2020! Identify each of the movies based on their theme songs!"""
    def __init__(self, bot):
        self.bot = bot
        self.partition_map = get_partition_mapping()

    @commands.command(name="puzzleplaceholder", aliases=['pph'])
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
        word = re.sub("[^A-Z]+", "", "".join(args).upper())

        if len(word) < 1 or len(word) > 20:
            embed.add_field(name=f"Error!",
                            value=f"Word provided `{word}` is not between 1-20 letters")
            await ctx.send(embed=embed)
            return

        if word in music_race_constants.ANSWERS:
            embed.add_field(name=f"{word}",
                            value=f"`{music_race_constants.ANSWERS[word][music_race_constants.TUNE]}`")
            await ctx.send(embed=embed)
            await ctx.send(
                file=discord.File(os.path.join(os.getcwd(),
                                               constants.MODULES_DIR,
                                               music_race_constants.MUSIC_RACE_DIR,
                                               music_race_constants.PUZZLE_SONGS_DIR,
                                               word + "_final.mp3"),
                                  filename=f"{list(music_race_constants.ANSWERS).index(word)+1} of {len(music_race_constants.ANSWERS)}.mp3"))
            return

        # We need to figure out the longest substring that is part of the answer
        # Add that duration of the song.
        # Afterwards, we need to find all the remaining letters
        # and add random partitions, or silence.
        finalanswer = []
        delay = 0
        # For each letter we match, we can add that to the start of our output song
        for i in range(len(word)):
            found_song = False
            x = word[0:(i+1)]
            # Matches one of the songs
            for answer in music_race_constants.ANSWERS:
                if answer.startswith(x):
                    finalanswer.append((f"{answer}_part_{i}", delay))
                    found_song = True
                    break
            # Newly added character is not the start to a song
            if not found_song:
                # Get a random clip with that letter
                if word[i] in self.partition_map:
                    finalanswer.append((np.random.choice(self.partition_map[word[i]]), delay))
            # Increments
            delay += 3

        debug_output_msg = ""
        for ans in finalanswer:
            debug_output_msg += f"{ans[1]}-{ans[1]+3}: {ans[0]}\n"
        # TODO: Remove once we are more certain about how this works. It ruins the puzzle, obviously
        await ctx.send(debug_output_msg)

        inputs = ''.join([f"-i {os.path.join(os.getcwd(), constants.MODULES_DIR, music_race_constants.MUSIC_RACE_DIR, music_race_constants.PUZZLE_SONGS_DIR, finalanswer[idx][0] + '.mp3')} " for idx in range(len(finalanswer))])
        # Otherwise, we just chop each song into 3s bits, with 0.5s between them
        filter_complex = "".join([f"[{idx}]atrim=0:{music_race_constants.SONG_SNIPPET_LENGTH},adelay={finalanswer[idx][1]*1000+500*idx}|{finalanswer[idx][1]*1000+500*idx},volume={music_race_constants.VOLUME/2}[{letter}];"
                                  for idx, letter in zip(range(len(finalanswer)), string.ascii_lowercase)])
        mix = ''.join([f"[{letter}]" for _, letter in zip(finalanswer, list(string.ascii_lowercase))])

        output_dir = os.path.join(os.getcwd(),
                                  constants.MODULES_DIR,
                                  music_race_constants.MUSIC_RACE_DIR,
                                  music_race_constants.PUZZLE_OUTPUTS_DIR,
                                  ctx.channel.name)
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        output_path = os.path.join(output_dir, f"{word}.mp3")
        os.system(
            f"ffmpeg -y  {inputs} " +
            f"-filter_complex '{filter_complex}{mix}amix=inputs={len(finalanswer)}:dropout_transition=1000,volume={music_race_constants.VOLUME/2}' "
            f"{output_path}"
        )
        await ctx.send(file=discord.File(output_path))


def setup(bot):
    bot.add_cog(MusicRace(bot))

