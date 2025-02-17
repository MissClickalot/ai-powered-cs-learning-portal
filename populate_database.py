import sqlite3

# Connect to SQLite database
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

"""
TABLE FIELDS

query_history
id, user_id, query_string, extracted_meaning

query_result_history
id, output, query_history_id

users
id, email, password_hash, user_preferences_id, user_profiles_id

user_preferences
id, news_preference_id

user_profiles
id, avatars_id

avatars
id, avatar_name, file_reference

news_preferences
id, news_categories_id, user_preferences_id

news_categories
id, news_category_title

local_resources
id, file_reference, syllabus_categories_id

syllabus_categories
id, category_title
"""

"""
# Insert into `avatars`
avatars_data = [
    ("Augustus De Morgan", "static/avatars/augustus_de_morgan.png"),
    ("Ada Lovelace", "static/avatars/ada_lovelace.png"),
    ("George Boole", "static/avatars/george_boole.png"),
    ("John von Neumann", "static/avatars/john_von_neumann.png"),
    ("Grace Hopper", "static/avatars/grace_hopper.png"),
    ("Alan Turing", "static/avatars/alan_turing.png"),
    ("Claude Shannon", "static/avatars/claude_shannon.png"),
    ("Tim Berners-Lee", "static/avatars/tim_berners_lee.png"),
    ("Steve Jobs", "static/avatars/steve_jobs.png"),
    ("James Gosling", "static/avatars/james_gosling.png")
]
# The id field will be handled by SQLite automatically
cursor.executemany("INSERT INTO avatars (avatar_name, file_reference) VALUES (?, ?)", avatars_data)
"""

"""
# Insert into `syllabus_categories`
syllabus_categories_data = [("Computer systems",), ("Data representation",), ("Boolean logic",), ("Algorithmic thinking",),
                            ("Programming",), ("Databases",), ("Productivity software",), ("Solution development",),
                            ("Testing",), ("Computer networks",), ("Security",), ("Impacts",), ("Digital authoring",), ("Electronics",)]
# The id field will be handled by SQLite automatically
cursor.executemany("INSERT INTO syllabus_categories (category_title) VALUES (?)", syllabus_categories_data)
"""

"""
# Insert into `local_resources`
local_resources_data = [
    # Computer systems
    ("static/resources/computer-systems-ebook-part-1.pdf", 1),
    ("static/resources/computer-systems-ebook-part-2.pdf", 1),
    ("static/resources/computer-systems-ebook-part-3.pdf", 1),
    # Data representation
    ("static/resources/data-representation-ebook.pdf", 2),
    # Boolean logic
    ("static/resources/boolean-logic-ebook-part-1.pdf", 3),
    ("static/resources/boolean-logic-ebook-part-2.pdf", 3),
    ("static/resources/installing-java.pdf", 3),
    ("static/resources/installing-digital.pdf", 3),
    # Programming
    ("static/resources/programming-primer-ebook.pdf", 5),
    ("static/resources/python-install-ebook.pdf", 5),
    ("static/resources/pycharm-install-ebook.pdf", 5),
    ("static/resources/python-part-1-fundamentals-ebook.pdf", 5),
    ("static/resources/python-part-2-beyond-the-fundamentals-a-ebook.pdf", 5),
    ("static/resources/python-part-2-beyond-the-fundamentals-b-ebook.pdf", 5),
    ("static/resources/pygame-ebook.pdf", 5),
    ("static/resources/tkinter-ebook.pdf", 5),
    # Databases
    ("static/resources/databases-part-1.pdf", 6),
    ("static/resources/databases-part-2.pdf", 6),
    # Impacts
    ("static/resources/artificial-intelligence-basics-ebook.pdf", 12)
]
cursor.executemany("INSERT INTO local_resources (file_reference, syllabus_categories_id) VALUES (?, ?)", local_resources_data)
"""

"""
# Insert into `news_categories`
news_categories_data = [
    ("Artificial Intelligence",),
    ("Quantum Computing",),
    ("Data Protection Act",),
    ("Computer Misuse Act",),
    ("Cyber Security",),
    ("Python",),
    ("Hacks",),
    ("Virtual Reality",)
]
# The id field will be handled by SQLite automatically
cursor.executemany("INSERT INTO news_categories (news_category_title) VALUES (?)", news_categories_data)
"""

"""
# Create indexes separately in SQLite to establish relationships
cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_profiles_avatars ON user_profiles (avatars_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_profiles ON users (user_profiles_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_preferences ON users (user_preferences_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_local_resources_categories ON local_resources (syllabus_categories_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_result_history ON query_result_history (query_history_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_preferences_categories ON news_preferences (news_categories_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_preferences_users ON news_preferences (user_preferences_id);")
"""

# Commit
conn.commit()

# Close the connection
conn.close()