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

# Glif API credentials
GLIF_API_KEY = os.getenv('GLIF_API_KEY')
MAIN_TWEET_COMMUNITY_REPLY_GLIF_ID = os.getenv('MAIN_TWEET_COMMUNITY_REPLY_GLIF_ID')  # Glif App ID from environment variable

# Target account to monitor
TARGET_USERNAME = os.getenv('MAIN_TWEET_COMMUNITY_REPLY_TARGET_USERNAME', 'jusscubs')  # Default to 'jusscubs' if not set

# Monitoring interval in minutes
MAIN_TWEET_COMMUNITY_REPLY_MONITOR_INTERVAL = int(os.getenv('MAIN_TWEET_COMMUNITY_REPLY_MONITOR_INTERVAL', '90'))  # Default to 90 minutes

# Authenticate with Twitter API v2
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_KEY_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET,
    wait_on_rate_limit=True
)

def get_last_non_reply_tweet(username):
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
            max_results=100,  # Fetch up to 100 tweets per request
            tweet_fields=['id', 'text', 'in_reply_to_user_id'],
            pagination_token=pagination_token,
            exclude=['replies']  # Exclude replies
        )

        if tweets_response.data:
            for tweet in tweets_response.data:
                # If 'in_reply_to_user_id' is None, it's not a reply
                if tweet.in_reply_to_user_id is None:
                    return tweet
            # If all tweets in this batch are replies, get the next page
            pagination_token = tweets_response.meta.get('next_token')
            if not pagination_token:
                break  # No more pages to fetch
        else:
            print(f"No tweets found for user '{username}'.")
            return None

    print(f"No non-reply tweets found for user '{username}'.")
    return None

def get_top_liked_replies(tweet_id, username, top_n=5):
    query = f"conversation_id:{tweet_id} is:reply -from:{username}"
    replies_response = client.search_recent_tweets(
        query=query,
        max_results=100,
        tweet_fields=['id', 'text', 'public_metrics', 'in_reply_to_user_id'],
        expansions=['author_id'],
        user_fields=['username']
    )

    if replies_response.data:
        replies = replies_response.data

        # Build a list of dictionaries with 'text' and 'like_count'
        replies_list = []
        for reply in replies:
            like_count = reply.public_metrics.get('like_count', 0)
            replies_list.append({
                'text': reply.text,
                'like_count': like_count
            })

        # Sort the replies by 'like_count' in descending order
        sorted_replies = sorted(replies_list, key=lambda x: x['like_count'], reverse=True)

        # Use however many replies are available (up to top_n)
        top_replies_texts = [reply['text'] for reply in sorted_replies[:top_n]]
        return top_replies_texts
    else:
        print(f"No replies found for tweet ID {tweet_id}.")
        return []

def send_to_glif_api(inputs_list):
    headers = {
        "Authorization": f"Bearer {GLIF_API_KEY}",
        "Content-Type": "application/json"
    }

    # Prepare the payload
    payload = {
        "id": MAIN_TWEET_COMMUNITY_REPLY_GLIF_ID,
        "inputs": inputs_list  # Sending the list of top replies as inputs
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

def monitor_and_respond():
    while True:
        last_tweet = get_last_non_reply_tweet(TARGET_USERNAME)

        if last_tweet:
            print(f"Processing new tweet ID: {last_tweet.id}")
            replies_texts = get_top_liked_replies(last_tweet.id, TARGET_USERNAME, top_n=5)

            if replies_texts:
                # Send the replies to the Glif API and post the generated tweet automatically
                glif_output = send_to_glif_api(replies_texts)
                if glif_output:
                    post_new_tweet(glif_output)
                else:
                    print("Failed to get output from Glif API.")
            else:
                print("No replies to process.")
        else:
            print("No new tweets found or already processed.")

        # Sleep for the specified interval before the next check
        time.sleep(MAIN_TWEET_COMMUNITY_REPLY_MONITOR_INTERVAL * 60)

if __name__ == "__main__":
    monitor_and_respond()