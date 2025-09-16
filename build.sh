#!/bin/bash

# Build script for Render deployment
echo "🚀 Starting Agenda IA Backend build for Render..."

# Set Python path
export PYTHONPATH="/opt/render/project/src/backend:$PYTHONPATH"

# Upgrade pip
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Verify FastAPI installation
echo "✅ Verifying FastAPI installation..."
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')"

# Verify MongoDB driver
echo "✅ Verifying Motor (MongoDB) installation..."
python -c "import motor; print('Motor (MongoDB driver) installed successfully')"

# Verify OpenAI
echo "✅ Verifying OpenAI installation..."
python -c "import openai; print('OpenAI library installed successfully')"

# Create logs directory if it doesn't exist
mkdir -p logs

echo "🎉 Backend build completed successfully for Render!"
echo "✅ Ready to start with: python main.py"