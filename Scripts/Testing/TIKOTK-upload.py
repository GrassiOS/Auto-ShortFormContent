import requests
import webbrowser
from flask import Flask, request
import threading


# Replace with your own TikTok app credentials
CLIENT_KEY = "sbawst680fmieojq9a"
CLIENT_SECRET = "6eAS8PoTOPpS4bzLmX5UyOFrvmoYyi6Z"
REDIRECT_URI = "http://localhost:3000"  # Set your redirect URI to localhost

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def home():
    authorization_code = request.args.get('code')
    if authorization_code:
        print(f'Authorization code received: {authorization_code}')
        
        # Exchange the authorization code for an access token
        token_url = "https://open-api.tiktok.com/oauth/access_token"
        payload = {
            "client_key": CLIENT_KEY,
            "client_secret": CLIENT_SECRET,
            "code": authorization_code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        }
        
        # Make the POST request to get the access token
        response = requests.post(token_url, data=payload)
        response_data = response.json()

        # Check if the response is successful
        if response.status_code == 200 and "data" in response_data:
            access_token = response_data["data"]["access_token"]
            print(f"Access token: {access_token}")
        else:
            print("Failed to get access token:", response_data)
        
        return "Authorization code received! You can close this window."

    return "Waiting for authorization code..."

def run_server():
    app.run(port=3000)

# Step 1: Generate the TikTok authorization URL
auth_url = (
    f"https://open-api.tiktok.com/platform/oauth/connect?"
    f"client_key={CLIENT_KEY}&response_type=code&scope=user.info.basic&redirect_uri={REDIRECT_URI}&state=your_custom_state"
)

# Start the Flask server in a new thread
threading.Thread(target=run_server).start()

# Step 2: Open the browser to allow the user to authorize the app
print("Opening the authorization URL in your browser...")
webbrowser.open(auth_url)

print("Please authorize the app and then return to the terminal.")
