import tweepy
import os
import time
from dotenv import load_dotenv
import requests
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

# OpenAI API key
openai_api_key = os.getenv('OPEN_AI_API_KEY')

# File to store the last seen tweet ID
LAST_SEEN_FILE = 'last_seen_id.txt'

# Function to read the last seen tweet ID from a file
def read_last_seen_id():
    try:
        with open(LAST_SEEN_FILE, 'r') as file:
            return int(file.read().strip())
    except FileNotFoundError:
        return 1848474839822082444  # Default to this ID if no history file exists

# Function to write the last seen tweet ID to a file
def write_last_seen_id(last_seen_id):
    with open(LAST_SEEN_FILE, 'w') as file:
        file.write(str(last_seen_id))

# Function to call OpenAI API
def generate_response(tweet_content):
    with open('system.txt', 'r') as file:
        system_message = file.read()
    with open('prompt.txt', 'r') as file:
        prompt_template = file.read()

    # Construct the prompt with the tweet content first
    prompt = f"{tweet_content} {prompt_template}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 150
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
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
    while True:
        try:
            # Fetch user information
            user = client.get_user(username=username)
            if user.data is None:
                print(f"User '{username}' not found.")
                return

            # Fetch recent tweets from the user timeline
            tweets = client.get_users_tweets(id=user.data.id, since_id=last_seen_id, max_results=5)
            if tweets.data:
                # Process tweets in chronological order
                for tweet in reversed(tweets.data):
                    if tweet.id > last_seen_id:
                        reply_to_tweet(tweet.id, tweet.text)
                        last_seen_id = tweet.id
                        write_last_seen_id(last_seen_id)
                        time.sleep(10)  # Wait for 10 seconds before responding to the next tweet
            time.sleep(60)  # Wait for a minute before fetching again
        except tweepy.TweepyException as e:
            print(f"Error fetching tweets: {e}")
            time.sleep(60)

# Example usage
if __name__ == "__main__":
    # Replace 'username' with the actual username of the account you want to monitor
    monitor_user_tweets('truth_terminal')
