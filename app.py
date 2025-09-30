# app.py
import os
from flask import Flask, jsonify, render_template
from sqlalchemy import create_engine, text

app = Flask(__name__)

# Get the database URL from Render's environment variables
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("No DATABASE_URL set for Flask application")

engine = create_engine(DATABASE_URL)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def get_data():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT timestamp, following_count FROM following_history ORDER BY timestamp ASC"))
        rows = result.fetchall()

    labels = [row[0].strftime('%Y-%m-%d %H:%M') for row in rows]
    data = [row[1] for row in rows]

    return jsonify({'labels': labels, 'data': data})