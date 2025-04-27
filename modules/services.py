import sqlite3
from select import select

# Connect to the database
def connect_db(database = "database.db"):
    conn = sqlite3.connect(database)
    return conn

# Insert new users into `users` table
def insert_user(email, hashed_password):
    # If the user's email is already in `users`, do NOT add another entry
    if select_user_by_email(email):
        return False
    else:
        with connect_db() as conn:
            cursor = conn.cursor()
            insert_statement = "INSERT INTO users (email, password_hash, user_preferences_id, user_profiles_id) VALUES (?, ?, ?, ?)"
            cursor.execute(insert_statement, (email, hashed_password, 0, 0))
            conn.commit()

        return True

# Get specific user using email
def select_user_by_email(email):
    with connect_db() as conn:
        cursor = conn.cursor()
        select_statement = "SELECT * FROM users WHERE email = ?"
        cursor.execute(select_statement, [email])
        user = cursor.fetchone()
    return user

# Get specific user using id
def select_user_by_id(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        select_statement = "SELECT * FROM users WHERE id = ?"
        cursor.execute(select_statement, [user_id])
        user = cursor.fetchone()
    return user