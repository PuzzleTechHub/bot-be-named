import discord
import gspread
import json
import os
import constants
from oauth2client.service_account import ServiceAccountCredentials
import math
import pandas as pd


def create_embed() -> discord.Embed:
    """
    Create an empty discord embed with color.

    :return: (discord.Embed)
    """
    return discord.Embed(color=constants.EMBED_COLOR)


def create_level_prep_embed(level) -> discord.Embed:
    """
    Create an embed to let the team know their next level will start soon.
    
    :param level: (int) the level the team just completed.
    :param teamname: (str) the name of the team
    :return embed: (discord.Embed) the embed that includes the level-up message.
    """
    embed = create_embed()
    embed.add_field(name=f"Level {level} Complete!", value=f"Well done! Level {level+1} will begin in {constants.BREAK_TIME} seconds.")
    return embed


def get_opening_statement(sheet_used) -> discord.Embed:
    """
    Assemble the opening message to send to the team before their puzzle begins

    :return embed: (discord.Embed) the embed that includes the welcome message
    """
    embed = create_embed()
    embed.add_field(name=f"Welcome!", value=f"You have started a new race against the {sheet_used} wordlist! "
                                            f"Level 1 will start in about {constants.BREAK_TIME} seconds from this message! "
                                            f"You will have {constants.TIME_LIMIT} seconds to complete levels 1-5. "
                                            f"After every {constants.NUM_LEVELS}th level, you will get {constants.BONUS_TIME} "
                                            f"additional seconds (i.e you get {constants.TIME_LIMIT + constants.BONUS_TIME} "
                                            f"seconds to complete levels 6-10). Good luck and have fun!")
    return embed


def create_code_embed(level, codes):
    """
    Function to create the code embed
    :param level: (int) The level of the current puzzle solvers
    :param codes: (pandas.DataFrame) the current set of codes

    :return embeds: (list of discord.Embed) The embeds we create for the code
    :return code_answer: (list of str) the answers to the given codes
    """
    code_answers = []
    embed_list = []
    embed = create_embed()
    embed.add_field(name=f"Level {level}", value=f"Welcome to level {level}! You will have {compute_level_time(level)} " + \
    f"seconds to solve {level} {constants.CODE}s, beginning now.", inline=False)
    embed_list.append(embed)
    for i in range(level):
        code_proposal = codes.sample()
        embed_list.append(create_embed())
        embed_list[-1].add_field(name=f"{constants.CODE.capitalize()} #{i+1}", value=f"{code_proposal[constants.URL].item()}", inline=False)
        embed_list[-1].set_image(url=code_proposal[constants.URL].item())
        code_answers.append(code_proposal[constants.ANSWER].item().replace(' ', '').lower())
    embed_list.append(create_embed())
    embed_list[-1].add_field(name="Answering", value=f"Use {constants.BOT_PREFIX}answer to make a guess on any of the {constants.CODE}s.",
                    inline=False)
    return embed_list, code_answers


def create_no_code_embed() -> discord.Embed:
    """
    Function to create an embed to say there is no code

    :return embed: (discord.Embed) The embed we create
    """
    embed = create_embed()
    embed.add_field(name=f"No Current {constants.CODE.capitalize()}", 
                    value=f"You haven't started the race. To start, use command {constants.BOT_PREFIX}startrace.",
                    inline=False)
    return embed


def get_answer_result(user_answer, current_answers) -> str:
    """
    Return either correct or incorrect based on the team's answer and the list of codes.

    :param user_answer: (str) the answer given by the user
    :param current_answers: (list of str) the remaining answers for that team in the level

    :return result: (str) either correct or incorrect
    """
    user_answer = user_answer.lower()
    if user_answer in current_answers:
            current_answers.pop(current_answers.index(user_answer))
            result = constants.CORRECT
    else:
        result = constants.INCORRECT

    return result


def compute_level_time(level):
    """
    60 seconds on levels 1-5
    +10 on levels 6-10
    +10 on levels 10-15
    ...
    """
    return constants.TIME_LIMIT + constants.BONUS_TIME * math.floor((level - 1) / constants.NUM_LEVELS)


def get_dataframe_from_gsheet(sheet):
    """
    Load in all the values from the google sheet.
    NOTE: excludes headers from gsheet and replaces them with the ones in constants
    :return: (pd.DataFrame)
    """
    return pd.DataFrame(sheet.get_all_values()[1:], columns=constants.COLUMNS)


def create_gspread_client():
    """
    Create the client to be able to access google drive (sheets)
    """
    # Scope of what we can do in google drive
    scopes = ['https://www.googleapis.com/auth/spreadsheets']

    # Write the credentials file if we don't have it
    if not os.path.exists('client_secret.json'):
        json_creds = dict()
        for param in constants.JSON_PARAMS:
            json_creds[param] = os.getenv(param).replace('\"', '').replace('\\n', '\n')
        with open('client_secret.json', 'w') as f:
            json.dump(json_creds, f)
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scopes)
    return gspread.authorize(creds)


