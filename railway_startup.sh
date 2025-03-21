#!/bin/bash

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Initialize database
echo "Initializing database..."
python init_db.py

# Start the application
echo "Starting application..."
gunicorn 'app:create_app("production")' --bind 0.0.0.0:$PORT
