import os
import time
import tweepy
import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException

# Load environment variables from .env file
load_dotenv()

# Authentication with Twitter API v2
client = tweepy.Client(
    bearer_token=os.getenv('BEARER_TOKEN'),
    consumer_key=os.getenv('API_KEY'),
    consumer_secret=os.getenv('API_KEY_SECRET'),
    access_token=os.getenv('ACCESS_TOKEN'),
    access_token_secret=os.getenv('ACCESS_TOKEN_SECRET')
)

# Glif API key
glif_api_key = os.getenv('GLIF_API_KEY')
ToT_GLIF_ID = os.getenv('ToT_GLIF_ID')  # Glif App ID for ToT

# Monitor interval in minutes
monitor_interval = int(os.getenv('ToT_MONITOR_INTERVAL', '15'))  # Default to 15 minutes if not set

# Terminal of Truth account username
ToT_ACCOUNT = os.getenv('ToT_ACCOUNT', 'truth_terminal')  # Default to 'truth_terminal' if not set

# Variable to track the last tweet ID processed
last_tweet_id = None

# Function to call Glif API
def generate_response(tweet_content):
    headers = {
        "Authorization": f"Bearer {glif_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "id": ToT_GLIF_ID,  # Use Glif App ID from environment variable
        "inputs": {"tweet_content": tweet_content}
    }

    try:
        response = requests.post("https://simple-api.glif.app", headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("output", "")
    except RequestException as e:
        print(f"API request failed: {e}")
        return None

# Function to reply to a tweet
def reply_to_tweet(tweet_id, response_text):
    try:
        client.create_tweet(text=response_text, in_reply_to_tweet_id=tweet_id)
        print(f"Replied to tweet {tweet_id} with: {response_text}")
    except tweepy.TweepyException as e:
        print(f"Error replying to tweet: {e}")

# Function to monitor and handle tweets from ToT account
def monitor_user_tweets(username):
    global last_tweet_id

    try:
        # Fetch user information
        user = client.get_user(username=username)
        if user.data is None:
            print(f"User '{username}' not found.")
            return

        # Fetch recent tweets from the user timeline, fetching at least 5 as required by the API
        tweets = client.get_users_tweets(id=user.data.id, max_results=5)

        if tweets.data:
            # Get the most recent tweet
            latest_tweet = tweets.data[0]
            print(f"\nLatest Tweet from @{username}:")
            print(f"Tweet ID: {latest_tweet.id}")
            print(f"Tweet Content: {latest_tweet.text}\n")

            # Log the latest tweet even if not replying
            if last_tweet_id is None or latest_tweet.id != last_tweet_id:
                last_tweet_id = latest_tweet.id

                # Generate a response to the tweet
                response_text = generate_response(latest_tweet.text)
                if response_text:
                    print(f"Generated Reply: \"{response_text}\"")
                    reply_to_tweet(latest_tweet.id, response_text)
                else:
                    print("Failed to get a response from Glif API.")
            else:
                print(f"No new tweet since the last check. Latest Tweet ID: {last_tweet_id}")
        else:
            print(f"No tweets found for user '{username}'.")
    except tweepy.TweepyException as e:
        print(f"Error fetching tweets: {e}")

# Function to start monitoring
def start_monitoring():
    while True:
        monitor_user_tweets(ToT_ACCOUNT)
        time.sleep(monitor_interval * 60)

if __name__ == "__main__":
    start_monitoring()