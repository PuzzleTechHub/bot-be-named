from discord.ext import commands
import constants
from utils import discord_utils
from modules.perfect_pitch import perfect_pitch_utils, perfect_pitch_constants
import discord
import random
import os
import glob


class PerfectPitch(commands.Cog, name="Perfect Pitch"):
    """Identify the note being played!"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="playtuneinfo", aliases=["ptinfo","playtunehelp","pthelp"])
    @commands.has_any_role(
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE,
        846095217017749515
    )
    async def playtuneinfo(self, ctx):
        """Give the users everything they need to know about the puzzle"""
        print("Received playtuneinfo")

        embed = discord_utils.create_embed()
        embed.add_field(name=f"Playtune Help",
                        value=f"Welcome to Playtune, the bot command to play musical notes of your choice!"
                        f"\n\nJust use `{ctx.prefix}playtune` followed by the notes you want to play. For example, try `{ctx.prefix}playtune C D E F G Ab4 B#4 C5`"
                        f"\n\n**Extra Settings**"
                        f"\nUse `R` for Rest. For example, try `{ctx.prefix}playtune C R R R C R R C R C C`"
                        f"\nUse `m=1` for meter and `o=4` for the octave to set as default for the song. For example, try `{ctx.prefix}playtune m=0.8 o=5 C D E F`"
                        f"\nAdd `L2` after your note (or use the correct lowercase symbols) to adjust length. For example, try `{ctx.prefix}playtune CL4 CL2 CL1 CL0.5 RL3 Cw Ch Cq Ce`"
                        f"\n\nTo see an example with all of them, try `{ctx.prefix}playtunesample`"
                        )
        await ctx.send(embed=embed)
        s = "wd=6, w=4, hd=3, h=2, qd=1.5, q=1, ed=0.75, e=0.5, sd = 0.375, s=0.25"


    @commands.command(name="playtunesample", aliases=["ptsample"])
    @commands.has_any_role(
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE,
        846095217017749515
    )
    async def playtunesample(self, ctx):
        """Give the users everything they need to know about the puzzle"""
        print("Received playtunesample")

        embed = discord_utils.create_embed()
        embed.add_field(name=f"Playtune Sample",
                        value=f"`{ctx.prefix}playtune o=5 m=1.2 RL0.5 EL0.5 F#L0.5 GL3 DL0.5 BL0.5 AL3 GL0.5 F#L0.5 EL0.5 EL0.5 E EL0.5 F# GL3 EL0.5 F#L0.5 GL3 DL0.5 BL0.5 AL3 GL0.5 AL0.5 B B C6L0.5 B AL0.5 GL0.5 AL0.5 GL3 DL1.5 B4L1.5 A4L3 G4 G4 DL1.5 B4L1.5 G4L4`"
                        )
        await ctx.send(embed=embed)


    @commands.command(name="playtune")
    @commands.has_any_role(
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE,
        846095217017749515
    )
    async def playtune(self, ctx, *args):
        """Play a string of notes together"""
        print("Received playtune")
        tune_dir = os.path.join(os.getcwd(), constants.MODULES_DIR, perfect_pitch_constants.PERFECT_PITCH_DIR,
                                perfect_pitch_constants.MUSIC, perfect_pitch_constants.TUNES, ctx.channel.name)
        # If the channel does not have a directory for them yet, create one
        if not os.path.exists(tune_dir):
            os.mkdir(tune_dir)

        # Create the tune object and process the input.
        tune = perfect_pitch_utils.Tune(ctx.channel.name)
        tune.process_args(args)
        # Create tune uses FFMPEG to mix the notes together, and returns the path of the file it created
        # TODO: Errors, error handling
        output_path = await tune.create_tune()
        try:
            await ctx.send(file=discord.File(output_path, filename="tune.mp3"))
        except FileNotFoundError:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"{constants.FAILED}",
                            value=f"Sorry, we had a problem creating your tune! Check out `{ctx.prefix}playtunehelp` "
                                  f"to see how to use the command, or try: "
                                  f"`{ctx.prefix}playtune meter=1 octave=5 C D E F` as an example")
            await ctx.send(embed=embed)

    @commands.command(name="chord")
    @commands.has_any_role(
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE,
        846095217017749515
    )
    async def chord(self, ctx):
        """Sends the user a random chord. Note: all chords come from the 4th octave (middle C)"""
        chord = random.choice(glob.glob(os.path.join(os.getcwd(), constants.MODULES_DIR, perfect_pitch_constants.PERFECT_PITCH_DIR,
                                                     perfect_pitch_constants.MUSIC, perfect_pitch_constants.PIANO,
                                                     perfect_pitch_constants.CHORDS, "*.mp3")))
        await ctx.send(file=discord.File(chord, filename="random_chord.mp3"))
        await ctx.send(f"Answer: ||{chord.split('/')[-1].replace('.mp3', '').replace('_', ' ').center(15)}||")

    # TODO: CLEAN PLS for the love of christ
    @commands.command(name="note")
    @commands.has_any_role(
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE,
        846095217017749515
    )
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
            note_path = os.path.join(os.getcwd(),
                                     constants.MODULES_DIR,
                                     perfect_pitch_constants.PERFECT_PITCH_DIR,
                                     perfect_pitch_constants.MUSIC,
                                     perfect_pitch_constants.PIANO,
                                     perfect_pitch_constants.NOTES,
                                     arg + ".mp3")
            if os.path.exists(note_path):
                await ctx.send(file=discord.File(note_path))
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
        # TODO: currently, note will always be none here
        filenames = f"{note if note else '*'}{'b' if flat_or_nat == 'flat' else '*'}{octave if isinstance(octave, int) else '*'}.mp3"

        mp3_paths = glob.glob(os.path.join(os.getcwd(),
                              constants.MODULES_DIR,
                              perfect_pitch_constants.PERFECT_PITCH_DIR,
                              perfect_pitch_constants.MUSIC,
                              perfect_pitch_constants.PIANO,
                              perfect_pitch_constants.NOTES,
                              filenames))

        # Make sure flat symbol is not in filename
        if flat_or_nat == 'nat':
            mp3_paths = list(filter(lambda x: 'b' not in x.split('/')[-1], mp3_paths))

        notepath = random.choice(mp3_paths)

        note = discord.File(notepath, filename="random_note.mp3")
        # Send the note, followed by the answer
        await ctx.send(file=note)
        await ctx.send(f"Answer: ||{notepath.split('/')[-1].split('.')[0].center(10)}||")


def setup(bot):
    bot.add_cog(PerfectPitch(bot))
