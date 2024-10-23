import os
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

# Glif API key
GLIF_API_KEY = os.getenv('GLIF_API_KEY')
GLIF_APP_ID = 'cm2lehw8800004tsgm3yxmqw0'  # Replace with your actual Glif app ID

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
            max_results=5,
            tweet_fields=['id', 'text', 'in_reply_to_user_id'],
            pagination_token=pagination_token
        )

        if tweets_response.data:
            for tweet in tweets_response.data:
                # Check if the tweet is not a reply
                if tweet.in_reply_to_user_id is None:
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
        "id": GLIF_APP_ID,
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

def main():
    username = 'catgfcoin'  # Replace with the target username
    last_tweet = get_last_non_reply_tweet(username)

    if last_tweet:
        print(f"Processing new tweet ID: {last_tweet.id}")
        second_most_liked_reply = get_second_most_liked_reply(last_tweet.id, username)

        if second_most_liked_reply:
            input_text = second_most_liked_reply['text']
            print(f"\nReplying to user tweet with ID: {second_most_liked_reply['id']}")
            print(f"User's message: {second_most_liked_reply['text']}\n")

            while True:
                # Generate Glif output
                glif_output = send_to_glif_api(input_text)
                if glif_output:
                    print("\nGenerated Reply:")
                    print(f"\"{glif_output}\"\n")
                    print("Enter '1' to send the reply, '2' to regenerate with the same inputs.")
                    user_choice = input("Your choice: ")

                    if user_choice == '1':
                        # Post the output as a reply
                        reply_to_tweet(second_most_liked_reply['id'], glif_output)
                        break  # Exit after replying once
                    elif user_choice == '2':
                        continue  # Regenerate the reply
                    else:
                        print("Invalid input. Please enter '1' or '2'.")
                else:
                    print("Failed to get output from Glif API.")
                    return  # Exit if API call fails
        else:
            print("No replies to process.")
    else:
        print("No new tweets found or already processed.")

if __name__ == "__main__":
    main()
