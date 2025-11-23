#!/bin/bash

# supply chain intelligence agent - quick start script

echo "================================="
echo "supply chain intelligence agent"
echo "================================="
echo ""

# check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "creating virtual environment..."
    python3 -m venv venv
fi

# activate virtual environment
echo "activating virtual environment..."
source venv/bin/activate

# install dependencies
if [ ! -f "venv/installed" ]; then
    echo "installing dependencies..."
    pip install -r requirements.txt
    touch venv/installed
fi

# check if .env exists
if [ ! -f ".env" ]; then
    echo "copying .env.example to .env..."
    cp .env.example .env
    echo "⚠️  please edit .env file and add your api keys"
fi

# check if database exists
if [ ! -f "inventory.db" ]; then
    echo "generating demo data..."
    python demo_data/generate_data.py
fi

echo ""
echo "✅ setup complete!"
echo ""
echo "launching dashboard..."
echo "dashboard will open at: http://localhost:8501"
echo ""

# launch dashboard
streamlit run dashboard/app.py
