from dotenv.main import load_dotenv
import discord
from discord.ext import commands
from discord.ext.tasks import loop
import os
from utils import google_utils, discord_utils, logging_utils, command_predicates
from modules.cipher_race import cipher_race_constants, cipher_race_utils
import constants
from aio_timers import Timer
from emoji import EMOJI_ALIAS_UNICODE_ENGLISH as EMOJIS

load_dotenv()

# TODO: 
# Practice Mode with a timer?
#   - One cipher_race at a time
#   - Timer increases with each correct answer?
#   - Maybe start shooting out 2 at a time?
#   - High scores?
# Challenge mode with a certain level cap?
#   - Say ~challenge 3
#   - After 3 levels, gives a success message and ends the race
# Change


class CipherRaceCog(commands.Cog, name="Cipher Race"):
    """Puzzle for Arithmancy March 2020! Identify and learn common ciphers under time control"""
    def __init__(self, bot):
        # Bot and cipher_race initializations
        self.bot = bot
        # The current race will have channel_id as key, with 
        # a dict containing level and current answers
        self.current_races = {}

        # Google Sheets Authentication and Initialization
        self.client = google_utils.create_gspread_client()


        self.spreadsheet = self.client.open_by_key(os.getenv('CIPHER_RACE_SHEET_KEY').replace('\'', ''))
        self.sheet_map = {
            cipher_race_constants.HP: google_utils.get_dataframe_from_gsheet(
                self.spreadsheet.worksheet(cipher_race_constants.HP_SHEET_TAB_NAME),
                cipher_race_constants.COLUMNS
            ),
            cipher_race_constants.COMMON: google_utils.get_dataframe_from_gsheet(
                self.spreadsheet.worksheet(cipher_race_constants.COMMON_SHEET_TAB_NAME),
                cipher_race_constants.COLUMNS
            ),
            cipher_race_constants.CHALLENGE: google_utils.get_dataframe_from_gsheet(
                self.spreadsheet.worksheet(cipher_race_constants.CHALLENGE_SHEET_TAB_NAME),
                cipher_race_constants.COLUMNS
            )
        }
        
    # Reload the google sheet every hour
    @commands.Cog.listener()
    async def on_ready(self):
        """When discord is connected"""
        self.reload_sheet.start()
            
    @commands.command(name='startcipherrace')
    async def startrace(self, ctx, sheet: str = cipher_race_constants.HP):
        """
        Start your cipher race! Gives you 60s per level to solve all codes.
        Level 1 is 1 code, and each level is 1 more code to solve. 
        Ciphers: morse, semaphore, braille, pigpen.
        Wordlist: hp, challenge, common

        Usage: `~startcipherrace` (Starts a cipher race with HP wordlist)
        Usage: `~startcipherrace challenge` (Starts a cipher race with challenge wordlist)
        Usage: `~startcipherrace common` (Starts a cipher race with common English wordlist)
        """
        channel = ctx.channel.id
        if channel in self.current_races:
            print("startrace called from a channel that's already racing!!")
            embed = discord_utils.create_embed()
            embed.add_field(name="Already Racing!",
                            value=f"Stop trying to start a new race while you have one going!",
                            inline=False)
            await ctx.send(embed=embed)
            return
        # Housekeeping
        logging_utils.log_command("startcipherrace", ctx.guild, ctx.channel, ctx.author)
        # Create entry in current_races
        self.current_races[channel] = dict()
        self.current_races[channel][cipher_race_constants.LEVEL] = 1
        # ~startcipherrace challenge gives you 1000 random english word sheet
        # ~startcipherrace hp gives you the harry potter sheet
        # ~startcipherrace common gives you 1000 very common english words
        if sheet not in self.sheet_map:
            sheet = cipher_race_constants.HP

        self.current_races[channel][cipher_race_constants.CODE] = self.sheet_map[sheet]
        embeds, self.current_races[channel][cipher_race_constants.ANSWERS] = cipher_race_utils.create_code_embed(
            self.current_races[channel][cipher_race_constants.LEVEL], self.current_races[channel][cipher_race_constants.CODE], ctx.prefix)

        await ctx.send(embed=cipher_race_utils.get_opening_statement(sheet))
        # In a short time, send the codes
        time = Timer(cipher_race_constants.BREAK_TIME, self.start_new_level, callback_args=(ctx, channel, embeds), callback_async=True)

    @commands.command(name='practice', aliases=['pigpenpls'])
    async def practice(self, ctx, code: str = None, sheet: str = cipher_race_constants.HP):
        """
        Gives a cipher of a specific type. Defaults to random cipher and HP wordlist.
        Ciphers: morse, semaphore, braille, pigpen.
        Wordlist: hp, challenge, common
        See also: `~startcipherrace`

        Usage: `~practice` (Shows a random cipher from HP wordlist)
        Usage: `~practice morse` (Shows a Morse cipher from HP wordlist)
        Usage: `~practice braille Common` (Shows a Braille cipher from Common wordlist. Both must be specified to use non-HP wordlist)
        """
        logging_utils.log_command("practice", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()
        # Supply no arguments: randomly sample
        # Supply 2 arguments: sample specific cipher_race
        # Supply more arguments: incorrect

        if sheet not in cipher_race_constants.SHEETS:
            embed.add_field(name=f"Sheet not found!",
                            value=f"We don't recognize the {sheet.capitalize()} sheet. Defaulting to {cipher_race_constants.HP}.\n"
                                  f"Current sheet options are: {', '.join(cipher_race_constants.SHEETS)}",
                            inline=False)
            sheet = cipher_race_constants.HP
        # If the cipher_race is not supplied, we randomly sample
        # If cipher_race is supplied but it's not one of our ciphers, send an error but still randomly sample.
        if code not in cipher_race_constants.CIPHERS:
            # get random cipher
            proposal_row = self.sheet_map[sheet].sample()
            used_cipher = proposal_row[cipher_race_constants.CODE].item()
            # Code was supplied but not in our list of codes
            if code is not None:
                embed.add_field(name=f"{cipher_race_constants.CODE.capitalize()} not found!",
                                value=f"We don't recognize {code.capitalize()}. Current options are: {', '.join(cipher_race_constants.CIPHERS)}.\n"
                                      f"Randomly selecting {used_cipher}.",
                                inline=False)
        else:
            # Make sure the wordlist actually uses that cipher
            if code.lower() in self.sheet_map[sheet][cipher_race_constants.CODE].value_counts().index:
                used_cipher = code.lower()
                proposal_row = self.sheet_map[sheet][self.sheet_map[sheet][cipher_race_constants.CODE] == used_cipher].sample()
            # That cipher isn't in the sheet, send error message
            else:
                embed.add_field(name=f"{cipher_race_constants.CODE.capitalize()} Not Found",
                                value=f"Sorry! We can't find that {cipher_race_constants.CODE} in the {sheet} sheet.\n"
                                      f"Current {cipher_race_constants.CODE} options: {', '.join([index[0] for index in self.sheet_map[sheet][cipher_race_constants.CODE].value_counts.index])}",
                                inline=False)
                await ctx.send(embed=embed)
                return

        embed.add_field(name=f"{used_cipher.capitalize()}",
                        value=f"{proposal_row[cipher_race_constants.URL].item()}")
        embed.add_field(name="Answer",
                        value=f"|| {proposal_row[cipher_race_constants.ANSWER].item()} ||")
        embed.set_image(url=proposal_row[cipher_race_constants.URL].item())
        await ctx.send(embed=embed)

    # Command to check the user's answer. They will be replied to telling them whether or not their answer is correct
    @commands.command(name='answerrace', aliases=['ar'])
    async def answer(self, ctx, *args):
        """
        Check your answer for cipher race
        See also: `~startcipherrace`

        Usage: `~answerrace <your answer>`
        """
        channel = ctx.channel.id
        logging_utils.log_command("answerrace", ctx.guild, ctx.channel, ctx.author)
        
        # if the team isn't puzzling then we need to instruct them to use startpuzzle command first.
        if channel not in self.current_races:
            embed = discord_utils.create_embed()
            embed.add_field(name="No race!",
                            value="This channel doesn't have a race going on. You can't answer anything!",
                            inline=False)
            embed.add_field(name="Start Race",
                            value=f"To start a race, use {ctx.prefix}startcipherrace",
                            inline=False)
            await ctx.send(embed=embed)
            return
        print(f"All current answers: {self.current_races[channel][cipher_race_constants.ANSWERS]}")
        
        # Remove the command and whitespace from the answer.
        user_answer = "".join(args)
        result = cipher_race_utils.get_answer_result(user_answer, self.current_races[channel][cipher_race_constants.ANSWERS])
        
        if result == cipher_race_constants.CORRECT:
            await ctx.message.add_reaction(EMOJIS[cipher_race_constants.CORRECT_EMOJI])
        else:
            await ctx.message.add_reaction(EMOJIS[cipher_race_constants.INCORRECT_EMOJI])

        # We pop off the correct answers as they are given, so at some point current_answers will be an empty list.
        # If there are more answers left, don't do any of that level complete nonsense.
        if len(self.current_races[channel][cipher_race_constants.ANSWERS]) >= 1:
            return
        # If there are no answers left for the round, then the team has completed the level
        # Create the next level prep embed
        embed = cipher_race_utils.create_level_prep_embed(self.current_races[channel][cipher_race_constants.LEVEL])
        # Proceed to next level. Perform computation ahead of time.
        self.current_races[channel][cipher_race_constants.LEVEL] += 1
        # Creates all cipher_race embeds, updates used cipher_race IDS, and refreshes current answers for the next level.
        if cipher_race_constants.CODE in self.current_races[channel]:
            embeds, self.current_races[channel][cipher_race_constants.ANSWERS] = cipher_race_utils.create_code_embed(
                self.current_races[channel][cipher_race_constants.LEVEL], self.current_races[channel][cipher_race_constants.CODE], ctx.prefix)
        else:
            embeds, self.current_races[channel][cipher_race_constants.ANSWERS] = cipher_race_utils.create_code_embed(
                self.current_races[channel][cipher_race_constants.LEVEL], self.codes, ctx.prefix)
        
        await ctx.send(embed=embed)
        Timer(cipher_race_constants.BREAK_TIME, self.start_new_level, callback_args=(ctx, channel, embeds), callback_async=True)

    @command_predicates.is_owner_or_admin()
    @commands.command(name='reloadciphersheet')
    async def reload(self, ctx):
        """
        Reload the cipherrace Google Sheets so we can update our cipherrace codes instantly.
        See also: `~startcipherrace`

        Category: Admin or Bot Owner only.
        Usage: `~reloadciphersheet`
        """
        self.sheet_map = {
            cipher_race_constants.HP: google_utils.get_dataframe_from_gsheet(
                self.spreadsheet.worksheet(cipher_race_constants.HP_SHEET_TAB_NAME),
                cipher_race_constants.COLUMNS
            ),
            cipher_race_constants.COMMON: google_utils.get_dataframe_from_gsheet(
                self.spreadsheet.worksheet(cipher_race_constants.COMMON_SHEET_TAB_NAME),
                cipher_race_constants.COLUMNS
            ),
            cipher_race_constants.CHALLENGE: google_utils.get_dataframe_from_gsheet(
                self.spreadsheet.worksheet(cipher_race_constants.CHALLENGE_SHEET_TAB_NAME),
                cipher_race_constants.COLUMNS
            )
        }
        print(f"Reload used. Reloaded {cipher_race_constants.CODE} sheet")
        embed = discord_utils.create_embed()
        embed.add_field(name="Sheet Reloaded",
                        value="Google sheet successfully reloaded",
                        inline=False)
        await ctx.send(embed=embed)

    @command_predicates.is_owner_or_admin()
    @commands.command(name='resetcipherrace')
    async def reset(self, ctx):
        """
        Reset the cipherrace module as if bot has just loaded up
        Does not reload cipher race google sheet. Use `~reloadciphersheet` for that
        See also: `~startcipherrace`

        Usage: `~resetcipherrace`
        """
        self.current_races = {}
        embed = discord_utils.create_embed()
        embed.add_field(name="Success",
                        value="Bot has been reset, and all races have been forcibly ended. I feel brand new!",
                        inline=False)
        await ctx.send(embed=embed)

    # Reload the Google sheet every hour so we can dynamically add
    # Without needing to restart the bot
    @loop(hours=24)
    async def reload_sheet(self):
        """Reload the google sheet every 24 hours"""
        self.sheet_map = {
            cipher_race_constants.HP: google_utils.get_dataframe_from_gsheet(
                self.spreadsheet.worksheet(cipher_race_constants.HP_SHEET_TAB_NAME),
                cipher_race_constants.COLUMNS
            ),
            cipher_race_constants.COMMON: google_utils.get_dataframe_from_gsheet(
                self.spreadsheet.worksheet(cipher_race_constants.COMMON_SHEET_TAB_NAME),
                cipher_race_constants.COLUMNS
            ),
            cipher_race_constants.CHALLENGE: google_utils.get_dataframe_from_gsheet(
                self.spreadsheet.worksheet(cipher_race_constants.CHALLENGE_SHEET_TAB_NAME),
                cipher_race_constants.COLUMNS
            )
        }
        print(f"Reloaded {cipher_race_constants.CODE} sheet on schedule")

    async def start_new_level(self, ctx, channel, embeds):
        """Send the codes for the next level. Used on a timer
        So the next level is sent out after a predetermined
        Break time after the previous level was completed.
        Then, starts the timer for the level to end
        """
        for embed in embeds:
            await ctx.send(embed=embed)
        timer = Timer(cipher_race_utils.compute_level_time(self.current_races[channel][cipher_race_constants.LEVEL]), self.send_times_up_message, callback_args=(ctx, channel, self.current_races[channel][cipher_race_constants.LEVEL]), callback_async=True)
        return

    async def send_times_up_message(self, ctx, channel, level):
        """After X seconds, the team's time is up and if they haven't solved all the codess,
        They need to restart their race.
        """
        # If there are no answers left, we assume the team solved the round
        if len(self.current_races[channel][cipher_race_constants.ANSWERS]) < 1 or self.current_races[channel][cipher_race_constants.LEVEL] != level:
            print(f"{channel}'s time is up, and they have completed the level!")
            return
        
        print(f"{channel}'s time is up, unlucky.")
        # Create an embed to send to the team. 
        embed = discord.Embed(color=constants.EMBED_COLOR)
        embed.add_field(name="Time's up!",
                        value=f"Sorry! Your time is up. You still had {len(self.current_races[channel][cipher_race_constants.ANSWERS])} "
                              f"{cipher_race_constants.CODE} left to solve for level {level}. "
                              f"If you'd like to re-attempt the race, use the {ctx.prefix}startcipherrace command!",
                        inline=False)
        embed.add_field(name="Answers",
                        value=f"The answers to the remaining codes were:\n"
                              f"{chr(10).join(self.current_races[channel][cipher_race_constants.ANSWERS])}",
                        inline=False)
        await ctx.send(embed=embed)
        self.current_races.pop(channel)
        return


def setup(bot):
    bot.add_cog(CipherRaceCog(bot))
