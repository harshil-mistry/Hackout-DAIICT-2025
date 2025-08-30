from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'coastalguard-dev-key-2025')

# Main route - Landing page
@app.route('/')
def index():
    return render_template('index.html')

# Official dashboard route (we'll expand this later)
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Community forum route (we'll expand this later)
@app.route('/community')
def community():
    return render_template('community.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
