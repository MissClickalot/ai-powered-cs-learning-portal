from flask import Flask, render_template, send_from_directory, request, jsonify
import spacy
import sqlite3
import http.client
import urllib.parse
import json

# Create an instance of the Flask class for the app
app = Flask(__name__)

# Define a route for the root URL
@app.route('/')
# Function to execute when user accesses the root URL
def index():
    # Use the index.html template
    return render_template('index.html')

# Define a route for each page
@app.route('/<page>')
def render_page(page):
    try:
        # Get keywords
        gcse_keywords = get_syllabus_keywords()
        # Get news data
        news_categories = get_news_categories()
        extracted_news = get_news(news_categories)
        return render_template(f'{page}.html', gcse_keywords=gcse_keywords, extracted_news=extracted_news)
    except:
        return "Page not found", 404

# Serve manifest.json from the static folder at the root URL
@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/service_worker.js')
def service_worker():
    return send_from_directory('static', 'service_worker.js')

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

# News
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

def get_news(news_categories):
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
            'api_token': 'S3TlQsEPjpmBP0mjxD2EPOBWoljfPYIQIJStKiR9',
            # 'categories': 'tech',
            'search': news_category,
            'domains': domains,
            'sort': 'published_on',
            'limit': 3, # Maximum requests on free plan
        })

        conn.request('GET', '/v1/news/all?{}'.format(params))

        res = conn.getresponse()
        data = res.read()

        # print(data.decode('utf-8'))

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

def get_syllabus_keywords():
    # Connect to the database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Fetch all keywords from the relevant table
    cursor.execute("SELECT category_title FROM syllabus_categories")
    rows = cursor.fetchall()

    # Convert to a list of strings
    gcse_keywords = [row[0] for row in rows]

    # Close the connection
    conn.close()

    return gcse_keywords

if __name__ == '__main__':
    # Start the Flask development server
    app.run()
