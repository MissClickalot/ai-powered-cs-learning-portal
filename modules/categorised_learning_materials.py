# Libraries
import sqlite3

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