import gspread
from oauth2client.service_account import ServiceAccountCredentials
from helpers.create_call_script import generate_call_script
import requests
import json
from helpers.config import email_google_sheet, call_script_google_sheet, CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, ZOHO_API_BASE_URL, TOKEN_URL

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
    print("Fetching Zoho access token...")
    payload = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, data=payload, headers=headers)

    try:
        response.raise_for_status()
        response_json = response.json()
        if "access_token" in response_json:
            print("Access token obtained successfully.")
            return response_json["access_token"]
        else:
            raise Exception(f"Failed to get access token: {response_json.get('error', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request error: {e}")

def authorize_google_sheets():
    """
        - Parameters:
            - None
            
        - Returns:
            - gspread.client.Client: client
            
        - Description:
            - Authorizes Google Sheets using the credentials.json file.
    """
    try:
        print("Authorizing Google Sheets...")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials = ServiceAccountCredentials.from_json_keyfile_name('/home/fox/ai/src/credentials.json', scope)
        return gspread.authorize(credentials)
    except Exception as e:
        raise Exception(f"Error authorizing Google Sheets: {e}")

def upload_to_zoho(email, call_script, access_token):
    """
        - Parameters:
            - email: str
            - call_script: str
            - access_token: str
            
        - Returns:
            - None
            
        - Description:
            - Uploads the lead to Zoho CRM.
    """
    url = f"{ZOHO_API_BASE_URL}/Leads"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "data": [{"Email": email, "Call_Script": call_script}]
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        print(f"Successfully uploaded lead to Zoho CRM: {email}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to upload lead to Zoho CRM for {email}: {response.text}")

def upload_to_google_sheet(email, call_script, new_sheet_id):
    """
        - Parameters:
            - email: str
            - call_script: str
            - new_sheet_id: str
            
        - Returns:
            - None
            
        - Description:
            - Uploads the lead to the Google Sheet.
    """
    client = authorize_google_sheets()
    try:
        sheet = client.open_by_key(new_sheet_id).sheet1
        first_name, last_name = (email.split('@')[0].split('.') + [""])[:2]
        sheet.append_row([email, first_name, last_name, call_script])
        print(f"Successfully uploaded lead to Google Sheet: {email}")
    except Exception as e:
        print(f"Failed to upload to Google Sheet: {e}")

def process_email_tracking(sheet_id, new_sheet_id):
    """
        - Parameters:
            - sheet_id: str
            - new_sheet_id: str
            
        - Returns:
            - None
            
        - Description:
            - Processes the email tracking sheet and generates call scripts.
    """
    client = authorize_google_sheets()
    sheet = client.open_by_key(sheet_id).sheet1
    rows = sheet.get_all_records()

    try:
        access_token = get_access_token(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
    except Exception as e:
        print(f"Error obtaining access token: {e}")
        return

    for index, row in enumerate(rows):
        try:
            email = row.get('Email_address')
            
            open_amount = row.get('Open_Amount', '')
            try:
                open_amount = int(open_amount) if open_amount else 0
            except ValueError:
                open_amount = 0  

            # Can adjust the open amount here: 
            if open_amount > 5:
                # Generate the call script and upload
                call_script = generate_call_script(row)
                upload_to_google_sheet(email, call_script, new_sheet_id)
                upload_to_zoho(email, call_script, access_token)

                sheet.delete_rows(index + 2)  
                print(f"Processed and removed row for: {email}")
        except Exception as e:
            print(f"Error processing row {index + 1}: {e}")

if __name__ == "__main__":
    try:
        """
        Main function to process email tracking sheet and generate call scripts.
        """
        source_sheet_id = email_google_sheet 
        destination_sheet_id = call_script_google_sheet 
        process_email_tracking(source_sheet_id, destination_sheet_id)
    except Exception as e:
        print(f"Critical error occurred: {e}")