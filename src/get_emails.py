import requests
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from helpers.config import email_google_sheet, CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, ZOHO_API_BASE_URL, TOKEN_URL
from helpers.create_email import create_email

# Constants for Google Sheets
SPREADSHEET_ID = email_google_sheet
SERVICE_ACCOUNT_FILE = 'credentials.json'

def get_access_token(client_id, client_secret, refresh_token):
    """
        - Parameters:
            - client_id: str
            - client_secret: str
            - refresh_token: str
            
        - Returns:
            - str: access_token
            
        - Description:
            - Fetches the access token from Zoho CRM using the client_id, client_secret, and refresh_token.
    """
    payload = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, data=payload, headers=headers)
    response.raise_for_status()
    return response.json().get("access_token")

def fetch_emails_from_zoho(access_token):
    """
        - Parameters:
            - access_token: str
            
        - Returns:
            - list: zoho_emails
            
        - Description:
            - Fetches the emails from Zoho CRM using the access_token.
    """
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    response = requests.get(f"{ZOHO_API_BASE_URL}/Leads", headers=headers)
    response.raise_for_status()
    return [record.get("Email") for record in response.json().get("data", []) if record.get("Email")]

def upload_to_google_sheets(data):
    """
        - Parameters:
            - data: list
            
        - Description:
            - Uploads the data to Google Sheets.
    """
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build('sheets', 'v4', credentials=credentials)
    
    values = [[row.get('Email_address'), row.get('Subject'), row.get('Email Template Body')] for row in data]
    
    body = {'values': values}
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='Sheet1!A1', 
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS", 
        body=body
    ).execute()

def main():
    """
    Main function to authenticate with Zoho CRM, fetch emails, save emails to 
    CSV file, generate emails, and upload emails to Google Sheets.
    """
    print("Authenticating with Zoho CRM...")
    access_token = get_access_token(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)

    print("Fetching emails from Zoho CRM...")
    zoho_emails = fetch_emails_from_zoho(access_token)

    if not zoho_emails:
        print("No emails found!")
        return

    # Save Zoho emails to CSV file
    pd.DataFrame({"Email": zoho_emails}).to_csv("data/zoho_emails.csv", index=False)
    print(f"Saved {len(zoho_emails)} emails to data/zoho_emails.csv")

    # Generate emails based on `prospects.csv`
    generated_emails_df = create_email()
    email_data = generated_emails_df.to_dict('records')
    upload_to_google_sheets(email_data)

    print("Emails successfully uploaded to Google Sheets!")

if __name__ == "__main__":
    main()