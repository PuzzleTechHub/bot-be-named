from dotenv.main import load_dotenv
import discord
from discord.ext import commands
import asyncio
import os
import modules.code.code_utils as utils
from utils import google_utils
from modules.code import code_constants
import constants
from aio_timers import Timer
from emoji import EMOJI_ALIAS_UNICODE_ENGLISH as EMOJIS

load_dotenv()

# TODO: 
# Practice Mode with a timer?
#   - One code at a time
#   - Timer increases with each correct answer?
#   - Maybe start shooting out 2 at a time?
#   - High scores?
# Challenge mode with a certain level cap?
#   - Say ~challenge 3
#   - After 3 levels, gives a success message and ends the race
# Change


class CodeCog(commands.Cog):
    def __init__(self, bot):
        # Bot and code initializations
        self.bot = bot
        # The current race will have channel_id as key, with 
        # a dict containing level and current answers
        self.current_races = {}

        # Google Sheets Authentication and Initialization
        self.client = google_utils.create_gspread_client()

        # Default to HP Sheet
        self.sheet_key = os.getenv('HP_SHEET_KEY').replace('\'', '')
        self.sheet = self.client.open_by_key(self.sheet_key).sheet1
        # Store list of codes as a dataframe
        self.codes = utils.get_dataframe_from_gsheet(self.sheet)
        self.sheet_map = {
            code_constants.HP: utils.get_dataframe_from_gsheet(
                self.client.open_by_key(os.getenv("HP_SHEET_KEY").replace('\'', '')).sheet1),
            code_constants.COMMON: utils.get_dataframe_from_gsheet(
                self.client.open_by_key(os.getenv("COMMON_SHEET_KEY").replace('\'', '')).sheet1),
            code_constants.CHALLENGE: utils.get_dataframe_from_gsheet(
                self.client.open_by_key(os.getenv("CHALLENGE_SHEET_KEY").replace('\'', '')).sheet1),
        }
        
        # Reload the google sheet every hour
        bot.loop.create_task(self.reload_sheet())
            
    @commands.command(name='startrace', aliases=['StarTrace', 'StartRace'])
    async def startrace(self, ctx):
        """
        Start your race! You will have 60 seconds per level to solve the codes
        Usage: ~startrace
        """
        channel = ctx.channel.id
        if channel in self.current_races:
            print("startrace called from a channel that's already racing!!")
            embed = utils.create_embed()
            embed.add_field(name="Already Racing!",
                            value=f"Stop trying to start a new race while you have one going!",
                            inline=False)
            await ctx.send(embed=embed)
            return
        # Housekeeping
        print(f"Received startrace in channel {channel}")
        # Create entry in current_races
        self.current_races[channel] = dict()
        self.current_races[channel][code_constants.LEVEL] = 1
        # TODO: NEW: add a sheet option to hold multiple sheets
        # ~startrace eng gives you 1000 random english word sheet
        # ~startrace hp gives you the harry potter sheet
        sheet_used = None
        if len(ctx.message.content.split()) > 1 and ctx.message.content.split()[1] in self.sheet_map:
            sheet_used = ctx.message.content.split()[1]
            self.current_races[channel][code_constants.CODE] = self.sheet_map[sheet_used]
            embeds, self.current_races[channel][code_constants.ANSWERS] = utils.create_code_embed(
                self.current_races[channel][code_constants.LEVEL], self.current_races[channel][code_constants.CODE])

        # Creates the embeds containing the codes for that level as well as updates the IDs we're using and the acceptable answers for the level
        else:
            embeds, self.current_races[channel][code_constants.ANSWERS] = utils.create_code_embed(
                self.current_races[channel][code_constants.LEVEL], self.codes)
            sheet_used = code_constants.HP

        await ctx.send(embed=utils.get_opening_statement(sheet_used))
        # In a short time, send the codes
        time = Timer(code_constants.BREAK_TIME, self.start_new_level, callback_args=(ctx, channel, embeds), callback_async=True)

    @commands.command(name='endrace')
    async def endrace(self, ctx):
        """
        DONT USE PLS
        Ends the race
        Usage: ~endrace
        """
        channel = ctx.channel.id
        if channel not in self.current_races:
            embed = utils.create_embed()
            embed.add_field(name="No race!",
                            value="This channel doesn't have a race going on. You can't end something that hasn't started!",
                            inline=False)
            embed.add_field(name="Start Race",
                            value=f"To start a race, use {constants.BOT_PREFIX}startrace",
                            inline=False)
            await ctx.send(embed=embed)
            return
        self.current_races.pop(channel)
        embed = utils.create_embed()
        embed.add_field(name="Race Stopped",
                        value=f"To start a new race, use {constants.BOT_PREFIX}startrace",
                        inline=False)
        embed.add_field(name="Experimental",
                        value="ehm, this command is still in development. It actually probably didn't do anything, sorry!",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='practice', aliases=['pigpenpls'])
    async def practice(self, ctx):
        """
        Gives a cipher of a specific type. Defaults to random
        Usage: ~practice <cipher_name>
        """
        print("Received ~practice")
        toks = ctx.message.content.split()
        cipher_abbrev = None
        embed = utils.create_embed()
        used_cipher = None
        # Supply no arguments: randomly sample
        # Supply 2 arguments: sample specific code
        # Supply more arguments: incorrect
        if len(toks) < 2:
            # get random cipher
            proposal_row = self.codes.sample()
            used_cipher = proposal_row[code_constants.CODE].item()
        elif len(toks) == 2:
            if toks[1].lower() in self.codes[code_constants.CODE].value_counts().index:
                used_cipher = toks[1].lower()
            else:
                embed.add_field(name=f"{code_constants.CODE.capitalize()} Not Found",
                                value=f"Sorry! We can't find that {code_constants.CODE} in our database.",
                                inline=False)
                embed.add_field(name=f"Currently Supported {code_constants.CODE.capitalize()}",
                                value=f"{', '.join([index[0] for index in self.codes[code_constants.CODE].value_counts.index])}",
                                inline=False)
                await ctx.send(embed=embed)
                return
            proposal_row = self.codes[self.codes[code_constants.CODE] == used_cipher].sample()
        else:
            embed.add_field(name="Incorrect Usage",
                            value=f"Usage: {constants.BOT_PREFIX}practice or {constants.BOT_PREFIX}practice <{code_constants.CODE}_name>")
            await ctx.send(embed=embed)
            return

        embed.add_field(name=f"{used_cipher.capitalize()}",
                        value=f"{proposal_row[code_constants.URL].item()}")
        embed.add_field(name="Answer",
                        value=f"|| {proposal_row[code_constants.ANSWER].item()} ||")
        embed.set_image(url=proposal_row[code_constants.URL].item())
        await ctx.send(embed=embed)

    # Command to check the user's answer. They will be replied to telling them whether or not their answer is correct
    @commands.command(name='answer', aliases=['a'])
    async def answer(self, ctx):
        """
        Check your  answer
        Usage: ~answer <your answer>
        """
        channel = ctx.channel.id
        print(f"Received answer from {channel}")
        
        # if the team isn't puzzling then we need to instruct them to use startpuzzle command first.
        if channel not in self.current_races:
            embed = utils.create_embed()
            embed.add_field(name="No race!",
                            value="This channel doesn't have a race going on. You can't answer anything!",
                            inline=False)
            embed.add_field(name="Start Race",
                            value=f"To start a race, use {constants.BOT_PREFIX}startrace",
                            inline=False)
            await ctx.send(embed=embed)
            return
        print(f"All current answers: {self.current_races[channel][code_constants.ANSWERS]}")
        
        # Remove the command and whitespace from the answer.
        #user_answer = ctx.message.content.replace(f'{constants.BOT_PREFIX}answer', '').replace(' ', '')
        user_answer = ''.join(ctx.message.content.split()[1:])
        result = utils.get_answer_result(user_answer, self.current_races[channel][code_constants.ANSWERS])
        
        if result == code_constants.CORRECT:
            await ctx.message.add_reaction(EMOJIS[code_constants.CORRECT_EMOJI])
        else:
            await ctx.message.add_reaction(EMOJIS[code_constants.INCORRECT_EMOJI])

        # We pop off the correct answers as they are given, so at some point current_answers will be an empty list.
        # If there are more answers left, don't do any of that level complete nonsense.
        if len(self.current_races[channel][code_constants.ANSWERS]) >= 1:
            return
        # If there are no answers left for the round, then the team has completed the level
        # Create the next level prep embed
        embed = utils.create_level_prep_embed(self.current_races[channel][code_constants.LEVEL])
        # Proceed to next level. Perform computation ahead of time.
        self.current_races[channel][code_constants.LEVEL] += 1
        # Creates all code embeds, updates used code IDS, and refreshes current answers for the next level.
        if code_constants.CODE in self.current_races[channel]:
            embeds, self.current_races[channel][code_constants.ANSWERS] = utils.create_code_embed(
                self.current_races[channel][code_constants.LEVEL], self.current_races[channel][code_constants.CODE])
        else:
            embeds, self.current_races[channel][code_constants.ANSWERS] = utils.create_code_embed(
                self.current_races[channel][code_constants.LEVEL], self.codes)
        
        await ctx.send(embed=embed)
        Timer(code_constants.BREAK_TIME, self.start_new_level, callback_args=(ctx, channel, embeds), callback_async=True)

    @commands.command(name='reload')
    @commands.has_any_role(
        constants.BOT_WHISPERER
    )
    async def reload(self, ctx):
        """
        Reload the Google Sheet so we can update our codes instantly.
        Usage: ~reload
        """
        self.codes = utils.get_dataframe_from_gsheet(self.sheet)
        print(f"{constants.BOT_PREFIX}reload used. Reloaded {code_constants.CODE} sheet")
        embed = utils.create_embed()
        embed.add_field(name="Sheet Reloaded",
                        value="Google sheet successfully reloaded",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='reset')
    @commands.has_role(constants.BOT_WHISPERER)
    async def reset(self, ctx):
        """
        Admin Command.
        Reset the bot as if it has just loaded up
        Usage: ~reset
        Note: Does not reload google sheet. Use ~reload for that
        """
        self.current_races = {}
        embed = utils.create_embed()
        embed.add_field(name="Success",
                        value="Bot has been reset. I feel brand new!",
                        inline=False)
        await ctx.send(embed=embed)


    # Function to clean the bot's code so it can start a new one.
    # UPDATE: Don't reset used code IDs. We have enough. Only do that on a forced ~reset
    def reset_code(self, team):
        self.current_level[team] = 1
        self.current_answers[team] = []
        self.currently_puzzling[team] = False


    # Reload the Google sheet every hour so we can dynamically add
    # Without needing to restart the bot
    async def reload_sheet(self):
        await self.bot.wait_until_ready()
        while True:
            await asyncio.sleep(3600) # 1 hour
            self.codes = utils.get_dataframe_from_gsheet(self.sheet)
            print(f"Reloaded {code_constants.CODE} sheet on schedule")

    async def start_new_level(self, ctx, channel, embeds):
        """Send the codes for the next level. Used on a timer
        So the next level is sent out after a predetermined
        Break time after the previous level was completed.
        Then, starts the timer for the level to end
        """
        for embed in embeds:
            await ctx.send(embed=embed)
        timer = Timer(utils.compute_level_time(self.current_races[channel][code_constants.LEVEL]), self.send_times_up_message, callback_args=(ctx, channel, self.current_races[channel][code_constants.LEVEL]), callback_async=True)
        return

    async def send_times_up_message(self, ctx, channel, level):
        """After X seconds, the team's time is up and if they haven't solved all the codess,
        They need to restart their race.
        """
        # If there are no answers left, we assume the team solved the round
        if len(self.current_races[channel][code_constants.ANSWERS]) < 1 or self.current_races[channel][code_constants.LEVEL] != level:
            print(f"{channel}'s time is up, and they have completed the level!")
            return
        
        print(f"{channel}'s time is up, unlucky.")
        # Create an embed to send to the team. 
        embed = discord.Embed(color=constants.EMBED_COLOR)
        embed.add_field(name="Time's up!",
                        value=f"Sorry! Your time is up. You still had {len(self.current_races[channel][code_constants.ANSWERS])} "
                              f"{code_constants.CODE} left to solve for level {level}. "
                              f"If you'd like to re-attempt the race, use the {constants.BOT_PREFIX}startrace command!",
                        inline=False)
        embed.add_field(name="Answers",
                        value=f"The answers to the remaining codes were:\n"
                              f"{chr(10).join(self.current_races[channel][code_constants.ANSWERS])}", inline=False)
        await ctx.send(embed=embed)
        self.current_races.pop(channel)
        return


def setup(bot):
    bot.add_cog(CodeCog(bot))
