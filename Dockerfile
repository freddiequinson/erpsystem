FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-distutils \
    python3-dev \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements-railway.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements-railway.txt

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV FLASK_CONFIG=production

# Initialize database and start application
CMD python -m flask db upgrade || true && python init_db.py && gunicorn 'app:create_app("production")' --bind 0.0.0.0:$PORT
