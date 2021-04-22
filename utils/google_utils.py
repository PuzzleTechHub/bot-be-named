import gspread
import os
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import constants
import json

def create_gspread_client():
    """
    Create the client to be able to access google drive (sheets)
    """
    # Scope of what we can do in google drive
    scopes = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/drive']

    # Write the credentials file if we don't have it
    if not os.path.exists('client_secret.json'):
        json_creds = dict()
        for param in constants.JSON_PARAMS:
            json_creds[param] = os.getenv(param).replace('\"', '').replace('\\n', '\n')
        with open('client_secret.json', 'w') as f:
            json.dump(json_creds, f)
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scopes)
    return gspread.authorize(creds)


def get_dataframe_from_gsheet(sheet: gspread.Spreadsheet, columns: list) -> pd.DataFrame:
    """
    Load in all the values from the google sheet.
    NOTE: excludes headers from gsheet and replaces them with the ones in constants
    :param sheet: (gspread.Spreadsheet)
    :param columns: (list of str)
    :return: (pd.DataFrame)
    """
    return pd.DataFrame(sheet.get_all_values()[1:], columns=columns)


def update_sheet_from_df(sheet: gspread.Spreadsheet, df: pd.DataFrame):
    """Dump the current dataframe onto the google sheet"""
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

