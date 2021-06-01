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
answers_tunes =
[
"~playtune B3h Ch C#h Ch B3h Ch C#h Ch Ee F#s F#s F#e F# Ee Ee Ee Ee Gs Gs Ge G F#e F#e F#e Ee F#s F#s F#e F# Ee Ee Ee Ee Gs Gs Ge G F#e F#e F#e Ee F#s F#s F#e F# Ee Ee Ee Ee Gs Gs Ge G F#e F#e Ee D#5e D5h Be Ae Bh Ee F#s F#s F#e F# Ee Ee Ee Ee Gs Gs Ge G",
"~playtune o=5 m=1.2 Re Ee F#e Ghd De Be Ahd Ge F#e Ee Ee E Ee F# Ghd Ee F#e Ghd De Be Ahd  Ge Ae B B C6e B Ae Ge Ae Ghd Dqd B4qd A4hd G4 G4 Dqd B4qd G4w",
"~playtune m=1.3 o=4 E Aqd C5e B Ah E5 D5hd Bhd Aqd C5e B Gh A Ew E Aqd C5e B Ah E5 G5h Gb5 F5h D5 F5qd E5e D#5 Ah C5 Aw C5 E5h C5 E5h C5 F5h E5 D#5h D#5 E5qd C5e A D#h E E5w C5 E5h C5 E5h C5 G5h Gb5 F5h Db5 F5qd E5e D#5 D#h C5 Aw",
"~playtune Ce Ce Cs Cs Ce Cs Cs Ee Cs Cs Ce Ee Ee Es Es Ee Es Es Ge Es Es E De Ds Ds De Ds Ds Ds Ds De Re De De Ds Ds Ds De Ds D Ds Ged Ahd As Bed Ehd Es Ged Ahd As Bed Ew",
"~playtune E2s E2s E2s E2s G2s G2s E2s E2s G2s G2s G2s G2s Es Bs E5s G5s F#5 E5e Bqd Es Bs E5s G5s F#5 E5e C5qd Es Bs E5s G5s F#5 E5e G5h F#5e E5e Bh Gs E5s G5s C6s B5 A5e E5qd Gs E5s G5s C6s B5 A5e F5qd Es Bs E5s G5s F#5 E5e G5h F#5e E5e Bhd",
"~playtune Eed Fs Ge C5h Ded Es Fhd Ged As Be F5h Aed Bs C5 D5 E5 Eed Fs Ge C5h D5ed E5s F5hd Ged Gs E5 D5ed Gs E5 D5ed Gs E5 D5ed Gs E5e D5e E5ed F5s G5e C6h D5ed E5s F5hd G5ed A5s B5e F6h A5ed B5s C6 D6 E6 E5ed F5s G5e C6h D6ed E6s F6hd Ged Gs E5 D5ed Gs E5 D5ed Gs E5 D5ed Gs F5 E5ed Gs F5 E5ed D5s C5h",
"~playtune o=5 F4t F4t F4t Bb4h F5h Ebt Dt Ct Bbh F Ebt Dt Ct Bbh F Ebt Dt Ebt Ch F4t F4t F4t  Bb4h Fh Ebt Dt Ct Bbh F Ebt Dt Ct Bbh F Ebt Dt Ebt Ch F4L0.67 F4t G4qd G4e Ebe De Ce Bb4e Bb4t Ct Dt CL0.67 G4t A4 F4ed F4e G4qd G4e Ebe De Ce Bb4e Feq Cs Ch",
"",
"~playtune Fe Ge Ge Ah Ge Fe Ge C5h Bbe Ae Fhd R Fe Ge Ahd Bbs As Gs Fs Ge C5h Ae C5e D5h C5h Gh Rh Fqd Fe F F E Fh F E Fh G Ah Gh Fqd Fe F F E Fh F Cw",
"~playtune Ds Ds D Ds Ds D Ds Ds Ds Ds Ebs Ebs Eb Ebs Ebs E Es Es Es Es Fs Fs F Fs Fs E Es Es Es Es Ebs Ebs Eb Ebs Ebs Bb3 C Ds Ds D Ds Ds D Ds Ds Ds Ds DS Ebs Ebs Eb Ebs Ebs E Es Es Es Es Fs Fs F Fs Fs E Es Es Es Es Ebs Ebs Eb Ebs Ebs Bb3 C G3w D Ced Bb3s Bb3 Ced Ds D G3hd D Ced Bb3s Bb3 A3 G3w D Ced Bb3s Bb3 Ced Ds D G3hd D Ced Bb3s Bb3 A3 G3w",
]



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

        if word in answers:
            embed.add_field(name=f"Success!",
                            value=f"Song `{word}` successfully identified")
            await ctx.send(embed=embed)
            await ctx.send(
                file=discord.File(os.path.join(os.getcwd(),
                                               constants.MODULES_DIR,
                                               constants.PERFECT_PITCH_DIR,
                                               perfect_pitch_constants.MUSIC,
                                               perfect_pitch_constants.PUZZLE_SONGS,
                                               word.lower() + "_final.mp3"),
                                  filename=f"{answers.index(word)+1} of {len(answers)}.mp3"))
            return

        # We need to figure out the longest substring that is part of the answer
        # Add that duration of the song.
        # Afterwards, we need to find all the remaining letters
        # and add random partitions, or silence.
        finalanswer = []
        delay = 0
        # This flag is true if the first letter(s) match the first letter of a song, and false otherwise
        base_song_flag = True
        for i in reversed(range(len(word))):
            # Did not find a match
            if i == 0:
                base_song_flag = False
                break
            x = word[0:i]
            for answer_idx, answer in enumerate(answers):
                if answer.startswith(x):
                    finalanswer.append((answer.lower(), i*3))
                    delay = i * 3
                    break
            # If we found a match
            if delay > 0:
                break
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

        debug_output_msg = ""
        if base_song_flag:
            list_indexing = 1
            debug_output_msg += f"0-{finalanswer[0][1]}: {finalanswer[0][0]}\n"
        else:
            list_indexing = 0
        for ans in finalanswer[list_indexing:]:
            debug_output_msg += f"{ans[1]}-{ans[1]+3}: {ans[0]}\n"
        # TODO: Remove once we are more certain about how this works. It ruins the puzzle, obviously
        await ctx.send(debug_output_msg)

        inputs = ''.join([f"-i {os.path.join(os.getcwd(), constants.MODULES_DIR, constants.PERFECT_PITCH_DIR, perfect_pitch_constants.MUSIC, perfect_pitch_constants.PUZZLE_SONGS, finalanswer[idx][0] + '.mp3')} " for idx in range(len(finalanswer))])
        # If we they got the start to a song, then we want to play that whole duration uncut.
        if base_song_flag:
            filter_complex = f"[0]atrim=0:{finalanswer[0][1]},adelay=0|0[a];"
        else:
            filter_complex = ""
        # Otherwise, we just chop each song into 3s bits, with 0.5s between them
        filter_complex += "".join([f"[{idx+list_indexing}]atrim=0:3000,adelay={finalanswer[idx+list_indexing][1]*1000+500*idx}|{finalanswer[idx+list_indexing][1]*1000+500*idx}[{letter}];"
                                  for idx, letter in zip(range(len(finalanswer[list_indexing:])), string.ascii_lowercase[list_indexing:])])
        mix = ''.join([f"[{letter}]" for _, letter in zip(finalanswer, list(string.ascii_lowercase))])

        output_dir = os.path.join(os.getcwd(),
                                  constants.MODULES_DIR,
                                  constants.PERFECT_PITCH_DIR,
                                  perfect_pitch_constants.MUSIC,
                                  perfect_pitch_constants.PUZZLE_OUTPUTS,
                                  ctx.channel.name)
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        fpath = f"{word}.mp3"
        os.system(
            f"ffmpeg -y  {inputs} " +
            f"-filter_complex '{filter_complex}{mix}amix=inputs={len(finalanswer)}:dropout_transition=1000,volume={perfect_pitch_constants.VOLUME/2}' "
            f"{os.path.join(output_dir, fpath)}"
        )
        await ctx.send(file=discord.File(os.path.join(output_dir, fpath)))


def setup(bot):
    bot.add_cog(MusicRace(bot))

