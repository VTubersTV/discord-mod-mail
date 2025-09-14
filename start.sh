#!/bin/bash

# Discord Mod Mail Bot Startup Script

echo "Starting Discord Mod Mail Bot..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.template to .env and configure it with your Discord bot token."
    exit 1
fi

# Check if data directory exists
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p data
fi

# Run the bot
echo "Starting bot..."
python bot.py
