import os
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

# Function to call Glif API
def generate_response(tweet_content):
    headers = {
        "Authorization": f"Bearer {glif_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "id": "cm2m4ri2k0000a2uvel5tk2cp",  # Your Glif App ID
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

# Function to monitor and handle tweets from a specific user
def monitor_user_tweets(username):
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

            # Generate a response to the tweet
            response_text = generate_response(latest_tweet.text)
            if response_text:
                print("\nGenerated Reply:")
                print(f"\"{response_text}\"\n")
                print("Enter '1' to send the reply, '2' to regenerate with the same input.")
                user_choice = input("Your choice: ")

                if user_choice == '1':
                    # Post the generated reply as a reply to the tweet
                    reply_to_tweet(latest_tweet.id, response_text)
                elif user_choice == '2':
                    # Regenerate the reply
                    monitor_user_tweets(username)
                else:
                    print("Invalid input. Please enter '1' or '2'.")
            else:
                print("Failed to get a response from Glif API.")
        else:
            print(f"No tweets found for user '{username}'.")
    except tweepy.TweepyException as e:
        print(f"Error fetching tweets: {e}")

if __name__ == "__main__":
    # Replace 'truth_terminal' with the actual username of the account you want to monitor
    monitor_user_tweets('truth_terminal')
