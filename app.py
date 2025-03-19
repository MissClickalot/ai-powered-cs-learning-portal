from flask import Flask, request, render_template, send_from_directory, redirect, url_for
import spacy
import sqlite3
import http.client
import urllib.parse
import json
from password_validation import validate_password, hash_password, verify_password  # Import own python password validation code
import jsonify
import secrets
import requests
import os
import queue
import sounddevice as sd
import vosk

# Create an instance of the Flask class for the app
app = Flask(__name__)

app.secret_key = secrets.token_hex(32)  # Generates a secure 32-byte random hex key


# Initialise the spaCy engine
# en_core_web_sm is a pre-trained model that knows English grammar and vocabulary
nlp = spacy.load("en_core_web_sm")

"""
Cleans and preprocesses the search query by:
- Lowercasing
- Removing stopwords
- Removing punctuation
- Lemmatising words

This:
- Ensures efficient processing
- Removes unimportant words
- Extracts relevant words
"""
def preprocess_query(query):
    # Convert the query to lowercase
    query = query.lower()
    # Process the query with spaCy
    query_processed = nlp(query)
    # Tokenise the query and store in list
    query_tokens = [query_token.lemma_ for query_token in query_processed if not query_token.is_stop and not query_token.is_punct]

    # Return a list of important words
    return query_tokens

"""
Named Entity Recognition (NER) to extract key topics.
Extracts named entities (like AI, ML, Python) from the given text.
"""
def extract_entities(query):
    # Identify key topics from a query using spaCy's Named Entity Recognition (NER)
    query = nlp(query)
    query_entities = {ent.text: ent.label_ for ent in query.ents}

    return query_entities

def fetch_json_data(url, headers):
    try:
        # GET request
        response = requests.get(url, headers=headers)
        # Raise an error for bad responses (e.g., 404, 500)
        response.raise_for_status()
        # Parse JSON response as a dictionary
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def filter_json(data, preprocessed_query):
    filtered_data_list = []
    for word in preprocessed_query:
        filtered_data = [item for item in data if word in item.get("outcome", "").lower()]
        if filtered_data:
            filtered_data_list.append(filtered_data[0])

    return filtered_data_list

def load_stt_model():
    # Path to the Vosk model
    model_path = "static/vosk_model"

    # Check if the model exists
    if not os.path.exists(model_path):
        raise FileNotFoundError("Speech recognition model not found. Please use the text box instead.")

    # Load Vosk model
    return vosk.Model(model_path)

# Callback function to process audio
def stt_callback(indata, frames, time, status):
    if status:
        print(status, flush=True)
    audio_queue.put(bytes(indata))

def stt_recognise_speech():
    # Set up the microphone input
    with sd.RawInputStream(samplerate=16000,  # Set sample rate to 16kHz as required by vosk
                           blocksize=8000,  # Block size determines the amount of audio processed at a time
                           dtype="int16",  # Data type for raw audio (16-bit PCM)
                           channels=1,  # Mono audio input (single channel)
                           callback=stt_callback):  # Function to process incoming audio

        # Initialise the Vosk speech recogniser with the model
        recognizer = vosk.KaldiRecognizer(model, 16000)

        print("Listening...")

        while True:
            # Get the next chunk of audio data from the queue
            data = audio_queue.get()
            # Check if the recogniser detects a speech segment
            if recognizer.AcceptWaveform(data):
                # Convert the result from JSON format to a Python dictionary
                result = json.loads(recognizer.Result())
                # Print the output
                print("You said:", result["text"])

def get_learning_content(filtered_data_list, material_type, headers):
    # Mine the JSON to get the url of the outcome ID
    # Create an empty list to append items containing data
    trimmed_data = []
    for item in filtered_data_list:
        id_to_mine = item.get("outcome_id", "")
        url_to_mine = f"https://bit-by-bit.org/api/{material_type}?_format=json&outcome_id={id_to_mine}"
        data = fetch_json_data(url_to_mine, headers)
        # Only add it to list if it contains data
        if data:
            trimmed_data.append(data[0])

    return trimmed_data

def get_hyperlinked_content(content):
    hyperlinked_content = {}
    entry = 0
    for content_item in content:
        entry += 1
        hyperlinked_content[entry] = {'title':content_item.get("title"), 'url':content_item.get("url")}

    return hyperlinked_content

