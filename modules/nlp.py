# Libraries
import spacy
import requests

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
    query_processed = nlp_model(query)
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
    query = nlp_model(query)
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

if __name__ == '__main__':
    # Initialise the spaCy engine
    # en_core_web_sm is a pre-trained model that knows English grammar and vocabulary
    nlp_model = spacy.load("en_core_web_sm")

    # Define the user query
    query = "I want to know about binary"
    preprocessed_query = preprocess_query(query)
    # extracted_entities = extract_entities(preprocessed_query)
    # print(extract_entities)

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
    print(hyperlinked_learning_content)