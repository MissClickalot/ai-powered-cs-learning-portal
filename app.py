from flask import Flask, request, render_template, send_from_directory, jsonify
import spacy
import sqlite3
import jsonify
import secrets
import os
import queue
from werkzeug.utils import secure_filename
# Import custom modules from /modules folder
from modules.password_validation import verify_password  # Import own python password validation code
from modules import nlp  # Import own natural language processing code
from modules import speech_to_text  # Import own speech to text conversion and processing code
from modules import news_api_client  # Import own code to fetch from db and communicate with a news API
from modules import categorised_learning_materials  # Import own code to get offline material

# Create an instance of the Flask class for the app
app = Flask(__name__)

# Generate a secure 32-byte random hex key
app.secret_key = secrets.token_hex(32)

# Folder to temporarily store uploaded PDFs
UPLOAD_FOLDER = 'temp_pdf_uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Only allow PDF files
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to get user by email from the database
def get_user_by_email(email = "evie.paige.anderson@gmail.com"):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, password_hash FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()  # Returns (id, email, password_hash) or None
    conn.close()
    return user # Returns a tuple (id, email, password_hash) or None

# Define a route for the root URL
@app.route('/', methods=['GET', 'POST'])
# Function to execute when user accesses the root URL
def index():
    # Final results dictionary to send to the template
    hyperlinked_learning_content = {}
    query_submitted = False

    if request.method == 'POST':
        query_submitted = True

        # Always use what's in the text box, regardless of how it got there (typing or speech)
        query = request.form.get('user_input')

        # Debug
        print("Received query:", query)

        # Use the upgraded NLP processor
        processor = nlp.NLPProcessor()

        # Step 1: Preprocess query with concept alias expansion
        expanded_terms, original_query = processor.preprocess_query(query)

        # Step 2: Get all outcomes
        url = "https://bit-by-bit.org/api/learning-outcomes?_format=json"
        headers = {"User-Agent": "Mozilla/5.0"}
        all_outcomes = processor.fetch_json_data(url, headers)

        # Step 3: Score and filter
        matches = processor.filter_and_rank_outcomes(all_outcomes, expanded_terms, original_query)
        strong = matches["strong_matches"]
        related = matches["related_matches"]
        metadata = matches["metadata"]

        # Step 4: Fetch all content types in parallel
        learning = processor.get_learning_content(strong + related, "learning-by-outcome", headers, metadata)
        testing = processor.get_learning_content(strong + related, "self-test-by-outcome", headers, metadata)
        exams = processor.get_learning_content(strong + related, "gcse-questions-by-outcome", headers, metadata)

        # Step 5: Enrich content with metadata
        learning_dict = processor.get_hyperlinked_content(learning, metadata)
        testing_dict = processor.get_hyperlinked_content(testing, metadata)
        exams_dict = processor.get_hyperlinked_content(exams, metadata)

        # Step 6: Merge all content by outcome ID
        merged = {}
        def insert(item, content_type):
            outcome_id = item.get("outcome_id")
            if not outcome_id:
                return
            if outcome_id not in merged:
                merged[outcome_id] = {
                    "outcome_text": item.get("outcome_text"),
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "teaser": item.get("teaser"),
                    "score": item.get("score"),
                    "matched_terms": item.get("matched_terms", []),
                    "prerequisites": item.get("prerequisites", []),
                    "learning": None,
                    "test": None,
                    "exam": None
                }
            merged[outcome_id][content_type] = {
                "title": item.get("title"),
                "url": item.get("url"),
                "teaser": item.get("teaser")
            }

        for item in learning_dict.values():
            insert(item, "learning")
        for item in testing_dict.values():
            insert(item, "test")
        for item in exams_dict.values():
            insert(item, "exam")

        # Pass the full merged object or just the learning part depending on how index.html handles it
        hyperlinked_learning_content = merged

        return render_template('index.html', hyperlinked_learning_content=hyperlinked_learning_content, query_submitted=True)

    # GET method fallback
    return render_template('index.html', hyperlinked_learning_content={}, query_submitted=False)

# Upload route
@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400

    file = request.files['pdf_file']

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Ensure folder exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        file.save(save_path)

        return jsonify({'success': True, 'message': 'File uploaded successfully', 'filename': filename}), 200

    return jsonify({'success': False, 'message': 'Invalid file type'}), 400

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
        syllabus_keywords = categorised_learning_materials.get_syllabus_keywords()
        resources_by_category = categorised_learning_materials.get_local_resources_by_category(syllabus_keywords)
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
        news_categories = news_api_client.get_news_categories()
        extracted_news = news_api_client.get_news(news_categories)
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
