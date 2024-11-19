import requests
import pandas as pd
import logging
import time
from datetime import datetime, timedelta

def get_access_token(client_id, tenant_id, client_secret):
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    body = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    response = requests.post(url, headers=headers, data=body)
    response.raise_for_status()
    return response.json()['access_token'], datetime.now() + timedelta(minutes=55)

def delete_all_emails(access_token, email, client_id, tenant_id, client_secret):
    def make_request(url, headers):
        response = requests.get(url, headers=headers)
        if response.status_code == 401:
            logging.info(f"{datetime.now()} - Token expired. Refreshing token.")
            new_token, _ = get_access_token(client_id, tenant_id, client_secret)
            headers['Authorization'] = f'Bearer {new_token}'
            response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response

    url = f"https://graph.microsoft.com/v1.0/users/{email}/mailFolders"
    headers = {'Authorization': f'Bearer {access_token}'}

    response = make_request(url, headers)
    folders = response.json()['value']

    for folder in folders:
        folder_id = folder['id']
        logging.info(f"{datetime.now()} - Processing folder: {folder['displayName']} for {email}")
        
        while True:
            messages_url = f"https://graph.microsoft.com/v1.0/users/{email}/mailFolders/{folder_id}/messages"
            messages_response = make_request(messages_url, headers)
            messages = messages_response.json()['value']

            if not messages:
                break  # Exit loop if no more messages

            for message in messages:
                message_id = message['id']
                delete_url = f"https://graph.microsoft.com/v1.0/users/{email}/messages/{message_id}"
                delete_response = requests.delete(delete_url, headers=headers)
                if delete_response.status_code == 401:
                    logging.info(f"{datetime.now()} - Token expired. Refreshing token.")
                    access_token, token_expiry = get_access_token(client_id, tenant_id, client_secret)
                    headers['Authorization'] = f'Bearer {access_token}'
                    delete_response = requests.delete(delete_url, headers=headers)
                delete_response.raise_for_status()
            
            time.sleep(1)  # Adding a delay between batches

        logging.info(f"{datetime.now()} - Deleted all messages in folder {folder['displayName']} for {email}")

# Read credentials
credentials = {}
with open('credentials.txt', 'r') as file:
    for line in file:
        key, value = line.strip().split('=')
        credentials[key] = value

# Set up logging
logging.basicConfig(filename='deleted_mails.log', level=logging.INFO)

# Get initial access token
access_token, token_expiry = get_access_token(credentials['ClientID'], credentials['TenantID'], credentials['ClientSecret'])

# Read accounts from CSV
accounts = pd.read_csv('accounts.csv')

# Delete all emails for each account
for _, row in accounts.iterrows():
    if datetime.now() >= token_expiry:
        access_token, token_expiry = get_access_token(credentials['ClientID'], credentials['TenantID'], credentials['ClientSecret'])
    
    delete_all_emails(access_token, row['email'], credentials['ClientID'], credentials['TenantID'], credentials['ClientSecret'])
    logging.info(f"{datetime.now()} - Completed deletion for {row['email']}")

logging.info(f"{datetime.now()} - Script execution completed.")
