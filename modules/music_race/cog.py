import string

from discord.ext import commands
from utils import discord_utils
import discord
import random
import os
import shutil
import glob

class MusicRace(commands.Cog, name="Music Race"):
    """Race against the clock identifying music notes!"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="testffmpeg")
    async def testffmpeg(self, ctx):
        test_dir = os.path.join(os.getcwd(), "modules", "music_race", "music", "test")
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        os.mkdir(test_dir)
        output_file = os.path.join(os.getcwd(), "modules", "music_race", "music", "test", "output.mp3")
        input_dir = os.path.join(os.getcwd(), "modules", "music_race", "music", "notes")
        os.system(f"ffmpeg -i {os.path.join(input_dir, 'E4.mp3')} -i {os.path.join(input_dir, 'Ab4.mp3')} "
                  f"-i {os.path.join(input_dir, 'B4.mp3')} -filter_complex '[0]adelay=0|0[a];[1]adelay=500|500[b];"
                  f"[2]adelay=1000|1000[c];[0]adelay=2000|2000[d];[1]adelay=2000|2000[e];[2]adelay=2000|2000[f];"
                  f"[a][b][c][d][e][f]amix=inputs=3' {output_file}")
        await ctx.send(file=discord.File(output_file))

    @commands.command(name="playtune")
    async def playtune(self, ctx, *args):
        """Play a string of notes together"""
        notes = []
        for arg in args:
            assert len(arg) <= 2 and arg in ['Ab', 'A', 'Bb', 'B', 'C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G'], \
                "Arg is not a note"
            notes.append(arg)
        inputs = ' '.join([f"-i {os.path.join(os.getcwd(), 'modules', 'music_race', 'music', 'notes', note)}" for note in notes])
        filter_complex = ';'.join([f"[{idx}]adelay={500*idx}|{500*idx}[{letter}]" for idx, letter in zip(range(len(notes)), list(string.ascii_lowercase))])
        mix = ''.join([f"[{letter}]" for _, letter in zip(notes, list(string.ascii_lowercase))])
        output_path = os.path.join(os.getcwd(), "modules", "music_race", "music", "test", "output.mp3")
        os.system(f"ffmpeg {inputs} -filter_complex '{filter_complex};{mix}amix=inputs=3' {output_path}")
        await ctx.send(file=discord.File(output_path))

    @commands.command(name="chord")
    async def chord(self, ctx):
        """Sends the user a random chord. Note: all chords come from the 4th octave (middle C)"""
        chord = random.choice(glob.glob(os.path.join(os.getcwd(), "modules", "music_race", "music", "chords", "*.mp3")))
        await ctx.send(file=discord.File(chord, filename="random_chord.mp3"))
        await ctx.send(f"Answer: ||{chord.split('/')[-1].replace('.mp3', '').replace('_', ' ').center(15)}||")

    @commands.command(name="note")
    async def note(self, ctx, *args):
        """Send the user a random note for them to identify.
        Arguments:
            - Octave (int): The specific octave you want a random note from
            - Flat_or_Nat (str): Whether you want the note to be flat/sharp or natural
            - Note (str): A specific note (e.g. G4)
        """
        print("Received note")
        # User-selected parameters for which notes will appear
        octave = None
        flat_or_nat = ''
        note = ''
        for arg in args:
            # If the user supplied an exact note, send it
            if os.path.exists(os.path.join(os.getcwd(), "modules", "music_race", "music", "notes", arg + ".mp3")):
                await ctx.send(file=discord.File(os.path.join(os.getcwd(), "modules", "music_race", "music", "notes", arg+".mp3")))
                return
            # Don't redefine octave multiple times; only take first int argument passed
            if not isinstance(octave, int):
                try:
                    octave = int(arg)
                except ValueError:
                    pass
            # Similarly, only first flat or nat passed
            if (arg == 'flat' or arg == 'nat') and not flat_or_nat:
                flat_or_nat = arg

        if octave is not None and (octave < 0 or octave > 7):
            embed = discord_utils.create_embed()
            embed.add_field(name="Failed!",
                            value="Make sure your octave value is between 0 and 7!")
            await ctx.send(embed=embed)
            return
        # The user can specify which octave they want to hear, in which case we only get a note from that octave
        filenames = f"{note if note else '*'}{'b' if flat_or_nat == 'flat' else '*'}{octave if isinstance(octave, int) else '*'}.mp3"
        #if octave is not None:
        #    filenames = f"*{'b' if flat_or_nat == 'flat' else ''}{octave if octave else ''}.mp3"
        #else:
        #    filenames = f"*{'b*' if flat_or_nat == 'flat' else ''}.mp3"

        mp3_paths = glob.glob(os.path.join(os.getcwd(), "modules", "music_race", "music", "notes", filenames))

        # Make sure flat symbol is not in filename
        if flat_or_nat == 'nat':
            mp3_paths = list(filter(lambda x: 'b' not in x.split('/')[-1], mp3_paths))

        notepath = random.choice(mp3_paths)

        note = discord.File(notepath, filename="random_note.mp3")
        await ctx.send(file=note)
        await ctx.send(f"Answer: ||{notepath.split('/')[-1].split('.')[0].center(10)}||")




def setup(bot):
    bot.add_cog(MusicRace(bot))
