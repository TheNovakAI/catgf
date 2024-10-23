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

# Glif API credentials
GLIF_API_KEY = os.getenv('GLIF_API_KEY')
# Set GLIF_APP_ID directly since it's a constant value
GLIF_APP_ID = 'cm2lea2b80000h3rwev5sogoq'  # Replace with your actual Glif app ID if different

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
        "id": GLIF_APP_ID,
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
            while True:
                # Ask the user for verification
                print("\nGenerated Tweet:")
                print(f"\"{glif_output}\"\n")
                print("Enter '1' to send the tweet, '2' to regenerate with the same inputs.")
                user_choice = input("Your choice: ")

                if user_choice == '1':
                    # Post the output as a new tweet
                    post_new_tweet(glif_output)
                    return  # Exit after posting once
                elif user_choice == '2':
                    # Regenerate tweet content using the same inputs
                    glif_output = send_to_glif_api()
                    if not glif_output:
                        print("Failed to regenerate tweet. Exiting.")
                        return  # Exit if regeneration fails
                else:
                    print("Invalid input. Please enter '1' or '2'.")
        else:
            print("Failed to get output from Glif API.")
            return  # Exit if initial API call fails

if __name__ == "__main__":
    main()
