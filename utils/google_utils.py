import gspread
import os
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import json


JSON_PARAMS = [
    "type",
    "project_id",
    "private_key_id",
    "private_key",
    "client_email",
    "client_id",
    "auth_uri",
    "token_uri",
    "auth_provider_x509_cert_url",
    "client_x509_cert_url",
]


async def create_gspread_client() -> gspread.Client:
    """
    Create the client to be able to access google drive (sheets)
    """
    creds = get_gdrive_credentials()
    return gspread.authorize(creds)


async def get_gdrive_credentials() -> ServiceAccountCredentials:
    """
    Get google drive credentials
    """
    # Scope of what we can do in google drive
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    # Write the credentials file if we don't have it
    if not os.path.exists("client_secret.json"):
        json_creds = dict()
        for param in JSON_PARAMS:
            json_creds[param] = os.getenv(param).replace('"', "").replace("\\n", "\n")
        with open("client_secret.json", "w") as f:
            json.dump(json_creds, f)
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "client_secret.json", scopes
    )
    return creds


async def get_dataframe_from_gsheet(
    sheet: gspread.Spreadsheet, columns: list
) -> pd.DataFrame:
    """
    Load in all the values from the google sheet.
    NOTE: excludes headers from gsheet and replaces them with the ones in constants
    :param sheet: (gspread.Spreadsheet)
    :param columns: (list of str)
    :return: (pd.DataFrame)
    """
    return pd.DataFrame(sheet.get_all_values()[1:], columns=columns)


async def update_sheet_from_df(sheet: gspread.Spreadsheet, df: pd.DataFrame) -> None:
    """Dump the current dataframe onto the google sheet"""
    sheet.update([df.columns.values.tolist()] + df.values.tolist())


async def get_sheet_link(
    sheet: gspread.Spreadsheet, tab: gspread.Worksheet = None
) -> str:
    """Get the URL for a Google sheet. Optionally add a specific tab"""
    if tab:
        # Ensure the tab belongs to the sheet
        try:
            sheet.worksheet(tab.title)
        except gspread.exceptions.WorksheetNotFound:
            raise KeyError(f"Sheet {sheet.title} has no tab {tab.title}")
        return sheet.url + "#gid=" + str(tab.id)
    else:
        return sheet.url


GSPREAD_CLIENT = create_gspread_client()
