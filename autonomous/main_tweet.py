import os
import time
import tweepy
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Twitter API credentials (unbranded)
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
API_KEY = os.getenv('API_KEY')
API_KEY_SECRET = os.getenv('API_KEY_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')

# Glif API credentials (unbranded)
GLIF_API_KEY = os.getenv('GLIF_API_KEY')
# Branded GLIF ID
MAIN_TWEET_GLIF_ID = os.getenv('MAIN_TWEET_GLIF_ID')  # Glif App ID from environment variable

# Monitoring interval in minutes
MONITOR_INTERVAL_MINUTES = int(os.getenv('MAIN_TWEET_MONITOR_INTERVAL_MINUTES', '120'))  # Default to 120 minutes

# Authenticate with Twitter API v2
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_KEY_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET,
    wait_on_rate_limit=True
)

def send_to_glif_api():
    headers = {
        "Authorization": f"Bearer {GLIF_API_KEY}",
        "Content-Type": "application/json"
    }

    # Prepare the payload
    payload = {
        "id": MAIN_TWEET_GLIF_ID,
        # Omit 'inputs' if no inputs are required, or set it to an empty dictionary
        "inputs": {}
    }

    try:
        response = requests.post("https://simple-api.glif.app", headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("output", "")
    except requests.RequestException as e:
        print(f"Glif API request failed: {e}")
        return None

def post_new_tweet(tweet_text):
    try:
        client.create_tweet(text=tweet_text)
        print(f"Posted new tweet: {tweet_text}")
    except tweepy.TweepyException as e:
        print(f"Error posting new tweet: {e}")

def main():
    while True:
        # Generate new tweet content using the Glif API
        glif_output = send_to_glif_api()

        if glif_output:
            # Post the output as a new tweet automatically
            post_new_tweet(glif_output)
        else:
            print("Failed to get output from Glif API.")

        # Sleep for the specified interval before the next check
        time.sleep(MONITOR_INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    main()