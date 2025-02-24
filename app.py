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
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/how-to-use')
def how_to_use():
    return render_template('how-to-use.html')

@app.route('/learn-offline')
def learn_offline():
    return render_template('learn-offline.html')

@app.route('/legal')
def legal():
    return render_template('legal.html')

@app.route('/news')
def news():
    try:
        # Get news data
        news_categories = get_news_categories()
        extracted_news = get_news(news_categories)
        return render_template('news.html', extracted_news=extracted_news)
    except:
        return "News page not available", 500

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/sign-in')
def sign_in():
    return render_template('sign-in.html')

@app.route('/sign-out')
def sign_out():
    return render_template('sign-out.html')

# Serve manifest.json from the static folder at the root URL
@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/service_worker.js')
def service_worker():
    return send_from_directory('static', 'service_worker.js')

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

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
