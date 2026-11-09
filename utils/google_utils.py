import gspread
import os

from oauth2client.service_account import ServiceAccountCredentials
import json

"""
Google utils. Used for any operations related to accessing the bot's Google accounts and credentials. 
Used in any module that uses sheets (sheets, lion, hydra...)
"""

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


def create_gspread_client() -> gspread.Client:
    """
    Create the client to be able to access google drive (sheets)
    """
    creds = get_gdrive_credentials()
    return gspread.authorize(creds)


def get_gdrive_credentials() -> ServiceAccountCredentials:
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
