import tweepy
import os
import time
from dotenv import load_dotenv
import requests
from requests.exceptions import RequestException
from datetime import datetime

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

# File to store the last seen tweet ID
LAST_SEEN_FILE = 'last_seen_id.txt'
FIRST_RUN_FILE = 'first_run_flag.txt'

# Function to read the last seen tweet ID from a file
def read_last_seen_id():
    try:
        with open(LAST_SEEN_FILE, 'r') as file:
            return int(file.read().strip())
    except FileNotFoundError:
        return None

# Function to write the last seen tweet ID to a file
def write_last_seen_id(last_seen_id):
    with open(LAST_SEEN_FILE, 'w') as file:
        file.write(str(last_seen_id))

# Function to check if it's the first run
def is_first_run():
    try:
        with open(FIRST_RUN_FILE, 'r') as file:
            return file.read().strip() == "true"
    except FileNotFoundError:
        return True

# Function to mark the first run as complete
def mark_first_run_complete():
    with open(FIRST_RUN_FILE, 'w') as file:
        file.write("false")

# Function to call Glif API
def generate_response(tweet_content):
    headers = {
        "Authorization": f"Bearer {glif_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "id": "cm2jmya15000012r1v9ukjb5v",
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
def reply_to_tweet(tweet_id, tweet_content):
    response_text = generate_response(tweet_content)
    if response_text:
        try:
            client.create_tweet(text=response_text, in_reply_to_tweet_id=tweet_id)
            print(f"Replied to tweet {tweet_id} with: {response_text}")
        except tweepy.TweepyException as e:
            print(f"Error replying to tweet: {e}")

# Function to monitor tweets from a specific user
def monitor_user_tweets(username):
    last_seen_id = read_last_seen_id()
    first_run = is_first_run()

    try:
        # Fetch user information
        user = client.get_user(username=username)
        if user.data is None:
            print(f"User '{username}' not found.")
            return

        # Fetch recent tweets from the user timeline
        tweets = client.get_users_tweets(id=user.data.id, max_results=5)

        if tweets.data:
            # Get the most recent tweet ID
            most_recent_tweet_id = max(tweet.id for tweet in tweets.data)

            if first_run:
                # On the first run, just store the last seen tweet ID without replying
                write_last_seen_id(most_recent_tweet_id)
                mark_first_run_complete()
                print(f"First run completed. Stored the most recent tweet ID: {most_recent_tweet_id}")
            else:
                # Process tweets in chronological order if not the first run
                for tweet in reversed(tweets.data):
                    if last_seen_id is None or tweet.id > last_seen_id:
                        reply_to_tweet(tweet.id, tweet.text)
                        last_seen_id = tweet.id
                        write_last_seen_id(last_seen_id)
                        time.sleep(10)  # Wait for 10 seconds before responding to the next tweet
    except tweepy.TweepyException as e:
        print(f"Error fetching tweets: {e}")

# Main function for continuous monitoring
def continuous_monitoring(username, interval=60):
    while True:
        monitor_user_tweets(username)
        print(f"Waiting for {interval} seconds before checking for new tweets...")
        time.sleep(interval)

# Example usage
if __name__ == "__main__":
    # Replace 'username' with the actual username of the account you want to monitor
    continuous_monitoring('truth_terminal')