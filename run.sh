#!/bin/bash

echo "🌱 Starting Integrated Smart Plant Disease Detection System..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if requirements are installed
echo "📦 Checking dependencies..."
python3 -c "import gradio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
    
    echo "📚 Downloading NLTK data..."
    python3 -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True); nltk.download('stopwords', quiet=True)"
else
    echo "✓ Dependencies already installed"
fi

echo ""
echo "🚀 Launching application..."
echo ""

# Run the application
python3 integrated_plant_system.py
