import os
import time
import tweepy
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Twitter API credentials
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
API_KEY = os.getenv('API_KEY')
API_KEY_SECRET = os.getenv('API_KEY_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')

# Glif API key and App ID
GLIF_API_KEY = os.getenv('GLIF_API_KEY')
COMMUNITY_REPLY_GLIF_ID = os.getenv('Community_reply_GLIF_ID')  # Glif App ID from environment variable

# Target account to monitor
TARGET_USERNAME = os.getenv('TARGET_USERNAME', 'catgfcoin')  # Default to 'catgfcoin' if not set

# Monitoring interval in minutes
COMMUNITY_REPLY_MONITOR_INTERVAL = int(os.getenv('Community_reply_MONITOR_INTERVAL', '60'))  # Default to 60 minutes

# Authenticate with Twitter API v2
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_KEY_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET,
    wait_on_rate_limit=True
)

# Track last processed tweet ID to avoid duplication
last_tweet_id = None

def get_last_non_reply_tweet(username):
    global last_tweet_id

    # Fetch user information
    user = client.get_user(username=username)
    if user.data is None:
        print(f"User '{username}' not found.")
        return None

    # Fetch the user's recent tweets, excluding replies
    pagination_token = None
    while True:
        tweets_response = client.get_users_tweets(
            id=user.data.id,
            max_results=5,
            tweet_fields=['id', 'text', 'in_reply_to_user_id'],
            pagination_token=pagination_token
        )

        if tweets_response.data:
            for tweet in tweets_response.data:
                # Check if the tweet is not a reply and hasn't been processed before
                if tweet.in_reply_to_user_id is None and tweet.id != last_tweet_id:
                    last_tweet_id = tweet.id  # Update the last processed tweet ID
                    return tweet
            # If no non-reply tweets found, move to next page of results
            pagination_token = tweets_response.meta.get('next_token')
            if not pagination_token:
                break
        else:
            print(f"No tweets found for user '{username}'.")
            return None

    print(f"No non-reply tweets found for user '{username}'.")
    return None

def get_second_most_liked_reply(tweet_id, username):
    query = f"conversation_id:{tweet_id} is:reply -from:{username}"
    replies_response = client.search_recent_tweets(
        query=query,
        max_results=100,
        tweet_fields=['id', 'text', 'public_metrics', 'author_id'],
        expansions=['author_id']
    )

    if replies_response.data:
        # Map author IDs to usernames, if available
        users = {}
        if replies_response.includes and 'users' in replies_response.includes:
            users = {str(user.id): user.username for user in replies_response.includes['users']}

        replies = replies_response.data

        # Build a list of dictionaries for each reply
        replies_list = []
        for tweet in replies:
            tweet_dict = {
                'id': tweet.id,
                'text': tweet.text,
                'public_metrics': tweet.public_metrics,
                'author_id': tweet.author_id,
                'author_username': users.get(str(tweet.author_id), 'unknown')
            }
            replies_list.append(tweet_dict)

        # Sort replies by like count (popularity)
        sorted_replies = sorted(
            replies_list,
            key=lambda x: x['public_metrics']['like_count'],
            reverse=True
        )

        if len(sorted_replies) >= 1:
            # Return the most liked reply if at least one exists
            return sorted_replies[0]
        else:
            print("Not enough replies to find the second most liked one.")
            return None
    else:
        print("No replies found for the tweet.")
        return None

def send_to_glif_api(input_text):
    headers = {
        "Authorization": f"Bearer {GLIF_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "id": COMMUNITY_REPLY_GLIF_ID,
        "inputs": {"tweet_content": input_text}
    }

    try:
        response = requests.post("https://simple-api.glif.app", headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("output", "")
    except requests.RequestException as e:
        print(f"Glif API request failed: {e}")
        return None

def reply_to_tweet(reply_to_tweet_id, response_text):
    try:
        client.create_tweet(
            text=response_text,
            in_reply_to_tweet_id=reply_to_tweet_id
        )
        print(f"Replied to tweet {reply_to_tweet_id} with: {response_text}")
    except tweepy.TweepyException as e:
        print(f"Error replying to tweet: {e}")

def monitor_and_respond():
    last_processed_id = None
    while True:
        last_tweet = get_last_non_reply_tweet(TARGET_USERNAME)

        if last_tweet:
            print(f"Processing new tweet ID: {last_tweet.id}")
            if last_tweet.id != last_processed_id:
                last_processed_id = last_tweet.id  # Update last processed tweet ID
                second_most_liked_reply = get_second_most_liked_reply(last_tweet.id, TARGET_USERNAME)

                if second_most_liked_reply:
                    input_text = second_most_liked_reply['text']
                    print(f"\nReplying to user tweet with ID: {second_most_liked_reply['id']}")
                    print(f"User's message: {second_most_liked_reply['text']}\n")

                    # Generate Glif output
                    glif_output = send_to_glif_api(input_text)
                    if glif_output:
                        reply_to_tweet(second_most_liked_reply['id'], glif_output)
                    else:
                        print("Failed to get output from Glif API.")
                else:
                    print("No suitable replies to process.")
            else:
                print("No new tweets to process since the last check.")
        else:
            print("No new tweets found or already processed.")

        # Sleep for the specified interval before the next check
        time.sleep(COMMUNITY_REPLY_MONITOR_INTERVAL * 60)

if __name__ == "__main__":
    monitor_and_respond()