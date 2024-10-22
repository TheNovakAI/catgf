#gpt only

import os
import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException

# Load environment variables from .env file
load_dotenv()

# OpenAI API key
openai_api_key = os.getenv('OPEN_AI_API_KEY')

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

# Main function to test GPT-4o response
def main():
    tweet_content = input("Enter the tweet content: ")
    response = generate_response(tweet_content)
    if response:
        print("GPT-4o Response:", response)

if __name__ == "__main__":
    main()
