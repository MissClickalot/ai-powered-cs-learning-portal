from flask import Flask, render_template

# Create an instance of the Flask class for the app
app = Flask(__name__)
# Define a route for the root URL
@app.route('/')

# Function to execute when user acesses the root URL
def index():
    # Use the index.html template
    return render_template('index.html')

if __name__ == '__main__':
    # Start the Flask development server
    app.run()
