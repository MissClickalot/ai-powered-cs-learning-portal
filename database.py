import sqlite3

# Connect to SQLite database
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS query_history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NULL,
      query_string TEXT NULL,
      extracted_meaning TEXT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_preferences (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      news_preference_id INTEGER NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS avatars (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      avatar_name TEXT NULL,
      file_reference TEXT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_profiles (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      avatars_id INTEGER NOT NULL,
      FOREIGN KEY (avatars_id) REFERENCES avatars (id) ON DELETE NO ACTION ON UPDATE NO ACTION
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT NULL,
      password_hash TEXT NULL,
      user_preferences_id INTEGER NOT NULL,
      user_profiles_id INTEGER NOT NULL,
      FOREIGN KEY (user_preferences_id) REFERENCES user_preferences (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
      FOREIGN KEY (user_profiles_id) REFERENCES user_profiles (id) ON DELETE NO ACTION ON UPDATE NO ACTION
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS syllabus_categories (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      category_title TEXT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS local_resources (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      file_reference TEXT NULL,
      syllabus_categories_id INTEGER NOT NULL,
      FOREIGN KEY (syllabus_categories_id) REFERENCES syllabus_categories (id) ON DELETE NO ACTION ON UPDATE NO ACTION
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS query_result_history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      output TEXT NULL,
      query_history_id INTEGER NOT NULL,
      FOREIGN KEY (query_history_id) REFERENCES query_history (id) ON DELETE NO ACTION ON UPDATE NO ACTION
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS news_categories (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      news_category_title TEXT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS news_preferences (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      news_categories_id INTEGER NOT NULL,
      user_preferences_id INTEGER NOT NULL,
      FOREIGN KEY (news_categories_id) REFERENCES news_categories (id) ON DELETE NO ACTION ON UPDATE NO ACTION,
      FOREIGN KEY (user_preferences_id) REFERENCES user_preferences (id) ON DELETE NO ACTION ON UPDATE NO ACTION
    )
''')

# Create indexes separately in SQLite to establish relationships
cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_profiles_avatars ON user_profiles (avatars_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_profiles ON users (user_profiles_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_preferences ON users (user_preferences_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_local_resources_categories ON local_resources (syllabus_categories_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_result_history ON query_result_history (query_history_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_preferences_categories ON news_preferences (news_categories_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_preferences_users ON news_preferences (user_preferences_id);")

# Commit and close
conn.commit()

# Check if tables were created
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Existing Tables:", tables)

# Loop through tables and print their structure
for table in tables:
    table_name = table[0]
    print(f"Table: {table_name}")

    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()

    for col in columns:
        col_id, col_name, col_type, col_notnull, col_default, col_pk = col
        print(f"   - {col_name} ({col_type}) {'PRIMARY KEY' if col_pk else ''} {'NOT NULL' if col_notnull else ''}")

    # Separator
    print("\n" + "-"*40)

conn.close()
