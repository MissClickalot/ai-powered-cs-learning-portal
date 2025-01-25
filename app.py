from flask import Flask, render_template, send_from_directory

# Create an instance of the Flask class for the app
app = Flask(__name__)

# Define a route for the root URL
@app.route('/')
# Function to execute when user acesses the root URL
def index():
    # Use the index.html template
    return render_template('index.html')

# Define a route for each page
@app.route('/<page>')
def render_page(page):
    try:
        return render_template(f'{page}.html')
    except:
        return "Page not found", 404

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
