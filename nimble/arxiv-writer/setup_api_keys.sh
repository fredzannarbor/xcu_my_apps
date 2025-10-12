#!/bin/bash

# Setup script for API keys
# This script helps you configure the necessary API keys for arxiv-writer

echo "🔧 Setting up API keys for arxiv-writer..."
echo ""

# Check if .env file exists
if [ -f ".env" ]; then
    echo "📄 Found existing .env file"
    source .env
else
    echo "📄 Creating new .env file"
    touch .env
fi

# Function to set API key
set_api_key() {
    local key_name=$1
    local key_description=$2
    
    echo ""
    echo "🔑 Setting up $key_description"
    echo "Current value: ${!key_name:-'(not set)'}"
    
    if [ -z "${!key_name}" ]; then
        echo "⚠️  $key_name is not set"
        echo "Please set your $key_description:"
        echo "  export $key_name='your-api-key-here'"
        echo "  # or add to .env file:"
        echo "  echo '$key_name=your-api-key-here' >> .env"
    else
        echo "✅ $key_name is configured"
    fi
}

# Check for Google API key (primary)
set_api_key "GOOGLE_API_KEY" "Google API Key (for Gemini models)"

# Check for other API keys (optional)
echo ""
echo "📋 Optional API keys (for other models):"
set_api_key "ANTHROPIC_API_KEY" "Anthropic API Key (for Claude models)"
set_api_key "OPENAI_API_KEY" "OpenAI API Key (for GPT models)"

echo ""
echo "🚀 To use the arxiv-writer with Gemini:"
echo "1. Get a Google API key from: https://aistudio.google.com/app/apikey"
echo "2. Set the environment variable:"
echo "   export GOOGLE_API_KEY='your-google-api-key'"
echo "3. Or add to .env file:"
echo "   echo 'GOOGLE_API_KEY=your-google-api-key' >> .env"
echo ""
echo "📖 Then test with:"
echo "   arxiv-writer codexes generate-section abstract --config examples/configs/xynapse_traces.json"
echo ""