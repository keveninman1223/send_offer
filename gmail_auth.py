from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os

# Define the scopes required to send emails
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def authenticate():
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0)

    # Save the credentials for future use
    with open("token.json", "w") as token:
        token.write(creds.to_json())

    print("✅ Authentication successful! Token saved as token.json.")


if __name__ == "__main__":
    authenticate()
