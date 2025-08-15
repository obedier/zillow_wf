#!/bin/bash

# Start the Extraction Runner for Zillow Waterfront Web App
# This script runs the Python extraction runner in the background

echo "🚀 Starting Zillow Waterfront Extraction Runner..."

# Change to the webapp directory
cd "$(dirname "$0")/.."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if the extraction runner script exists
if [ ! -f "scripts/extraction_runner.py" ]; then
    echo "❌ Extraction runner script not found"
    exit 1
fi

# Set environment variables (modify these as needed)
export DATABASE_URL="postgresql://username:password@localhost:5432/zillow_wf"

# Check if DATABASE_URL still contains placeholder values
if [[ "$DATABASE_URL" == *"username:password"* ]]; then
    echo "⚠️  Warning: DATABASE_URL contains placeholder values"
    echo "Please set the DATABASE_URL environment variable with your actual database credentials"
    echo "Example: export DATABASE_URL='postgresql://youruser:yourpass@localhost:5432/zillow_wf'"
    exit 1
fi

# Start the extraction runner
echo "✅ Starting extraction runner with database: $DATABASE_URL"
echo "📝 Logs will be written to: scripts/extraction_runner.log"
echo "🔄 Press Ctrl+C to stop the runner"

# Run the extraction runner
python3 scripts/extraction_runner.py
