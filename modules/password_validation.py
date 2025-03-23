import re
from argon2 import PasswordHasher  # Argon2 is one of the most secure password hashing algorithms
from argon2.exceptions import VerifyMismatchError  # To catch all exceptions hides errors (e.g. Argon2 version mismatches)

# Validate the password against security requirements
def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character."
    return None

# Hash the password with a salt
# Argon2 is one of the most secure hashing algorithms
# Argon2 automatically generates and stores a salt within the hash
def hash_password(password):
    # Hashes the password Argon2 with a salt
    ph = PasswordHasher()
    hashed_password = ph.hash(password)
    return hashed_password

# Verify the password against the Argon2 hash
def verify_password(input_password, hashed_password):
    # Verifies the input password against the hashed password.
    ph = PasswordHasher()
    try:
        return ph.verify(hashed_password, input_password)
    except VerifyMismatchError:
        # Password is incorrect
        return False

def main():
    password = input("Enter a password: ")

    # Validate the password
    validation_error = validate_password(password)
    if validation_error:
        print(f"Error: {validation_error}")
        return

    # Hash the password
    hashed_password = hash_password(password)
    print(f"Hashed password: {hashed_password}")

    # Verify the password
    input_password = input("Re-enter the password for verification: ")
    if verify_password(input_password, hashed_password):
        print("Password matches!")
    else:
        print("Invalid password.")

if __name__ == "__main__":
    main()