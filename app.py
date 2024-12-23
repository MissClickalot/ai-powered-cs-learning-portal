from flask import Flask

# Create an instance of the Flask class for the app
app = Flask(__name__)
# Define a route for the root URL
@app.route('/')

# Function to execute when user acesses the root URL
def index():
    return "Hello world"

if __name__ == '__main__':
    # Start the Flask development server
    app.run()
