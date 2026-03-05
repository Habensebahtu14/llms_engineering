import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from scraper import fetch_website_contents

# Load environment variables
load_dotenv(override=True)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Configuration
MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = "You are a professional assistant that analyzes website content and provides structured summaries."

USER_PROMPT_PREFIX = """
Here are the contents of a website.
Provide a short summary of this website.
If it includes news or announcements, then summarize these too.
"""

def get_web_summary(url: str) -> str:
    """
    Scrapes a website and generates a summary using an LLM.
    """
    try:
        # Extract content using the scraper utility
        web_content = fetch_website_contents(url)
        
        # Prepare the conversation
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{USER_PROMPT_PREFIX}\n\n{web_content}"}
        ]
        
        # Generate completion
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"An error occurred during analysis: {str(e)}"

if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        url_to_analyze = sys.argv[1]
    else:
        
        url_to_analyze = "https://habensebhatu.nl"
        
    result = get_web_summary(url_to_analyze)
    print(f"\n--- Results for {url_to_analyze} ---\n")
    print(result)