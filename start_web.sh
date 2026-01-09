#!/bin/bash
# Startup script for CasaCompra Web Application

set -e

echo "🚀 Starting CasaCompra Web Application..."

# Navigate to project directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Install requirements if not already installed
pip install -r requirements.txt

# Start the Flask application
echo "Starting Flask server on port 5000..."
python app.py