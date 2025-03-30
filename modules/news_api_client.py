# Libraries
import sqlite3
import http.client
import urllib.parse
import json
import os  # For environment variables (API token)
from dotenv import load_dotenv  # For environment variables (API token)
from pathlib import Path  # For environment variables (API token)

# Load environment variables from .env file found in parent directory
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv()

# Function to extract news categories from database
def get_news_categories():
    # Connect to the database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Fetch all news categories from the relevant table
    cursor.execute("SELECT news_category_title FROM news_categories")
    rows = cursor.fetchall()

    # Convert to a list of strings
    news_categories = [row[0] for row in rows]

    # Close the connection
    conn.close()

    return news_categories

# Function to make news API requests to extract articles using news category data
def get_news(news_categories):
    # Load token from environment
    api_token = os.getenv("NEWS_API_TOKEN")

    # Establish connection to API
    conn = http.client.HTTPSConnection('api.thenewsapi.com')

    # Dictionary for extracted news
    extracted_news = {}

    for news_category in news_categories:

        if news_category == 'Python':
            domains = 'thehackernews.com'
        else:
            domains = 'quantamagazine.org,bbc.co.uk'

        params = urllib.parse.urlencode({
            'api_token': api_token,
            'search': news_category,
            'domains': domains,
            'sort': 'published_on',
            'limit': 3, # Maximum requests on free plan
        })

        conn.request('GET', '/v1/news/all?{}'.format(params))

        res = conn.getresponse()
        data = res.read()

        # Parse JSON response
        try:
            news_data = json.loads(data)
            articles = news_data.get("data", [])

            # Extract title, description, and URL
            extracted_news[news_category] = [
                {
                    "title": article["title"],
                    "description": article["description"],
                    "url": article["url"],
                    "date": article["published_at"][:10]  # Extracts YYYY-MM-DD
                }
                for article in articles
            ]

        except json.JSONDecodeError:
            print("Error parsing JSON response")
            extracted_news[news_category] = []

    # Return the extracted information
    return extracted_news