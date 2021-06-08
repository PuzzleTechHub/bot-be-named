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

    @commands.command(name="playtunehelp", aliases=["playtuneinfo"])
    @commands.has_any_role(
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE,
        846095217017749515
    )
    async def playtunehelp(self, ctx):
        """Give the users everything they need to know about playtune"""
        print(f"Received playtunehelp from {ctx.channel.name}")

        embed = discord_utils.create_embed()
        embed.add_field(name=f"Playtune Help",
                        value=f"Welcome to Playtune, the bot command to play musical notes of your choice!"
                              f"\n\nJust use `{ctx.prefix}playtune` followed by the notes you want to play. "
                              f"For example, try `{ctx.prefix}playtune C D E F G A B C5`",
                        inline=False)
        embed.add_field(name=f"Rests",
                        value=f"Use `R` for Rest.\nFor example, try `{ctx.prefix}playtune C R R R C R R C R C C`",
                        inline=False)
        embed.add_field(name=f"Sharps and Flats",
                        value=f"Use `b` and `#` after any note to indicate it is a sharp or flat.\nFor example, try "
                              f"`~playtune C C# D D# E F F# G Ab A Bb C5`")
        embed.add_field(name=f"Meter",
                        value=f"Use `m=` at the start of the command to control the speed of your tune (the default is `1`)."
                              f"\nFor example, try `{ctx.prefix}playtune m=0.8 C D E F`.",
                        inline=False)
        embed.add_field(name=f"Customizing",
                        value=f"You can customise Octaves of songs, what Instruments you want to play, as well as Note Lengths!"
                              f"\nFor more information about the all of these, use `{ctx.prefix}playtunecustom`",
                        inline=False)
        embed.add_field(name=f"Example",
                        value=f"To see an example with everything put together, try `{ctx.prefix}playtunesample`",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="playtunecustom", aliases=["ptcustom"])
    @commands.has_any_role(
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE,
        846095217017749515
    )
    async def playtunecustom(self, ctx):
        """Give the users everything they need to know about customising playtune"""
        print(f"Received playtunecustom from {ctx.channel.name}")

        embed = discord_utils.create_embed()
        embed.add_field(name=f"Playtune Customizing",
                        value=f"Here are some of the ways you can customise playtune to get exactly what you want!"
                              f"\nFor a description of playtune itself, use `{ctx.prefix}playtunehelp`!",
                        inline=False)
        embed.add_field(name=f"Customizing Octave",
                        value=f"Use `o=` at the start of your tune to control the default octave of your tune (the normal default is `4`)."
                              f"\nFor example, try `{ctx.prefix}playtune m=0.8 o=5 C D E F`. \n"
                              f"You can control the octave of each note by putting the octave immediately after the note."
                              f"\nFor example, try `{ctx.prefix}playtune m=1.2 o=5 C4 C C6 C B4 Bb4 A4`",
                        inline=False)
        embed.add_field(name=f"Customizing Instrument",
                        value=f"Use `i=` at the start of your tune to control the instrument used. For example, try "
                              f"`{ctx.prefix}playtune m=0.8 o=5 i=xylophone C D E F`. Currently supported instruments "
                              f"include {perfect_pitch_constants.PIANO} (default), {perfect_pitch_constants.XYLOPHONE}, "
                              f"and {perfect_pitch_constants.MARIMBA}.\nUse `{ctx.prefix}playtuneinstrument` to learn more"
                              f"about each instrument's range of notes.",
                        inline=False)
        embed.add_field(name=f"Customizing Note Length",
                        value=f"We support two ways of customizing each note's length. The simpler is `L` notation. At "
                              f"the end of each note (after any sharps or flats, add `L` followed by the length of the note "
                              f"(the default of `L1`).\n"
                              f"For example, try `{ctx.prefix}playtune C#L2 C#L0.5 C#L0.5 CL0.25 C#L0.25 RL0.5 CL2`.\n"
                              f"We also support using letters like `w` for whole note, `e` for eighth note, and so on.\n"
                              f"For example, try `{ctx.prefix}playtune Ch Ce Ce Cs Cs Re Ch`\n"
                              f"For more information about the letter notation, use `{ctx.prefix}playtunelength`",
                        inline=False
                        )
        embed.add_field(name=f"Example",
                        value=f"To see an example with everything put together, try `{ctx.prefix}playtunesample`",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="playtuneinstrument")
    @commands.has_any_role(
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE,
        846095217017749515
    )
    async def playtuneinstrument(self, ctx):
        print(f"Received playtuneinstrument from {ctx.channel.name}")
        embed = discord_utils.create_embed()
        embed.add_field(name="Instruments and Ranges (Low/High)",
                        value=f"{perfect_pitch_constants.PIANO}: B0/C8\n{perfect_pitch_constants.XYLOPHONE}:F4/C8\n"
                              f"{perfect_pitch_constants.MARIMBA}: C2/C7")
        await ctx.send(embed=embed)

    @commands.command(name="playtunelength")
    @commands.has_any_role(
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE,
        846095217017749515
    )
    async def playtunelength(self, ctx):
        print(f"Received playtunelength from {ctx.channel.name}")
        embed = discord_utils.create_embed()
        embed.add_field(name="Note Lengths",
                        value="`w`: whole note (4 beats)\n"
                              "`hd`: dotted half note (3 beats)\n"
                              "`h`: half note (2 beats)\n"
                              "`qd`: dotted quarter note (1 1/2 beats)\n"
                              "`q`: quarter note (1 beat)\n"
                              "`ed`: dotted eighth note (3/4 beats)\n"
                              "`e`: eighth note (1/2 beats)\n"
                              "`t`: eighth triplet (1/3 beats)\n"
                              "`s`: sixteenth note (1/4 beats)\n\n"
                              "Any times not listed can be customized by using the `L` notation. For instance, "
                              "quarter note triples can be created with `L0.67` on each note, "
                              "meaning `2/3` of a beat each."
                        )
        await ctx.send(embed=embed)

    @commands.command(name="playtunesample", aliases=["ptsample"])
    @commands.has_any_role(
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE,
        846095217017749515
    )
    async def playtunesample(self, ctx):
        """Give the users everything they need to know about the puzzle"""
        print(f"Received playtunesample from {ctx.channel.name}")

        embed = discord_utils.create_embed()
        embed.add_field(name=f"Sample 1",
                        value=f"`{ctx.prefix}playtune m=1 o=4 Ce Ce Cs Cs Ce Cs Cs Ee Cs Cs Ce Ee Ee Es Es Ee Es "
                        "Es Ge Es Es E De Ds Ds De Ds Ds Ds Ds De Re De De Ds Ds Ds De Ds D Ds Ged Ahd As Bed Ehd "
                        "Es Ged Ahd As Bed Ew`",
                        inline=False
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
        print(f"Received playtune from {ctx.channel.name}")
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
        print(f"Received chord from {ctx.channel.name}")
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
        print(f"Received note from {ctx.channel.name}")
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
