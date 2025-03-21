#!/bin/bash

# Install system dependencies
apt-get update
apt-get install -y python3-distutils python3-dev build-essential

# Upgrade pip and install setuptools
pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r requirements-railway.txt

echo "Build completed successfully!"
