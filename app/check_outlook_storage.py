import requests
import pandas as pd

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
    return response.json()['access_token']

def check_storage(access_token, email):
    url = f"https://graph.microsoft.com/v1.0/users/{email}/mailFolders"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    folders = response.json()['value']
    
    total_size = sum(folder['sizeInBytes'] for folder in folders if 'sizeInBytes' in folder)  # This is in bytes
    total_size_mb = total_size / (1024 * 1024)  # Convert to megabytes
    return email, round(total_size_mb, 2)

# Read credentials
credentials = {}
with open('credentials.txt', 'r') as file:
    for line in file:
        key, value = line.strip().split('=')
        credentials[key] = value

# Get access token
access_token = get_access_token(credentials['ClientID'], credentials['TenantID'], credentials['ClientSecret'])

# Read accounts from CSV
accounts = pd.read_csv('accounts.csv')

# Check storage for each account
results = [check_storage(access_token, row['email']) for _, row in accounts.iterrows()]

# Write results to CSV
results_df = pd.DataFrame(results, columns=['Email', 'Total Size (MB)'])
results_df.to_csv('outlook_storage.csv', index=False)