# Function to get user by email from the database
def get_user_by_email(email = "evie.paige.anderson@gmail.com"):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, password_hash FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()  # Returns (id, email, password_hash) or None
    conn.close()
    return user # Returns a tuple (id, email, password_hash) or None

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

# Function to extract syllabus categories from database
def get_syllabus_keywords():
    # Connect to the database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Fetch all keywords from the relevant table
    cursor.execute("SELECT category_title FROM syllabus_categories")
    rows = cursor.fetchall()

    # Convert to a list of strings
    syllabus_keywords = [row[0] for row in rows]

    # Close the connection
    conn.close()

    return syllabus_keywords

# Function to collate all file paths of static resources grouped by syllabus categories
def get_local_resources_by_category(syllabus_keywords):
    """
    Retrieves local resources grouped by syllabus categories.

    :param syllabus_keywords: list of syllabus keywords.
    :return: Dictionary where keys are category titles and values are lists of local resources.
    """
    # Connect to the database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # SQL Query to JOIN both tables
    query = """
    SELECT sc.category_title, lr.file_reference
    FROM local_resources lr
    JOIN syllabus_categories sc ON lr.syllabus_categories_id = sc.id
    ORDER BY sc.category_title;
    """

    # Execute the query
    cursor.execute(query)
    results = cursor.fetchall()

    # Close connection
    conn.close()

    # Organise results into a dictionary
    resources_by_category = {}
    for category, file_reference in results:
        if category not in resources_by_category:
            resources_by_category[category] = []
        resources_by_category[category].append(file_reference)

    return resources_by_category

# Define a route for the root URL
@app.route('/', methods=['GET', 'POST'])
# Function to execute when user accesses the root URL
def index():
    hyperlinked_learning_content = {}
    if request.method == 'POST':
        # Get input from HTML form
        query = request.form.get('user_input')
        preprocessed_query = preprocess_query(query)

        # URL of the JSON API
        url = "https://bit-by-bit.org/api/learning-outcomes?_format=json"
        # Define headers
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        # Fetch the JSON data
        json_data = fetch_json_data(url, headers)

        # Filter the JSON data to match keywords
        filtered_data_list = filter_json(json_data, preprocessed_query)

        # Get learning content which matches the outcome IDs
        learning_content = get_learning_content(filtered_data_list, "learning-by-outcome", headers)
        # Get testing content which matches the outcome IDs
        testing_content = get_learning_content(filtered_data_list, "self-test-by-outcome", headers)
        # Get GCSE questions content which matches the outcome IDs
        gcse_questions_content = get_learning_content(filtered_data_list, "gcse-questions-by-outcome", headers)

        hyperlinked_learning_content = get_hyperlinked_content(learning_content)

        # Use the index.html template
        return render_template('index.html', hyperlinked_learning_content=hyperlinked_learning_content)
    # Render the HTML
    return render_template('index.html', hyperlinked_learning_content=hyperlinked_learning_content)

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
    try:
        # Get local resources
        syllabus_keywords = get_syllabus_keywords()
        resources_by_category = get_local_resources_by_category(syllabus_keywords)
        return render_template('learn-offline.html', resources_by_category=resources_by_category)
    except:
        return "Learn offline page not available", 500

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
def sign_in_page():
    return render_template('sign-in.html')

@app.route('/sign-in', methods=['POST'])
def sign_in():
    data = request.json  # Expecting JSON input

    if not data:
        return jsonify({"error": "Invalid request format"}), 400

    email = data.get("email")
    password = data.get("password")

    # Database lookup: Get user by email
    user = get_user_by_email(email)

    if not user:
        return jsonify({"error": "Invalid email or password."}), 401

    user_id, email, hashed_password = user  # Extract database values

    # Verify password using argon2
    try:
        if verify_password(hashed_password, password):
            session["user_id"] = user_id  # Store user session
            return jsonify({"message": "Login successful."}), 200
        else:
            return jsonify({"error": "Invalid email or password."}), 401
    except VerifyMismatchError:
        return jsonify({"error": "Invalid email or password."}), 401

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

if __name__ == '__main__':
    # Start the Flask development server
    app.run()
